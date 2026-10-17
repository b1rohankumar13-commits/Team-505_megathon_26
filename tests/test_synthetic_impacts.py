from copy import deepcopy
import pytest
from backend.synthetic_impacts import aggregate, scenario_inputs


def opportunity(pid, value, energy=None, status='recommended', available=True):
    return {'productId':pid, 'status':status, 'propensity':.7,
            'impact':{'available':available, 'annualDifference':{'value':value}, 'energyKwhSaved':energy}}


def test_alternative_home_and_solar_never_sum():
    c = {'id':'A', 'opportunities':[opportunity('GP01',100), opportunity('GP02',200,1000),
         opportunity('GP03',300,2000), opportunity('GP04',24), opportunity('GP01',999,status='ruled_out')]}
    before = deepcopy(c)
    r = aggregate({'A':c})
    assert r['co2eKg'] == 300
    assert r['energyKwh'] == 1000
    assert r['paperSheets'] == 24
    assert r['coverage'] == {'calculable':4,'total':4}
    assert r['includedScenarios'] == 3
    assert c == before
    assert aggregate({'A':c}) == r


def test_negative_savings_preserved_and_missing_not_zero():
    r = aggregate({'A':{'id':'A','opportunities':[opportunity('GP02',-100,-500)]}})
    assert r['co2eKg'] == -100
    assert r['energyKwh'] == -500
    assert r['paperSheets'] is None
    assert r['digitalAdoption'] is None


def test_missing_home_allows_solar_and_only_recommendations_count():
    r = aggregate({'A':{'id':'A','opportunities':[opportunity('GP02',None,available=False),
         opportunity('GP03',300,2000),opportunity('GP01',999,status='below_threshold')]}})
    assert r['co2eKg'] == 300
    assert r['coverage'] == {'calculable':1,'total':2}


def test_generated_inputs_are_reproducible_and_respect_baselines():
    c={'id':'SYN_C000001','vehicle':{'fuel':'petrol','annualDistance':{'value':10000}},
       'electricityUse':{'value':1000},'gasUse':{'value':5000},'statementsPerYear':12}
    before=deepcopy(c)
    for pid in ['GP01','GP02','GP03','GP04']:
        first=scenario_inputs(c,pid)
        assert first == scenario_inputs(c,pid)
        assert 'Synthetic' in first['assumption_notes'][0]
    solar=scenario_inputs(c,'GP03')
    assert solar['annual_self_consumed_solar_kwh'] <= min(1000,solar['annual_solar_generation_kwh'])
    assert scenario_inputs(c,'GP01')['annual_distance'] == 10000
    assert c == before
    c['vehicle']['fuel']='hybrid'
    assert scenario_inputs(c,'GP01') is None
    c['electricityUse']['value']=None
    assert scenario_inputs(c,'GP03') is None
