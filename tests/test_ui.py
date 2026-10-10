"""Render and interact with the real frontend using the real API in-process."""
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest
from backend import db
from backend.main import app

def test_ui_navigation_and_saved_interest(tmp_path,monkeypatch):
    monkeypatch.setattr(db,'DB_PATH',tmp_path/'ui.db')
    with TestClient(app) as client:
        def get(url,**kwargs): return client.get('/'+url.split('/',3)[3])
        def post(url,json,**kwargs): return client.post('/'+url.split('/',3)[3],json=json)
        with patch('requests.get',get),patch('requests.post',post):
            at=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'frontend'/'app.py'),default_timeout=30).run()
            assert not at.exception and not at.error
            for page in ['Customer 360','Scenario lab','Evidence & data']:
                at.radio(key='page').set_value(page).run()
                assert not at.exception and not at.error
            at.radio(key='page').set_value('Customer 360').run()
            at.button(key='interest-GP01').click().run()
            assert client.get('/customers/C10001/history').json()['actions'][0]['action']=='interested'
            at.button(key='scenario-GP01').click().run()
            assert at.radio(key='page').value=='Scenario lab'
            assert not at.exception and not at.error
