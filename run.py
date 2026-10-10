"""Start both local services: python run.py"""
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

root=Path(__file__).resolve().parent
os.chdir(root)
processes=[]
try:
    processes.append(subprocess.Popen([sys.executable,'-m','uvicorn','backend.main:app','--host','127.0.0.1','--port','8000']))
    for _ in range(60):
        if processes[0].poll() is not None: raise RuntimeError('Backend failed to start. Check port 8000 and installed dependencies.')
        try:
            with urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=1) as response:
                if response.status==200: break
        except OSError: time.sleep(.25)
    else: raise RuntimeError('Backend health check timed out.')
    processes.append(subprocess.Popen([sys.executable,'-m','streamlit','run','frontend/app.py','--server.address','127.0.0.1','--server.port','8501']))
    print('\nGreenPath: http://localhost:8501\nAPI docs: http://localhost:8000/docs\nCtrl+C stops both services.\n')
    while all(p.poll() is None for p in processes): time.sleep(.5)
except KeyboardInterrupt: pass
finally:
    for p in processes:
        if p.poll() is None: p.terminate()
    for p in processes:
        try: p.wait(timeout=5)
        except subprocess.TimeoutExpired: p.kill()
