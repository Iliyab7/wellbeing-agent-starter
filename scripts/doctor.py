"""Inspect private installation without exposing credentials or health payloads."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wellbeing.database import Database


def doctor(home=None):
    db = Database(home)
    with db.connect() as c:
        initialized = bool(c.execute('SELECT COUNT(*) FROM participants').fetchone()[0])
        records = c.execute('SELECT COUNT(*) FROM records').fetchone()[0]
    caps_path = db.home / 'capabilities.private.json'
    caps = json.loads(caps_path.read_text()) if caps_path.exists() else {}
    return {'initialized': initialized, 'stored_health_records': records,
            'dependencies': {name: importlib.util.find_spec(name) is not None for name in ('fastapi', 'uvicorn', 'mcp')},
            'capabilities': caps, 'iphone_verified': False,
            'note': 'Record count does not establish real-device origin. Check private device receipt separately.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--home')
    print(json.dumps(doctor(p.parse_args().home), indent=2))
