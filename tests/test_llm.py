import copy
import json
import httpx
import pytest
from backend.llm import Explainer


@pytest.fixture
def customer():
    return {'id': 'PRIVATE_ID', 'name': 'PRIVATE_NAME', 'opportunities': [{
        'productId': 'GP01', 'status': 'recommended', 'propensity': .82,
        'impact': {'annualDifference': {'value': 123}},
        'explanation': {'source': 'template', 'text': 'Synthetic impact: 123 kg. Eligibility not assessed.', 'generatedAt': 'fixed'},
    }]}


def transport(text, calls):
    def handle(request):
        calls.append(request)
        return httpx.Response(200, json={'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': json.dumps({'GP01': text})}]}}]})
    return httpx.MockTransport(handle)


def test_success_cache_no_mutation_or_private_identifiers(customer):
    calls = []
    before = copy.deepcopy(customer)
    e = Explainer(key='secret', transport=transport('The supplied signals support exploring this product.', calls))
    first = e.enrich(customer)
    assert first['opportunities'][0]['explanation']['source'] == 'llm'
    assert '123 kg' in first['opportunities'][0]['explanation']['text']
    assert e.enrich(customer) == first
    assert len(calls) == 1
    assert customer == before
    assert first['opportunities'][0]['impact'] == before['opportunities'][0]['impact']
    assert first['opportunities'][0]['propensity'] == .82
    assert 'PRIVATE' not in calls[0].content.decode()
    assert 'secret' not in str(calls[0].url)
    customer['opportunities'][0]['status'] = 'below_threshold'
    e.enrich(customer)
    assert len(calls) == 2


@pytest.mark.parametrize('text', ['You save 999 kilograms.', 'Your loan is approved.', '<script>alert()</script>', ''])
def test_invalid_narration_falls_back(customer, text):
    e = Explainer(key='secret', transport=transport(text, []))
    assert e.enrich(customer) == customer
    assert e.last_result == 'request_or_validation_failed'


def test_provider_failure_circuit_breaker(customer):
    calls = []
    def fail(request):
        calls.append(request)
        return httpx.Response(429)
    e = Explainer(key='secret', transport=httpx.MockTransport(fail))
    assert e.enrich(customer) == customer
    assert e.enrich(customer) == customer
    assert len(calls) == 1
    assert e.status()['lastResult'] == 'provider_http_429'


def test_missing_key_uses_templates(customer):
    e = Explainer(key='')
    assert e.enrich(customer) == customer
    assert not e.status()['configured']


def test_timeout_uses_template(customer):
    def fail(request):
        raise httpx.ReadTimeout('request failed')
    e = Explainer(key='secret', transport=httpx.MockTransport(fail))
    assert e.enrich(customer) == customer
