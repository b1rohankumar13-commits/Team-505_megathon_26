import pytest
from fastapi.testclient import TestClient
from backend import db
from backend.main import app
from backend.domain import seed_customers, opportunities, scenario, transactions, CATEGORIES

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(db,'DB_PATH',tmp_path/'test.db')
    with TestClient(app) as c: yield c

def test_seed_and_contract(client):
    assert len(client.get('/customers').json())==100
    ops=client.get('/opportunities').json()
    assert len(ops)==400
    assert all(o['propensity'] is None and o['confidence'] is None for o in ops)
    assert all(o['eligibility']=='not_assessed' for o in ops)
    c=seed_customers()[0]
    assert set(t['category'] for t in transactions(c))==set(CATEGORIES)

def test_exclusions_and_missing(client):
    ops=client.get('/customers/C10002').json()['opportunities']
    assert ops[0]['suitability']=='suppressed'
    assert ops[3]['suitability']=='suppressed'
    assert client.post('/customers/C10002/actions',json={'product_id':'GP01','action':'interested'}).status_code==409
    missing=client.post('/customers/C10004/scenario',json={'product_id':'GP03'}).json()
    assert missing['status']=='not_calculated' and missing['metrics']=={}
    assert client.get('/customers/C10003').json()['opportunities'][1]['suitability']=='suppressed'

def test_scenarios_and_bounds(client):
    result=client.post('/customers/C10001/scenario',json={'product_id':'GP03','generation':30000,'self_consumption':1}).json()
    assert result['metrics']['grid_import_reduced_kwh']==4800
    assert result['metrics']['remaining_grid_import_kwh']==0
    assert result['carbon_kgco2e'] is None
    paper=client.post('/customers/C10001/scenario',json={'product_id':'GP04','sheets':3}).json()
    assert paper['metrics']['sheets_avoided']==72
    assert client.post('/customers/C10001/scenario',json={'product_id':'GP02','reduction':1.5}).status_code==422
    assert client.get('/customers/unknown').status_code==404

def test_storage_survives_reinitialization(client):
    assert client.post('/customers/C10001/actions',json={'product_id':'GP01','action':'interested'}).status_code==201
    assert client.post('/customers/C10001/scenarios',json={'product_id':'GP02'}).status_code==201
    db.init_db()
    h=client.get('/customers/C10001/history').json()
    assert len(h['actions'])==len(h['scenarios'])==1
    assert len(client.get('/customers').json())==100
