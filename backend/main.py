"""Live inference API. No seeded database or demo fallback."""
import logging
import os
import json
from pathlib import Path

_settings = Path(__file__).resolve().parents[1] / ".runtime" / "local.json"
if _settings.exists():
    for _key, _value in json.loads(_settings.read_text()).items():
        if _key != "python": os.environ.setdefault(_key, _value)
from contextlib import asynccontextmanager
from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict

@asynccontextmanager
async def lifespan(app):
    app.state.service = None
    app.state.failure = None
    try:
        from .model_service import ModelService
        app.state.service = ModelService()
    except Exception as exc:
        logging.exception('Model initialization failed')
        app.state.failure = f'Model service unavailable: {exc}'
    yield

app = FastAPI(title='Green Insights model inference', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=os.environ.get('GREEN_UI_ORIGINS', 'http://localhost:8080,http://127.0.0.1:8080').split(','), allow_methods=['GET', 'POST'], allow_headers=['Content-Type', 'Accept'])

def service():
    if getattr(app.state, 'service', None) is None: raise HTTPException(503, getattr(app.state, 'failure', None) or 'Models are starting')
    return app.state.service

@app.get('/health')
def health():
    s = service()
    return {'status': 'ok', 'mode': 'model_inference', 'customers': len(s.customers), 'data': 'synthetic cohort', 'llm': 'not_connected'}

@app.get('/portfolio')
def portfolio(): return service().portfolio()
@app.get('/customers')
def customers(): return service().list_customers()
@app.get('/customers/{cid}')
def customer(cid: str):
    s = service()
    if cid not in s.customers: raise HTTPException(404, 'Customer not found')
    return s.customers[cid]
@app.get('/insights')
def insights(): return service().insights()
@app.get('/methodology')
def methodology(): return service().methodology()

class ScenarioRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    customerId: str
    productId: Literal['GP01', 'GP02', 'GP03', 'GP04']
    inputs: dict[str, float | int | str]

@app.post('/scenarios')
def scenario(body: ScenarioRequest):
    s = service()
    if body.customerId not in s.customers: raise HTTPException(404, 'Customer not found')
    try: return s.scenario(body.customerId, body.productId, body.inputs)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc
