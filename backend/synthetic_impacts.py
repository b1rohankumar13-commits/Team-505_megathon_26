"""Reproducible, explicitly synthetic scenario inputs; never training features/labels.

Ranges below are hackathon design assumptions, not empirical customer estimates.
Carbon factors still come exclusively from the checked deterministic engine.
"""
import hashlib

VERSION = 'synthetic-scenarios-v1'
NOTICE = ('Synthetic scenario assumptions for demonstration, not observed plans, '
          'validated engineering designs or measured savings. ' + VERSION)


def uniform(cid, field, low=0.0, high=1.0):
    seed = hashlib.sha256(f'{VERSION}|{cid}|{field}'.encode()).digest()
    fraction = int.from_bytes(seed[:8], 'big') / 2**64
    return low + (high - low) * fraction


def scenario_inputs(customer, pid):
    """Use recorded baseline quantities and fill only scenario parameters."""
    cid = customer['id']
    assumptions = [NOTICE]
    if pid == 'GP01':
        v = customer['vehicle']
        if not v or v['fuel'] not in ('petrol', 'diesel') or v['annualDistance']['value'] is None:
            return None  # Never disguise a hybrid as petrol to obtain a number.
        assumptions += ['Synthetic EV battery consumption: 0.15–0.22 kWh/km; charging efficiency: 0.85–0.95.',
                        'Annual distance and current fuel are from the supplied synthetic customer dataset.']
        inputs = {'annual_distance': v['annualDistance']['value'], 'distance_unit': 'miles',
                  'baseline_fuel': v['fuel'], 'ev_kwh_per_km': round(uniform(cid, 'ev_eff', .15, .22), 4),
                  'charging_efficiency': round(uniform(cid, 'charging', .85, .95), 4)}
    elif pid == 'GP02':
        e, g = customer['electricityUse']['value'], customer['gasUse']['value']
        if e is None or g is None: return None
        assumptions += ['Synthetic retrofit reduces electricity by 5–15% and gas by 10–30%; gross gas calorific basis assumed.',
                        'Before-use quantities are complete annual totals from the supplied dataset. No solar savings in this retrofit.']
        inputs = {'annual_electricity_before_kwh': e, 'annual_electricity_after_kwh': round(e * (1-uniform(cid, 'retro_e', .05, .15)), 4),
                  'annual_gas_before_kwh': g, 'annual_gas_after_kwh': round(g * (1-uniform(cid, 'retro_g', .10, .30)), 4),
                  'gas_basis': 'gross', 'intervention': 'Synthetic insulation and efficiency scenario'}
    elif pid == 'GP03':
        e = customer['electricityUse']['value']
        if e is None: return None
        generation = round(uniform(cid, 'solar_generation', 2500, 4500), 2)
        assumptions += ['Synthetic solar generation: 2,500–4,500 kWh/year; self-consumption fraction: 0.4–0.7, capped at recorded imports.',
                        'Recorded electricity use treated as grid imports. Roof suitability, permission and installation feasibility are assumed for this simulation only.']
        inputs = {'annual_grid_import_kwh': e, 'annual_solar_generation_kwh': generation,
                  'annual_self_consumed_solar_kwh': round(min(e, generation * uniform(cid, 'solar_share', .4, .7)), 4)}
    else:
        count = customer['statementsPerYear']
        if count is None: return None
        assumptions += ['Synthetic statement length: 1–3 physical sheets; full switching assumed for conditional paper savings.',
                        'Statement count is the complete annual dataset total. No paper-to-carbon conversion.']
        inputs = {'annual_paper_statements': count, 'sheets_per_statement': 1 + int(uniform(cid, 'sheets', 0, 3)), 'switch_fraction': 1.0}
    inputs['assumption_notes'] = assumptions
    return inputs


def ui_inputs(inputs):
    names = {'baseline_fuel': 'current_fuel', 'annual_electricity_before_kwh': 'electricity_before_kwh',
             'annual_electricity_after_kwh': 'electricity_after_kwh', 'annual_gas_before_kwh': 'gas_before_kwh',
             'annual_gas_after_kwh': 'gas_after_kwh', 'annual_grid_import_kwh': 'grid_imports_kwh',
             'annual_solar_generation_kwh': 'generation_kwh', 'annual_self_consumed_solar_kwh': 'self_consumed_kwh',
             'annual_paper_statements': 'statements_per_year'}
    result = {names.get(k, k): str(v) for k, v in inputs.items() if k != 'assumption_notes'}
    if 'gas_basis' in result: result['gas_basis'] += ' CV'
    if 'intervention' in result: result['intervention'] = 'insulation'
    return result


def aggregate(customers):
    """Only recommended scenarios count; home has priority over solar per customer."""
    products = {p: [] for p in ('GP01', 'GP02', 'GP03', 'GP04')}
    selected = []
    eligible_paper = []
    recommendations = 0
    calculable = 0
    for c in customers.values():
        recs = [o for o in c['opportunities'] if o['status'] == 'recommended']
        recommendations += len(recs)
        valid = {o['productId']: o for o in recs if o['impact']['available']}
        calculable += len(valid)
        # Home and solar are alternative energy scenarios; don't sum their reductions.
        if 'GP02' in valid and 'GP03' in valid: del valid['GP03']
        for pid, o in valid.items():
            selected.append(o)
            products[pid].append(o['impact']['annualDifference']['value'])
        eligible_paper += [(c['id'], o['propensity']) for o in recs if o['productId'] == 'GP04' and o['propensity'] is not None]
    carbon = [v for p in ('GP01','GP02','GP03') for v in products[p]]
    energy = [o['impact']['energyKwhSaved'] for o in selected if o['impact']['energyKwhSaved'] is not None]
    sum_or_none = lambda values: round(sum(values), 4) if values else None
    simulated = sum(uniform(cid, 'paperless_adoption') < p for cid, p in eligible_paper)
    return {'co2eKg': sum_or_none(carbon), 'energyKwh': sum_or_none(energy),
            'paperSheets': sum_or_none(products['GP04']),
            'digitalAdoption': simulated / len(eligible_paper) if eligible_paper else None,
            'digitalAdoptionNumerator': simulated, 'digitalAdoptionDenominator': len(eligible_paper),
            'co2ByProduct': {p: sum_or_none(v) if p != 'GP04' else None for p, v in products.items()},
            'coverage': {'calculable': calculable, 'total': recommendations},
            'includedScenarios': len(selected)}
