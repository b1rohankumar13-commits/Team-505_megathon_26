"""Start FastAPI and React, checking model readiness before opening the UI."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

root = Path(__file__).resolve().parent
settings = root / '.runtime' / 'local.json'
if settings.exists():
    for key, value in json.loads(settings.read_text()).items():
        if key != 'python': os.environ.setdefault(key, value)
port = int(os.environ.get('GREEN_API_PORT', '8001'))
base = f'http://127.0.0.1:{port}'
os.environ.setdefault('VITE_GREEN_API_URL', base)
processes = []
try:
    try:
        with urllib.request.urlopen(base + '/health', timeout=2) as response:
            if json.load(response).get('mode') != 'model_inference': raise RuntimeError('Port is occupied by a different backend')
    except urllib.error.URLError as exc:
        if isinstance(exc, urllib.error.HTTPError): raise RuntimeError('Existing backend is unhealthy. Stop it and retry.') from exc
        processes.append(subprocess.Popen([sys.executable, '-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', str(port)], cwd=root))
        for _ in range(180):
            if processes[-1].poll() is not None: raise RuntimeError('Backend failed; see error above')
            try:
                with urllib.request.urlopen(base + '/health', timeout=1) as response:
                    if json.load(response).get('mode') == 'model_inference': break
            except urllib.error.HTTPError as error:
                raise RuntimeError(error.read().decode()) from error
            except urllib.error.URLError: time.sleep(1)
        else: raise RuntimeError('Models did not become ready in 180 seconds')
    npm = shutil.which('npm.cmd' if os.name == 'nt' else 'npm')
    if not npm: raise RuntimeError('Install Node.js/npm first')
    frontend_env = {k: v for k, v in os.environ.items() if not k.startswith('GEMINI_')}
    processes.append(subprocess.Popen([npm, 'run', 'dev', '--', '--port', '8080', '--strictPort'], cwd=root, env=frontend_env))
    print('UI: http://localhost:8080  API: ' + base + '/docs', flush=True)
    while all(p.poll() is None for p in processes): time.sleep(.5)
finally:
    for p in processes:
        if p.poll() is None: p.terminate()
    for p in processes:
        try: p.wait(timeout=5)
        except subprocess.TimeoutExpired: p.kill()
