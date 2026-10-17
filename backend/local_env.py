"""Load only local Gemini settings; process environment always takes precedence."""
import os
import re
from pathlib import Path

KEYS = {'GEMINI_API_KEY', 'GEMINI_MODEL', 'GEMINI_ENABLED'}


def load_gemini_env(path=None):
    path = Path(path) if path is not None else Path(__file__).resolve().parents[1] / '.env'
    if not path.is_file():
        return
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        line = line.strip()
        if line.startswith('export '):
            line = line[7:].lstrip()
        key, sep, value = line.partition('=')
        key = key.strip()
        if not sep or key not in KEYS or key in os.environ:
            continue
        value = value.strip()
        if value.startswith(('"', "'")):
            quote = value[0]
            end = value.find(quote, 1)
            if end < 0 or (value[end + 1:].strip() and not value[end + 1:].strip().startswith('#')):
                raise ValueError(f'Invalid quoted setting for {key} in .env')
            value = value[1:end]
        else:
            value = re.split(r'\s+#', value, maxsplit=1)[0].rstrip()
        os.environ[key] = value
