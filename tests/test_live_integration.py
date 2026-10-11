"""Integration checks against the actual supplied frozen artifacts; no fitting."""
import json
import math
import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture(scope='module')
def api():
    with TestClient(app) as client:
        r = client.get('/health')
        assert r.status_code == 200, r.text
        yield client


def test_real_cohort_and_predictions(api):
    s = app.state.service
    rows = api.get('/customers').json()
    assert len(rows) == 1000
    assert all(c['id'].startswith('SYN_') and len(c['products']) == 4 for c in rows)
    portfolio = api.get('/portfolio').json()
    assert sum(portfolio['statusCounts'].values()) == 4000
    assert portfolio['statusCounts']['recommended'] > 0
    assert portfolio['statusCounts']['below_threshold'] > 0
    assert portfolio['potential']['co2eKg'] is None
    assert api.get('/customers/C10001').status_code == 404
    for cid, customer in s.customers.items():
        for opp in customer['opportunities']:
            expected = s.predictions.loc[(cid, {'GP01':'EV_FINANCE','GP02':'GREEN_HOME_LOAN','GP03':'SOLAR_FINANCE','GP04':'PAPERLESS'}[opp['productId']])]
            if opp['propensity'] is not None:
                assert opp['propensity'] == expected.propensity
                threshold = s.thresholds[opp['productId']]['xgb']['threshold']
                assert (opp['status'] == 'recommended') == (opp['propensity'] >= threshold)
            assert 0 <= opp['confidence'] <= 1
            assert opp['eligibility'] == {'assessed': False}
            assert opp['impact']['annualDifference']['value'] is None
        json.dumps(customer, allow_nan=False)


def candidate(pid):
    return next(c['id'] for c in app.state.service.customers.values() if next(o for o in c['opportunities'] if o['productId'] == pid)['status'] != 'ruled_out')


@pytest.mark.parametrize('pid,inputs,expected', [
    ('GP01', {'annual_distance':10000,'distance_unit':'km','current_fuel':'petrol','ev_kwh_per_km':.18,'charging_efficiency':.9},1327.3),
    ('GP02', {'electricity_before_kwh':1000,'electricity_after_kwh':2000,'gas_before_kwh':0,'gas_after_kwh':0,'gas_basis':'gross CV','intervention':'heat pump'},-143.95),
    ('GP03', {'grid_imports_kwh':4000,'generation_kwh':3000,'self_consumed_kwh':2000},287.9),
    ('GP04', {'statements_per_year':12,'sheets_per_statement':2,'switch_fraction':1},24),
])
def test_carbon_scenarios(api, pid, inputs, expected):
    cid = candidate(pid)
    before = api.get('/customers/' + cid).json()
    response = api.post('/scenarios', json={'customerId':cid,'productId':pid,'inputs':inputs})
    assert response.status_code == 200, response.text
    r = response.json()
    assert r['annualDifference']['value'] == pytest.approx(expected)
    assert r['statusUnchanged'] is True
    assert api.get('/customers/' + cid).json() == before
    if pid == 'GP04':
        assert r['annualDifference']['unit'] == 'sheets/year'
        assert r['baseline']['emissions']['value'] is None
    else: assert r['factors']


def test_rejections(api):
    assert api.post('/scenarios',json={'customerId':candidate('GP01'),'productId':'GP01','inputs':{}}).status_code == 422
    assert api.post('/scenarios',json={'customerId':'UNKNOWN','productId':'GP01','inputs':{}}).status_code == 404
    blocked = next((c['id'],o['productId']) for c in app.state.service.customers.values() for o in c['opportunities'] if o['status']=='ruled_out')
    assert api.post('/scenarios',json={'customerId':blocked[0],'productId':blocked[1],'inputs':{}}).status_code == 422
    assert api.post('/scenarios',json={'customerId':candidate('GP03'),'productId':'GP03','inputs':{'grid_imports_kwh':100,'generation_kwh':200,'self_consumed_kwh':150}}).status_code == 422


def test_reports_and_units(api):
    for endpoint in ['/insights','/methodology','/portfolio']:
        r = api.get(endpoint)
        assert r.status_code == 200, r.text
        json.dumps(r.json(), allow_nan=False)
    s = app.state.service
    c = next(c for c in s.customers.values() if c['vehicle'])
    assert c['vehicle']['annualDistance']['unit'] == 'miles/year'
    assert c['vehicle']['annualDistance']['value'] == float(s.group('vehicles',c['id']).iloc[0].annual_mileage)


def test_missing_service_fails_closed(api):
    saved = app.state.service
    app.state.service = None
    try:
        for path in ['/health','/portfolio','/customers','/insights']:
            assert api.get(path).status_code == 503
    finally:
        app.state.service = saved
