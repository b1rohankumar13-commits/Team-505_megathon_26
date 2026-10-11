"""Pure annual scenario arithmetic. No ML, LLM, database, randomness or clock."""
from collections.abc import Mapping
from math import isfinite
from numbers import Real

from .factors import DEFAULT_FACTORS, Factor

VERSION = '1.0.0'
BOUNDARY = ('Partial operational energy-use comparison: direct combustion plus purchased '
            'electricity generation and grid losses. Excludes fuel upstream, manufacture, '
            'installation, maintenance, end of life and rebound. Not a lifecycle, financed '
            'emissions or certified avoided-emissions assessment.')
PRODUCT_FIELDS = {
    'GP01': {'annual_distance', 'distance_unit', 'baseline_fuel',
             'ev_kwh_per_km', 'charging_efficiency'},
    'GP02': {'annual_electricity_before_kwh', 'annual_electricity_after_kwh',
             'annual_gas_before_kwh', 'annual_gas_after_kwh', 'gas_basis', 'intervention'},
    'GP03': {'annual_grid_import_kwh', 'annual_solar_generation_kwh',
             'annual_self_consumed_solar_kwh'},
    'GP04': {'annual_paper_statements', 'sheets_per_statement', 'switch_fraction'},
}


class InputProblem(Exception):
    def __init__(self, status, message, fields=()):
        super().__init__(message)
        self.status, self.fields = status, list(fields)


def _num(data, key, *, positive=False, maximum=None):
    value = data.get(key)
    if value is None:
        raise InputProblem('unavailable', 'Required input is missing.', [key])
    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
        raise InputProblem('invalid_input', f'{key} must be a finite number.', [key])
    if value < 0 or (positive and value == 0) or (maximum is not None and value > maximum):
        raise InputProblem('invalid_input', f'{key} is outside its permitted range.', [key])
    return float(value)


def _enum(data, key, options):
    value = data.get(key)
    if value is None:
        raise InputProblem('unavailable', 'Required input is missing.', [key])
    if not isinstance(value, str) or value not in options:
        raise InputProblem('invalid_input', f'{key} must be one of {sorted(options)}.', [key])
    return value


def _metric(name, value, unit):
    if not isfinite(value):
        raise InputProblem('invalid_input', 'Calculation overflow: review activity magnitudes.')
    return {'name': name, 'value': round(value, 6), 'unit': unit}


class CarbonEngine:
    def __init__(self, factors=None):
        # Explicit empty registry is useful for checking unavailable-source behaviour.
        self.factors = dict(DEFAULT_FACTORS if factors is None else factors)

    def calculate(self, product_id, inputs, *, geography='UK', factor_year=2026):
        """Return a JSON-safe record; savings are signed baseline minus scenario.

        Inputs are annual physical quantities. All scenario assumptions are supplied
        explicitly; the engine does not infer physical activity from spending.
        """
        result = {
            'product_id': product_id if isinstance(product_id, str) else None,
            'engine_version': VERSION, 'status': 'unavailable',
            'is_estimate': True, 'horizon': 'one year at stated activity and factor basis',
            'geography': geography if isinstance(geography, str) else None,
            'factor_year': factor_year if type(factor_year) is int else None,
            'method': None, 'boundary': BOUNDARY, 'baseline': {}, 'scenario': {},
            'metrics': [], 'baseline_kgco2e': None, 'scenario_kgco2e': None,
            'reduction_kgco2e': None, 'carbon_status': 'unavailable',
            'assumptions': [], 'factor_sources': [], 'missing_inputs': [],
            'invalid_inputs': [], 'message': '',
            'limitations': ['Conditional scenario, not realised savings or evidence of financing additionality.',
                            'Do not add home and solar reductions without a shared combined scenario.'],
        }
        try:
            if not isinstance(product_id, str) or product_id not in PRODUCT_FIELDS:
                raise InputProblem('invalid_input', 'Unsupported product; expected GP01 through GP04.', ['product_id'])
            if not isinstance(inputs, Mapping):
                raise InputProblem('invalid_input', 'inputs must be an object.', ['inputs'])
            unknown = set(inputs) - PRODUCT_FIELDS[product_id] - {'assumption_notes'}
            if unknown:
                raise InputProblem('invalid_input', 'Unexpected input fields; check units and schema.', sorted(unknown, key=str))
            if geography != 'UK' or type(factor_year) is not int or factor_year != 2026:
                raise InputProblem('unavailable', 'Only the UK 2026 factor set is supported.', ['geography', 'factor_year'])
            notes = inputs.get('assumption_notes', [])
            if not isinstance(notes, list) or any(not isinstance(n, str) for n in notes):
                raise InputProblem('invalid_input', 'assumption_notes must be a list of strings.', ['assumption_notes'])
            result['assumptions'] = ['Baseline and scenario activity are supplied by the caller; not inferred by this engine.', *notes]
            missing = sorted(k for k in PRODUCT_FIELDS[product_id] if inputs.get(k) is None)
            if missing:
                raise InputProblem('unavailable', 'Supply the required annual activity and scenario inputs.', missing)
            getattr(self, '_' + product_id.lower())(inputs, result)
        except InputProblem as exc:
            # Never leak a half-computed result as a valid carbon saving.
            result.update(status=exc.status, message=str(exc), metrics=[], baseline={}, scenario={},
                          baseline_kgco2e=None, scenario_kgco2e=None, reduction_kgco2e=None,
                          carbon_status='unavailable', factor_sources=[])
            result['missing_inputs' if exc.status == 'unavailable' else 'invalid_inputs'] = exc.fields
        except OverflowError:
            result.update(status='invalid_input', message='Calculation overflow: review activity magnitudes.',
                          metrics=[], baseline={}, scenario={}, baseline_kgco2e=None,
                          scenario_kgco2e=None, reduction_kgco2e=None, carbon_status='unavailable', factor_sources=[])
        return result

    def _factor(self, key, unit, result):
        factor = self.factors.get(key)
        if factor is None:
            raise InputProblem('unavailable', f'Verified factor is unavailable: {key}', ['factor:' + key])
        if (not isinstance(factor, Factor) or factor.unit != unit or factor.geography != 'UK'
                or factor.year != 2026 or isinstance(factor.value, bool)
                or not isinstance(factor.value, Real) or not isfinite(factor.value)
                or factor.value < 0 or not factor.source_url or not factor.cell):
            raise InputProblem('unavailable', f'Factor metadata, unit or value is incompatible: {key}', ['factor:' + key])
        # No unchecked custom replacement may silently inherit the documented scope.
        if factor != DEFAULT_FACTORS.get(key):
            raise InputProblem('unavailable', f'Unreviewed factor replacement: {key}', ['factor:' + key])
        if factor.factor_id not in {f['factor_id'] for f in result['factor_sources']}:
            result['factor_sources'].append(factor.record())
        return factor.value

    def _grid(self, result):
        return self._factor('grid_generation', 'kgCO2e/kWh', result) + self._factor('grid_losses', 'kgCO2e/kWh', result)

    @staticmethod
    def _finish(result, before, after, metrics):
        if not all(isfinite(v) for v in (before, after, before - after)):
            raise InputProblem('invalid_input', 'Calculation overflow: review activity magnitudes.')
        result.update(status='available', carbon_status='estimated_partial_operational',
                      baseline_kgco2e=round(before, 6), scenario_kgco2e=round(after, 6),
                      reduction_kgco2e=round(before-after, 6),
                      metrics=metrics + [_metric('operational_emissions_reduction', before-after, 'kgCO2e/year')],
                      message='Estimated annual operational change; a negative reduction means an increase.')

    def _gp01(self, d, r):
        distance = _num(d, 'annual_distance')
        unit = _enum(d, 'distance_unit', {'km', 'miles'})
        fuel = _enum(d, 'baseline_fuel', {'petrol', 'diesel'})
        efficiency = _num(d, 'ev_kwh_per_km', positive=True)
        charging = _num(d, 'charging_efficiency', positive=True, maximum=1)
        km = distance * (1.609344 if unit == 'miles' else 1)
        battery_kwh = km * efficiency
        purchased_kwh = battery_kwh / charging
        before = km * self._factor(fuel, 'kgCO2e/km', r)
        after = purchased_kwh * self._grid(r)
        r.update(method='ev_same_distance_operational_v1',
                 baseline={'annual_distance_km': km, 'fuel': fuel, 'vehicle_factor_basis': 'fleet average; not vehicle-specific'},
                 scenario={'annual_distance_km': km, 'ev_battery_kwh_per_km': efficiency,
                           'charging_efficiency': charging, 'annual_purchased_electricity_kwh': purchased_kwh})
        r['assumptions'] += ['Same annual distance in baseline and EV scenario.',
            'EV efficiency is battery-side kWh/km; charging_efficiency converts to purchased electricity.',
            'UK annual-average electricity generation plus grid losses; no upstream fuel factors on either side.']
        self._finish(r, before, after, [_metric('ev_purchased_electricity_required', purchased_kwh, 'kWh/year')])

    def _gp02(self, d, r):
        eb = _num(d, 'annual_electricity_before_kwh'); ea = _num(d, 'annual_electricity_after_kwh')
        gb = _num(d, 'annual_gas_before_kwh'); ga = _num(d, 'annual_gas_after_kwh')
        basis = _enum(d, 'gas_basis', {'gross', 'net'})
        intervention = d['intervention']
        if not isinstance(intervention, str) or not intervention.strip():
            raise InputProblem('invalid_input', 'Describe the home intervention.', ['intervention'])
        grid = self._grid(r) if eb or ea else 0.0
        gas = self._factor('gas_' + basis, 'kgCO2e/kWh_' + basis, r) if gb or ga else 0.0
        r.update(method='home_before_after_energy_v1',
                 baseline={'electricity_kwh_per_year': eb, 'gas_kwh_per_year': gb, 'gas_basis': basis},
                 scenario={'electricity_kwh_per_year': ea, 'gas_kwh_per_year': ga, 'intervention': intervention})
        r['assumptions'] += ['Both fuels supplied explicitly; known absence is zero, unknown is not zero.',
            'Before/after values are a declared retrofit scenario, not a guaranteed saving.',
            'Other fuels are outside this method; solar effects must not also be counted in this scenario.']
        self._finish(r, eb*grid + gb*gas, ea*grid + ga*gas,
                     [_metric('electricity_reduction', eb-ea, 'kWh/year'), _metric('gas_reduction', gb-ga, 'kWh/year')])

    def _gp03(self, d, r):
        imports = _num(d, 'annual_grid_import_kwh')
        generation = _num(d, 'annual_solar_generation_kwh')
        used = _num(d, 'annual_self_consumed_solar_kwh')
        if used > min(generation, imports):
            raise InputProblem('invalid_input', 'Self-consumption cannot exceed generation or baseline grid imports.', ['annual_self_consumed_solar_kwh'])
        grid = self._grid(r)
        r.update(method='solar_grid_import_footprint_v1', baseline={'annual_grid_import_kwh': imports},
                 scenario={'annual_grid_import_kwh': imports-used, 'annual_solar_generation_kwh': generation,
                           'annual_self_consumed_solar_kwh': used, 'annual_export_kwh': generation-used})
        r['assumptions'] += ['No storage; self-consumption explicitly supplied for a feasible installation.',
            'Underlying electricity demand unchanged; only grid imports decrease.',
            'Exported electricity receives no credit. Annual-average footprint change is not marginal grid avoided emissions.']
        self._finish(r, imports*grid, (imports-used)*grid,
                     [_metric('grid_import_reduction', used, 'kWh/year'), _metric('solar_export_no_carbon_credit', generation-used, 'kWh/year')])

    def _gp04(self, d, r):
        count = _num(d, 'annual_paper_statements')
        sheets = _num(d, 'sheets_per_statement', positive=True)
        fraction = _num(d, 'switch_fraction', maximum=1)
        before = count*sheets; avoided = before*fraction
        metric = _metric('paper_sheets_avoided', avoided, 'sheets/year')
        r.update(method='paper_volume_only_v1', status='partial', carbon_status='unavailable',
                 boundary='Paper volume only. No net carbon calculation for paper, printing, post or digital delivery.',
                 baseline={'annual_paper_statements': count, 'annual_sheets': before},
                 scenario={'switch_fraction': fraction, 'sheets_per_statement': sheets, 'annual_sheets': before-avoided},
                 metrics=[metric], message='Paper saving estimated; net CO2e unavailable without a supported paper-versus-digital method.')
        r['assumptions'] += ['sheets_per_statement counts physical sheets, not printed pages.',
                             'Fractional counts represent expected annual volumes; not measured avoided emissions.']


def calculate_impact(product_id, inputs, *, geography='UK', factor_year=2026):
    return CarbonEngine().calculate(product_id, inputs, geography=geography, factor_year=factor_year)
