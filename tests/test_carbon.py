import copy
import json
import unittest
from dataclasses import replace

from src.carbon import CarbonEngine, calculate_impact
from src.carbon.factors import DEFAULT_FACTORS

EV = dict(annual_distance=10000, distance_unit='km', baseline_fuel='petrol',
          ev_kwh_per_km=.18, charging_efficiency=.9)
HOME = dict(annual_electricity_before_kwh=4000, annual_electricity_after_kwh=4200,
            annual_gas_before_kwh=12000, annual_gas_after_kwh=9000,
            gas_basis='gross', intervention='Explicit user-supplied retrofit scenario')
SOLAR = dict(annual_grid_import_kwh=4000, annual_solar_generation_kwh=3500,
             annual_self_consumed_solar_kwh=2000)
PAPER = dict(annual_paper_statements=12, sheets_per_statement=2, switch_fraction=1)


class CarbonTests(unittest.TestCase):
    def test_ev_known_arithmetic(self):
        r = calculate_impact('GP01', EV)
        self.assertEqual(r['status'], 'available')
        self.assertAlmostEqual(r['baseline_kgco2e'], 1615.2)
        self.assertAlmostEqual(r['scenario_kgco2e'], 287.9)
        self.assertAlmostEqual(r['reduction_kgco2e'], 1327.3)

    def test_distance_units_same_physical_distance(self):
        km = calculate_impact('GP01', dict(EV, annual_distance=1609.344))
        miles = calculate_impact('GP01', dict(EV, annual_distance=1000, distance_unit='miles'))
        self.assertEqual(km['reduction_kgco2e'], miles['reduction_kgco2e'])

    def test_zero_driving(self):
        self.assertEqual(calculate_impact('GP01', dict(EV, annual_distance=0))['reduction_kgco2e'], 0)

    def test_negative_saving_preserved(self):
        r = calculate_impact('GP01', dict(EV, ev_kwh_per_km=2))
        self.assertLess(r['reduction_kgco2e'], 0)

    def test_charging_losses(self):
        better = calculate_impact('GP01', dict(EV, charging_efficiency=1))
        self.assertLess(better['scenario_kgco2e'], calculate_impact('GP01', EV)['scenario_kgco2e'])

    def test_missing_inputs_not_zero(self):
        r = calculate_impact('GP01', {})
        self.assertEqual(r['status'], 'unavailable')
        self.assertEqual(len(r['missing_inputs']), 5)
        self.assertIsNone(r['reduction_kgco2e'])

    def test_bad_activity(self):
        for value in [-1, float('nan'), float('inf'), True, '10000']:
            with self.subTest(value=value):
                r = calculate_impact('GP01', dict(EV, annual_distance=value))
                self.assertEqual(r['status'], 'invalid_input')
                json.dumps(r, allow_nan=False)

    def test_efficiency_bounds(self):
        for key, value in [('charging_efficiency', 0), ('charging_efficiency', 1.1), ('ev_kwh_per_km', 0)]:
            self.assertEqual(calculate_impact('GP01', dict(EV, **{key:value}))['status'], 'invalid_input')

    def test_reject_unsupported_fuel_and_distance_unit(self):
        for changes in [{'baseline_fuel':'unknown'}, {'baseline_fuel':'electric'}, {'distance_unit':'meters'}]:
            self.assertEqual(calculate_impact('GP01', dict(EV, **changes))['status'], 'invalid_input')

    def test_wrong_region_or_year(self):
        for kwargs in [{'geography':'India'}, {'factor_year':2025}, {'factor_year':True}]:
            self.assertEqual(calculate_impact('GP01', EV, **kwargs)['status'], 'unavailable')

    def test_missing_factor(self):
        r = CarbonEngine({}).calculate('GP01', EV)
        self.assertEqual(r['status'], 'unavailable')
        self.assertIsNone(r['reduction_kgco2e'])

    def test_bad_or_unreviewed_factor(self):
        for bad in [replace(DEFAULT_FACTORS['petrol'], unit='gCO2e/km'),
                    replace(DEFAULT_FACTORS['petrol'], value=.1),
                    replace(DEFAULT_FACTORS['petrol'], year=2025)]:
            registry = dict(DEFAULT_FACTORS, petrol=bad)
            self.assertEqual(CarbonEngine(registry).calculate('GP01', EV)['status'], 'unavailable')

    def test_home_accounts_for_electricity_increase(self):
        r = calculate_impact('GP02', HOME)
        self.assertAlmostEqual(r['reduction_kgco2e'], 3000*.18231 - 200*.14395)
        self.assertEqual(r['metrics'][0]['value'], -200)

    def test_home_unchanged_zero(self):
        d = dict(HOME, annual_electricity_after_kwh=4000, annual_gas_after_kwh=12000)
        self.assertEqual(calculate_impact('GP02', d)['reduction_kgco2e'], 0)

    def test_home_gas_basis(self):
        r = calculate_impact('GP02', dict(HOME, gas_basis='net'))
        self.assertAlmostEqual(r['reduction_kgco2e'], 3000*.20199 - 200*.14395)
        self.assertIn('UK_GAS_NET_CV_2026', [f['factor_id'] for f in r['factor_sources']])

    def test_home_missing_gas_not_imputed(self):
        d = dict(HOME); d.pop('annual_gas_before_kwh')
        self.assertEqual(calculate_impact('GP02', d)['status'], 'unavailable')

    def test_solar_only_self_consumption_credited(self):
        r = calculate_impact('GP03', SOLAR)
        self.assertAlmostEqual(r['reduction_kgco2e'], 287.9)
        self.assertEqual(r['scenario']['annual_export_kwh'], 1500)
        more = calculate_impact('GP03', dict(SOLAR, annual_solar_generation_kwh=6000))
        self.assertEqual(r['reduction_kgco2e'], more['reduction_kgco2e'])

    def test_solar_impossible_values_rejected_not_capped(self):
        for use in [3501, 4001]:
            self.assertEqual(calculate_impact('GP03', dict(SOLAR, annual_self_consumed_solar_kwh=use))['status'], 'invalid_input')

    def test_solar_no_self_consumption(self):
        self.assertEqual(calculate_impact('GP03', dict(SOLAR, annual_self_consumed_solar_kwh=0))['reduction_kgco2e'], 0)

    def test_paper_no_carbon_claim(self):
        r = calculate_impact('GP04', PAPER)
        self.assertEqual(r['status'], 'partial')
        self.assertEqual(r['metrics'][0]['value'], 24)
        self.assertIsNone(r['reduction_kgco2e'])
        self.assertEqual(r['factor_sources'], [])

    def test_paper_fraction_and_zero(self):
        self.assertEqual(calculate_impact('GP04', dict(PAPER, switch_fraction=.5))['metrics'][0]['value'], 12)
        self.assertEqual(calculate_impact('GP04', dict(PAPER, annual_paper_statements=0))['metrics'][0]['value'], 0)
        self.assertEqual(calculate_impact('GP04', dict(PAPER, switch_fraction=1.1))['status'], 'invalid_input')

    def test_input_shape_and_unknown_product(self):
        for product, data in [('GP05', {}), ('GP01', []), (None, {})]:
            self.assertEqual(calculate_impact(product, data)['status'], 'invalid_input')
        self.assertEqual(calculate_impact('GP01', dict(EV, annual_miles=100))['status'], 'invalid_input')

    def test_notes_validation(self):
        self.assertEqual(calculate_impact('GP01', dict(EV, assumption_notes='text'))['status'], 'invalid_input')

    def test_determinism_no_mutation_and_json_safety(self):
        for product, data in [('GP01', EV), ('GP02', HOME), ('GP03', SOLAR), ('GP04', PAPER)]:
            saved = copy.deepcopy(data)
            first = calculate_impact(product, data)
            self.assertEqual(first, calculate_impact(product, data))
            self.assertEqual(data, saved)
            json.dumps(first, allow_nan=False)

    def test_overflow_fails_closed(self):
        r = calculate_impact('GP01', dict(EV, annual_distance=1e308, ev_kwh_per_km=1e308))
        self.assertEqual(r['status'], 'invalid_input')
        self.assertIsNone(r['reduction_kgco2e'])
        json.dumps(r, allow_nan=False)

    def test_source_traceability(self):
        r = calculate_impact('GP01', EV)
        self.assertEqual(len(r['factor_sources']), 3)
        for factor in r['factor_sources']:
            self.assertTrue(factor['source_url'] and factor['worksheet'] and factor['cell'] and factor['workbook_sha256'])


if __name__ == '__main__': unittest.main()
