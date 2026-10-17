import os
import pytest
from backend.local_env import load_gemini_env, KEYS


def test_load_quotes_comments_and_allowlist(tmp_path, monkeypatch):
    for key in KEYS:
        monkeypatch.delenv(key, raising=False)
    path = tmp_path / '.env'
    path.write_text('\ufeffGEMINI_API_KEY="test-key" # comment\nexport GEMINI_MODEL=example-model # note\nGEMINI_ENABLED=false\nVITE_SECRET=do-not-load\n', encoding='utf-8')
    load_gemini_env(path)
    assert os.environ['GEMINI_API_KEY'] == 'test-key'
    assert os.environ['GEMINI_MODEL'] == 'example-model'
    assert os.environ['GEMINI_ENABLED'] == 'false'
    assert 'VITE_SECRET' not in os.environ


def test_environment_override_and_missing_file(tmp_path, monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'override')
    path = tmp_path / '.env'
    load_gemini_env(path)
    path.write_text('GEMINI_API_KEY=file-key')
    load_gemini_env(path)
    assert os.environ['GEMINI_API_KEY'] == 'override'


def test_bad_quote_does_not_expose_secret(tmp_path, monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    path = tmp_path / '.env'
    path.write_text('GEMINI_API_KEY="never-print-this')
    with pytest.raises(ValueError) as exc:
        load_gemini_env(path)
    assert 'never-print-this' not in str(exc.value)
