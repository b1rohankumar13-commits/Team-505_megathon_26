from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Literal
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from . import db
from .domain import CATALOGUE, CATEGORIES, CUTOFF, opportunities, scenario

@asynccontextmanager
async def lifespan(app):
    db.init_db()
    yield

app=FastAPI(title='GreenPath Insights API',version='1.0.0',lifespan=lifespan,description='Local synthetic-data UI prototype. Demo scores are not trained probabilities.')
ProductID=Literal['GP01','GP02','GP03','GP04']

def require_customer(cid):
    c=db.customer(cid)
    if c is None: raise HTTPException(404,'Customer not found')
    return c

@app.get('/health')
def health(): return {'status':'ok','storage':'SQLite','mode':'synthetic_demo'}

@app.get('/catalogue')
def catalogue(): return CATALOGUE

@app.get('/customers')
def customers(): return db.all_customers()

@app.get('/customers/{cid}')
def get_customer(cid:str):
    c=require_customer(cid)
    return {'customer':c,'opportunities':opportunities(c),'transactions':db.customer_transactions(cid)}

@app.get('/opportunities')
def get_opportunities():
    return [dict(o, name=c['name'],region=c['region']) for c in db.all_customers() for o in opportunities(c)]

class ScenarioInput(BaseModel):
    product_id: ProductID
    efficiency:float=Field(.18,ge=.05,le=.6)
    reduction:float=Field(.2,ge=0,le=.8)
    generation:float=Field(3500,ge=0,le=30000)
    self_consumption:float=Field(.6,ge=0,le=1)
    sheets:int=Field(2,ge=1,le=20)

@app.post('/customers/{cid}/scenario')
def estimate(cid:str,body:ScenarioInput):
    return scenario(require_customer(cid),pid=body.product_id,**body.model_dump(exclude={'product_id'}))

@app.post('/customers/{cid}/scenarios',status_code=201)
def save_scenario(cid:str,body:ScenarioInput):
    result=estimate(cid,body)
    with db.connection() as conn:
        cursor=conn.execute('INSERT INTO scenarios(customer_id,payload,created_at) VALUES (?,?,?)',(cid,json.dumps({'inputs':body.model_dump(),'result':result}),datetime.now(timezone.utc).isoformat()))
    return {'id':cursor.lastrowid,'result':result}

class ActionInput(BaseModel):
    product_id:ProductID
    action:Literal['interested','dismissed','review_requested']

@app.post('/customers/{cid}/actions',status_code=201)
def save_action(cid:str,body:ActionInput):
    c=require_customer(cid)
    op=next(o for o in opportunities(c) if o['product_id']==body.product_id)
    if op['suitability']!='candidate' and body.action!='dismissed':
        raise HTTPException(409,'Only candidate opportunities can be explored or reviewed.')
    with db.connection() as conn:
        cursor=conn.execute('INSERT INTO actions(customer_id,product_id,action,created_at) VALUES (?,?,?,?)',(cid,body.product_id,body.action,datetime.now(timezone.utc).isoformat()))
    return {'id':cursor.lastrowid,'status':'recorded','message':'Local preference only; no application or external message sent.'}

@app.get('/customers/{cid}/history')
def history(cid:str):
    require_customer(cid)
    with db.connection() as conn:
        actions=[dict(r) for r in conn.execute('SELECT * FROM actions WHERE customer_id=? ORDER BY id DESC',(cid,))]
        scenarios=[dict(r) for r in conn.execute('SELECT * FROM scenarios WHERE customer_id=? ORDER BY id DESC',(cid,))]
    for s in scenarios: s['payload']=json.loads(s['payload'])
    return {'actions':actions,'scenarios':scenarios}

@app.get('/methodology')
def methodology():
    return {'cutoff':CUTOFF,'outcome_window':'90 days after cutoff (proposed; no labels or model trained)',
        'data':'100 fictional UK customers and 4,800 transactions, generated with fixed seed 42. No public datasets ingested.',
        'scores':'Deterministic illustrative rankings, not ML propensity. Propensity and confidence are null. Data completeness is the fraction of product inputs present; it is not model confidence.',
        'models':'Not supplied. No training, held-out performance or calibration claims.',
        'explanations':'Evidence-only deterministic templates; no external LLM calls.',
        'impact':'Annual activity scenarios only. Carbon unavailable until independently verified factors and compatible boundaries are integrated.',
        'eligibility':'Not assessed; institution-authorised checks are required.',
        'categories':CATEGORIES,
        'boundaries':'Explicit petrol purchases → Fuel; servicing → Automotive; electricity-only → Electricity; gas-only → Gas; combined energy or other bills → Utilities; unmatched → Other. Synthetic labels use explicit merchant mappings, not an evaluated classifier.',
        'source_status':[{'source':'Uploaded PS1 and architecture / ML / acquisition notes','status':'Used as requirements'}, {'source':'UK government 2026 factors','status':'Referenced in plan; not ingested or approved'}, {'source':'NEED / UCI / London smart meters','status':'Referenced in plan; not ingested'}]}
