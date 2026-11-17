"""Inspect an existing store without initializing it or exposing payloads/secrets."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import sqlite3
import sys
from urllib.request import urlopen
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wellbeing.core import private_path

EXPECTED = {'fastapi': '0.163.1', 'uvicorn': '0.54.0', 'mcp': '1.30.0', 'httpx': '0.28.1', 'tzdata': '2026.6'}


def doctor(home=None, health_url=None):
    chosen = private_path(home or os.environ.get('WELLBEING_MVP_HOME') or Path.home() / '.wellbeing-mvp')
    versions = {}
    for name, expected in EXPECTED.items():
        try:
            actual = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            actual = None
        versions[name] = {'installed': actual, 'expected': expected, 'matches': actual == expected}
    result = {'initialized': False, 'dependencies': versions, 'device_verified': False,
              'channel_verified': False, 'scheduler_verified': False,
              'encryption_at_rest': 'not_provided', 'filesystem_permissions': 'OS ACL/disk configuration must be checked by deployment owner'}
    path = chosen / 'memory.sqlite3'
    if path.is_symlink():
        raise ValueError('Refusing symlink database')
    if path.exists():
        c = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=5)
        try:
            result['integrity'] = c.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
            result['initialized'] = bool(c.execute('SELECT COUNT(*) FROM participants').fetchone()[0])
            result['stored_health_records'] = c.execute('SELECT COUNT(*) FROM records').fetchone()[0]
            result['delivery_states'] = dict(c.execute('SELECT status,COUNT(*) FROM outbox GROUP BY status'))
            result['capability_receipts'] = []
            for (raw,) in c.execute('SELECT config FROM participants'):
                cfg = json.loads(raw)
                for name, cap in cfg.get('host_capabilities', {}).items():
                    if isinstance(cap, dict):
                        result['capability_receipts'].append({'capability': name, 'status': cap.get('status'), 'receipt_present': bool(cap.get('receipt_ref')), 'checked_at': cap.get('checked_at')})
        finally:
            c.close()
    if health_url:
        # Explicit optional probe, not inferred external reachability.
        try:
            with urlopen(health_url.rstrip('/') + '/healthz', timeout=5) as response:
                body = json.load(response)
            result['service_probe'] = {'ok': body.get('ok') is True, 'queue_producer': body.get('queue_producer')}
        except Exception:
            result['service_probe'] = {'ok': False}
    result['note'] = 'Counts and synthetic receipts do not prove phone origin, channel sends or live recurring host jobs.'
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--home'); p.add_argument('--health-url')
    args = p.parse_args()
    print(json.dumps(doctor(args.home, args.health_url), indent=2))
