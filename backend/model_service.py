"""Frozen inference adapter. No fixture scores or training at runtime."""
import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src' / 'ml'))
import config as cfg
import joblib
import numpy as np
import pandas as pd
from categoriser import predict_categories
from explain import REASON_CODES, tree_shap_values
from predict import predict_frame
from src.carbon import calculate_impact
from src.carbon.engine import PRODUCT_FIELDS
from .synthetic_impacts import VERSION, NOTICE, scenario_inputs, ui_inputs, aggregate

PRODUCTS = dict(cfg.PRODUCTS, GP04='Paperless Banking')
STATES = ('recommended', 'ruled_out', 'below_threshold', 'insufficient_data')
REQUIRED = {'GP01': ['vehicle_annual_mileage_mean', 'spend_12m_fuel'], 'GP02': ['home_owner', 'elec_kwh_mean', 'gas_kwh_mean'], 'GP03': ['home_owner', 'elec_kwh_mean'], 'GP04': ['dig_paper_last3m', 'dig_digital_last3m', 'digital_usage']}

def number(v):
    if v is None or pd.isna(v): return None
    return float(v) if math.isfinite(float(v)) else None

def quantity(v, unit): return {'value': number(v), 'unit': unit}
def filename(p): return p.replace('\\', '/').rsplit('/', 1)[-1]

def impact_view(r):
    paper = r['product_id'] == 'GP04'
    diff = next((x['value'] for x in r['metrics'] if x['unit'] == 'sheets/year' and 'avoided' in x['name']), None) if paper else r['reduction_kgco2e']
    side = lambda k: {'activity': json.dumps(r[k]), 'emissions': quantity(r[k + '_kgco2e'], 'kg CO2e/year')}
    return {'available': diff is not None, 'annualDifference': quantity(diff, 'sheets/year' if paper else 'kg CO2e/year'), 'energyKwhSaved': None, 'label': r['message'], 'baseline': side('baseline') if r['baseline'] else None, 'scenario': side('scenario') if r['scenario'] else None, 'method': r['method'] or 'Explicit annual scenario inputs required', 'factors': [{'name': f['factor_id'], 'value': f['value'], 'unit': f['unit'], 'source': f['source_url'], 'url': f['source_url'], 'year': f['year']} for f in r['factor_sources']], 'assumptions': r['assumptions'] + r['limitations'], 'geography': r['geography'], 'boundary': r['boundary'], 'missingInputs': r['missing_inputs']}

class ModelService:
    def __init__(self, artifact_dir=None, data_dir=None):
        directory = Path(artifact_dir or os.environ.get('GREEN_INSIGHTS_ARTIFACT_DIR', ROOT / 'artifacts'))
        data = Path(data_dir or os.environ.get('GREEN_INSIGHTS_DATA_DIR', ROOT / 'data'))
        self.hashes = {filename(k): v for k, v in json.loads((directory / 'model_lock.json').read_text()).items()}
        needed = ['customer_360.joblib', 'categoriser.joblib', 'categoriser_use_rules.joblib', 'thresholds.json'] + [f'{kind}_{pid}.joblib' for pid in PRODUCTS for kind in ['propensity', 'explain']]
        for name in needed:
            if name not in self.hashes or hashlib.sha256((directory / name).read_bytes()).hexdigest() != self.hashes[name]: raise ValueError('Artifact integrity check failed: ' + name)
        self.frame = joblib.load(directory / 'customer_360.joblib')
        if not self.frame.customer_id.is_unique or self.frame.customer_id.isna().any(): raise ValueError('Invalid customer identifiers')
        self.models = {p: joblib.load(directory / f'propensity_{p}.joblib') for p in PRODUCTS}
        self.explainers = {p: joblib.load(directory / f'explain_{p}.joblib') for p in PRODUCTS}
        self.thresholds = json.loads((directory / 'thresholds.json').read_text())
        self.summary = json.loads((ROOT / 'results' / 'summary.json').read_text())
        if self.summary['cutoff_date'] != cfg.CUTOFF_DATE: raise ValueError('Training/inference cutoff mismatch')
        hashes = {filename(k): v for k, v in self.summary['input_hashes'].items()}
        self.tables = {}
        for name in ['customers', 'transactions', 'products', 'vehicles', 'energy_usage', 'digital_usage']:
            path = data / f'{name}.csv'
            if not path.is_file(): raise ValueError(f'Missing {name}.csv; set GREEN_INSIGHTS_DATA_DIR')
            if hashlib.sha256(path.read_bytes()).hexdigest() != hashes[path.name]: raise ValueError(f'{path.name} differs from frozen training inputs; rebuild features before serving changed data')
            self.tables[name] = pd.read_csv(path)
        if set(self.tables['customers'].customer_id) != set(self.frame.customer_id): raise ValueError('Customer IDs do not match model snapshot')
        cutoff = pd.Timestamp(cfg.CUTOFF_DATE)
        for name, col in [('transactions', 'date'), ('products', 'start_date'), ('energy_usage', 'month'), ('digital_usage', 'month')]:
            table = self.tables[name]
            self.tables[name] = table.loc[pd.to_datetime(table[col], errors='raise') <= cutoff].copy()
        self.predictions = predict_frame(self.frame, models=self.models, explainers=self.explainers).set_index(['customer_id', 'opportunity'])
        self.shap = {p: tree_shap_values(self.models[p], self.frame) for p in PRODUCTS}
        self.frame = self.frame.set_index('customer_id', drop=False)
        self.positions = {cid: i for i, cid in enumerate(self.frame.index)}
        tx = self.tables['transactions']
        tx['category'] = predict_categories(joblib.load(directory / 'categoriser.joblib'), tx.merchant_description, use_rules=bool(joblib.load(directory / 'categoriser_use_rules.joblib')))
        self.groups = {name: {str(cid): group for cid, group in t.groupby('customer_id')} for name, t in self.tables.items()}
        self.now = datetime.now(timezone.utc).isoformat()
        self.customers = {cid: self._customer(cid) for cid in self.frame.index}
        self.apply_synthetic_impacts()

    def group(self, table, cid): return self.groups[table].get(cid, self.tables[table].iloc[:0])

    def annual(self, table, cid, field):
        t = self.group(table, cid)
        dates = pd.to_datetime(t.month)
        cutoff = pd.Timestamp(cfg.CUTOFF_DATE)
        t = t.loc[(dates > cutoff - pd.DateOffset(months=12)) & (dates <= cutoff)]
        if len(t) != 12 or pd.to_datetime(t.month).dt.to_period('M').nunique() != 12 or t[field].isna().any(): return None
        return number(t[field].sum())

    def _customer(self, cid):
        raw = self.group('customers', cid).iloc[0]
        f = self.frame.loc[cid]
        vehicles = self.group('vehicles', cid)
        vehicle = None
        if len(vehicles) == 1:
            v = vehicles.iloc[0]
            vehicle = {'type': str(v.vehicle_type), 'fuel': str(v.fuel_type), 'annualDistance': quantity(v.annual_mileage, 'miles/year')}
        tx = self.group('transactions', cid)
        debit = tx.loc[tx.debit_credit.str.lower().eq('debit')]
        totals = {cat: number(debit.loc[debit.category.eq(cat), 'amount'].abs().sum()) if len(debit) else None for cat in cfg.TXN_CATEGORIES}
        paper = self.annual('digital_usage', cid, 'paper_statements')
        digital = self.annual('digital_usage', cid, 'digital_statements')
        share = digital / (digital + paper) if digital is not None and paper is not None and digital + paper > 0 else None
        own = number(raw.home_owner)
        c = {'id': cid, 'name': cid, 'age': number(raw.age), 'incomeBand': str(raw.income_band), 'postcode': str(raw.postcode), 'region': 'Unavailable', 'segment': 'Homeowners' if own == 1 else 'Non-homeowners' if own == 0 else 'Ownership unavailable', 'homeOwner': bool(own) if own is not None else None, 'dataAsOf': cfg.CUTOFF_DATE, 'financialProducts': self.group('products', cid).loc[lambda x: x.status.str.lower().eq('active'), 'product'].tolist(), 'vehicle': vehicle, 'electricityUse': quantity(self.annual('energy_usage', cid, 'electricity_kwh'), 'kWh/year'), 'gasUse': quantity(self.annual('energy_usage', cid, 'gas_kwh'), 'kWh/year'), 'paperStatements': paper > 0 if paper is not None else None, 'statementsPerYear': paper, 'digitalActivity': {'loginsPerMonth': None, 'digitalShare': share}, 'dataSources': [], 'categoryTotals': totals, 'transactions': [{'date': str(t.date), 'description': str(t.merchant_description), 'amount': float(t.amount), 'category': str(t.category)} for t in tx.itertuples()], 'opportunities': []}
        for name in self.tables:
            group = self.group(name, cid)
            c['dataSources'].append({'name': name + '.csv (synthetic; hash verified)', 'period': 'Through ' + cfg.CUTOFF_DATE, 'status': 'missing' if group.empty else 'partial' if group.isna().any().any() else 'ok'})
        for pid in PRODUCTS:
            pred = self.predictions.loc[(cid, cfg.OPPORTUNITY_LABELS[pid])]
            exclusion = None if pd.isna(pred.exclusion_reason) else pred.exclusion_reason
            p = number(pred.propensity)
            threshold = float(self.thresholds[pid]['xgb']['threshold'])
            if not 0 <= threshold <= 1: raise ValueError('Invalid saved threshold')
            state = ('insufficient_data' if exclusion == 'INSUFFICIENT_DATA' else 'ruled_out') if exclusion else ('recommended' if p >= threshold else 'below_threshold')
            missing = [x for x in REQUIRED[pid] if number(f.get(x)) is None]
            codes = list(pred.reason_codes)
            evidence = [{'reasonCode': code, 'label': REASON_CODES[code][0], 'value': str(number(f[REASON_CODES[code][0]])), 'period': 'Snapshot through ' + cfg.CUTOFF_DATE, 'source': 'Verified Customer 360; positive TreeSHAP contribution'} for code in codes]
            top = sorted(zip(self.models[pid]['feature_cols'], self.shap[pid][self.positions[cid]]), key=lambda x: abs(x[1]), reverse=True)[:5]
            reason = str(exclusion).replace('_', ' ').capitalize() if exclusion else f'Calibrated probability {p:.4f} {">=" if state == "recommended" else "<"} validation-selected threshold {threshold:.4f}.'
            impact = impact_view(calculate_impact(pid, {}))
            impact['missingInputs'] = sorted(PRODUCT_FIELDS[pid])
            c['opportunities'].append({'productId': pid, 'product': PRODUCTS[pid], 'status': state, 'statusReason': reason, 'propensity': p, 'confidence': number(pred.confidence), 'outcomeWindow': f'{cfg.LABEL_WINDOW_MONTHS} months after {cfg.CUTOFF_DATE} (to {cfg.LABEL_WINDOW_END_DATE})', 'reasonCodes': codes, 'evidence': evidence, 'missingInputs': missing, 'conflictingInputs': [], 'shap': [{'feature': n, 'contribution': float(v)} for n, v in top], 'modelVersion': self.hashes[f'propensity_{pid}.joblib'][:16], 'predictedAt': self.now, 'eligibility': {'assessed': False}, 'impact': impact, 'explanation': {'text': f'{PRODUCTS[pid]}: {reason} ' + ('Supporting signals: ' + ', '.join(codes) + '. ' if codes else '') + 'Potential impact needs explicit scenario inputs. Financial eligibility has not been assessed.', 'source': 'template', 'generatedAt': self.now}, 'action': {'kind': 'none' if state == 'ruled_out' else {'GP01': 'ev_scenario', 'GP02': 'home_scenario', 'GP03': 'solar_scenario', 'GP04': 'paperless_preview'}[pid], 'label': 'Not recommended' if state == 'ruled_out' else 'Explore scenario' if pid != 'GP04' else 'Preview paperless statements'}})
        return c

    def list_customers(self):
        return [{**{k: c[k] for k in ['id', 'name', 'region', 'segment']}, 'products': [{k: o[k] for k in ['productId', 'status', 'propensity', 'confidence']} for o in c['opportunities']]} for c in self.customers.values()]

    def apply_synthetic_impacts(self):
        for customer in self.customers.values():
            for opp in customer['opportunities']:
                if opp['status'] != 'recommended': continue
                inputs = scenario_inputs(customer, opp['productId'])
                if inputs is None: continue
                result = calculate_impact(opp['productId'], inputs)
                if result['status'] not in ('available', 'partial'):
                    raise ValueError('Invalid generated scenario: ' + str(result))
                view = impact_view(result)
                metrics = result['metrics']
                energy = [m['value'] for m in metrics if m['name'] in ('electricity_reduction', 'gas_reduction', 'grid_import_reduction')]
                view['energyKwhSaved'] = sum(energy) if energy else None
                view['scenarioSource'] = VERSION
                view['scenarioInputs'] = ui_inputs(inputs)
                view['label'] = 'Synthetic scenario estimate: ' + result['message']
                opp['impact'] = view
                value, unit = view['annualDifference']['value'], view['annualDifference']['unit']
                opp['explanation']['text'] = opp['explanation']['text'].replace('Potential impact needs explicit scenario inputs.', f'Synthetic scenario potential: {value:,.2f} {unit}; not measured savings.')

    def portfolio(self):
        ops = [o for c in self.customers.values() for o in c['opportunities']]
        counts = lambda rows: {s: sum(o['status'] == s for o in rows) for s in STATES}
        totals = aggregate(self.customers)
        potential = {k: totals[k] for k in ['co2eKg','energyKwh','paperSheets','digitalAdoption','digitalAdoptionNumerator','digitalAdoptionDenominator']}
        potential['scenarioSource'] = VERSION
        potential['dedupNote'] = (NOTICE + '. Conditional annual savings assume adoption of recommended scenarios; not propensity-weighted. '
            'Home takes priority over solar for the same customer, so their savings are never added. Energy shows home/grid-import reductions only, excluding transport. '
            'Simulated paperless take-up is a separate six-month Bernoulli simulation using GP04 probabilities among recommended customers; it is not an observed conversion rate and does not weight impact totals.')
        return {'dataCutoff': cfg.CUTOFF_DATE, 'lastRefreshed': self.now, 'customers': len(self.customers),
            'statusCounts': counts(ops), 'potential': potential, 'impactCoverage': totals['coverage'], 'measuredOutcomes': None,
            'products': [{'productId': pid, 'name': PRODUCTS[pid], 'counts': counts([o for o in ops if o['productId'] == pid]), 'co2eKg': totals['co2ByProduct'][pid]} for pid in PRODUCTS]}

    def insights(self):
        rows = [{'customerId': c['id'], 'customerName': c['name'], 'region': c['region'], **{k: o[k] for k in ['productId', 'status', 'propensity', 'confidence']}, 'impactAvailable': o['impact']['available']} for c in self.customers.values() for o in c['opportunities']]
        segments = []
        for name in sorted({c['segment'] for c in self.customers.values()}):
            cs = [c for c in self.customers.values() if c['segment'] == name]
            ops = [o for c in cs for o in c['opportunities'] if o['propensity'] is not None]
            ps = {p: [o['propensity'] for o in ops if o['productId'] == p] for p in PRODUCTS}
            available = {p: float(np.mean(v)) for p, v in ps.items() if v}
            segments.append({'name': name, 'customers': len(cs), 'avgPropensity': float(np.mean([o['propensity'] for o in ops])) if ops else None, 'topProduct': max(available, key=available.get) if available else None})
        return {'regions': [], 'segments': segments, 'snapshots': [], 'conversions': None, 'propensityDistribution': [{'productId': p, 'buckets': np.histogram([r['propensity'] for r in rows if r['productId'] == p and r['propensity'] is not None], bins=np.linspace(0, 1, 6))[0].tolist()} for p in PRODUCTS], 'opportunities': sorted(rows, key=lambda r: r['propensity'] if r['propensity'] is not None else -1, reverse=True)}

    def scenario(self, cid, pid, inputs):
        opp = next(o for o in self.customers[cid]['opportunities'] if o['productId'] == pid)
        if opp['status'] == 'ruled_out': raise ValueError('Product ruled out; scenarios cannot override recommendation rules.')
        mapping = {'GP01': {'current_fuel': 'baseline_fuel'}, 'GP02': {'electricity_before_kwh': 'annual_electricity_before_kwh', 'electricity_after_kwh': 'annual_electricity_after_kwh', 'gas_before_kwh': 'annual_gas_before_kwh', 'gas_after_kwh': 'annual_gas_after_kwh'}, 'GP03': {'grid_imports_kwh': 'annual_grid_import_kwh', 'generation_kwh': 'annual_solar_generation_kwh', 'self_consumed_kwh': 'annual_self_consumed_solar_kwh'}, 'GP04': {'statements_per_year': 'annual_paper_statements'}}[pid]
        converted = {mapping.get(k, k): v for k, v in inputs.items()}
        if converted.get('gas_basis') in ['gross CV', 'net CV']: converted['gas_basis'] = converted['gas_basis'].split()[0]
        r = calculate_impact(pid, converted)
        if r['status'] not in ('available', 'partial'): raise ValueError(r['message'] + ' ' + ', '.join(r['missing_inputs'] + r['invalid_inputs']))
        v = impact_view(r)
        return {'productId': pid, **{k: v[k] for k in ['baseline', 'scenario', 'annualDifference', 'method', 'factors', 'assumptions']}, 'statusUnchanged': True}

    def methodology(self):
        def section(id, title, points, metrics=None): return {'id': id, 'title': title, 'points': points, 'metrics': metrics}
        metrics = []
        for pid, variants in self.summary['validation_metrics'].items():
            for variant, models in variants.items():
                for key in ['pr_auc', 'roc_auc', 'brier']:
                    metrics.append({'name': f'{pid} {variant} XGBoost {key}', 'value': str(round(models['xgb'][key], 4)), 'baseline': str(round(models['logreg'][key], 4))})
        return {'sections': [section('data', 'Data and provenance', ['Supplied frozen models and hash-matched synthetic CSV cohort; no real banking records.', 'Cutoff: ' + cfg.CUTOFF_DATE + '; outcome ends: ' + cfg.LABEL_WINDOW_END_DATE, 'Customer-level 70/15/15 split. Dashboard includes training, validation and test customers; it is not an independent evaluation.', 'No invented customer names or inferred regions. Approved synthetic scenario assumptions fill missing planned-use parameters. Unsupported baselines remain unavailable.']), section('models', 'Models and confidence', ['TF-IDF transaction categoriser; calibrated XGBoost models and saved validation thresholds.', 'Confidence is the validated heuristic D cubed times S, distinct from propensity.', 'SHAP explains raw model margin, not probability points or causation.']), section('carbon', 'Deterministic carbon engine', ['UK government 2026 factors: direct fuel combustion, grid generation and grid losses.', 'Versioned synthetic scenario inputs plus UK 2026 factors. No lifecycle or financed-emissions claim. Paper uses sheets.', 'Generated recommended scenarios contribute to portfolio totals. Home has priority over solar to avoid overlap. Ad-hoc what-if edits remain unsaved and do not change recommendations or totals.']), section('synthetic', 'Synthetic scenario assumptions', [NOTICE, 'EV: battery efficiency 0.15â€“0.22 kWh/km; charging efficiency 0.85â€“0.95.', 'Home: electricity reduction 5â€“15%; gas reduction 10â€“30%; gross gas basis assumed.', 'Solar: 2500â€“4500 kWh/year; self-consumption 40â€“70%, capped at annual imports. Roof suitability assumed.', 'Paper: 1â€“3 physical sheets/statement; complete switching for conditional impact.', 'Stable SHA-256 draws keyed by customer, parameter and version. Engineering ranges are design assumptions, not research findings.', 'Six-month simulated paperless take-up: independent deterministic Bernoulli draws using model probabilities, recommended GP04 customers only. Not measured outcomes or evaluation labels.']), section('llm', 'Explanations', ['Customer detail can use Gemini to narrate supplied evidence when configured. Numbers and decisions remain backend-owned. Synthetic data only; no raw transactions or customer identifiers are sent. Shape and text checks cannot guarantee semantic correctness; review the displayed evidence. Templates are used for disabled, failed or rejected responses. In-memory cache expires after one hour or restart. Scenario edits remain deterministic and do not regenerate these baseline explanations.']), section('evaluation', 'Saved validation report', self.summary['limitations'], metrics), section('responsible', 'Responsible use', ['Synthetic data only. No eligibility assessment or real banking actions.', 'Model scores do not prove savings or approval. External validation is still needed.'])]}
