"""Synthetic actual-TCP smoke, isolated temporary memory; no real channel sends."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.bootstrap import bootstrap
from wellbeing.core import read_json

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='wellbeing-synthetic-') as home:
        bootstrap(home); bootstrap(home)
        keys = read_json(Path(home) / 'credentials.private.json')
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
        base = f'http://127.0.0.1:{port}'
        env = {**os.environ, 'WELLBEING_MVP_HOME': home, 'WELLBEING_BIND': '127.0.0.1', 'PORT': str(port)}
        env.pop('WELLBEING_PUBLIC_URL', None)

        def request(path, role='host', body=None):
            data = json.dumps(body).encode() if body is not None else None
            req = Request(base + path, data=data, headers={'Authorization': 'Bearer ' + keys[role], 'Content-Type': 'application/json'})
            with urlopen(req, timeout=5) as response:
                return json.load(response)

        def start():
            process = subprocess.Popen([sys.executable, str(ROOT / 'scripts' / 'run_server.py')], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                deadline = time.monotonic() + 20
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise RuntimeError('Synthetic HTTP server exited')
                    try:
                        request('/healthz'); return process
                    except (URLError, HTTPError, TimeoutError):
                        time.sleep(0.1)
                raise RuntimeError('Synthetic HTTP server did not become ready')
            except BaseException:
                process.terminate(); process.wait(timeout=10); raise

        def stop(process):
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(timeout=5)

        process = start()
        try:
            request('/v1/config', body={'categories': ['metrics'], 'role_categories': {r: ['metrics'] for r in ('host', 'manager', 'analyst', 'coach')}})
            sample = {'data': {'metrics': [{'name': 'synthetic_steps', 'units': 'count', 'data': [{'date': datetime.now(timezone.utc).isoformat(), 'qty': 123, 'source': 'synthetic'}]}]}}
            assert request('/v1/intake/health', 'intake', sample)['inserted'] == 1
            assert request('/v1/intake/health', 'intake', sample)['unchanged'] == 1
            sample['data']['metrics'][0]['data'][0]['qty'] = 124
            assert request('/v1/intake/health', 'intake', sample)['updated'] == 1
            rid = request('/v1/records')[0]['id']
            request('/v1/tasks/create', 'manager', {'id': 'synthetic-task', 'role': 'analyst', 'objective': 'Describe fixture only', 'acceptance': ['preserve uncertainty'], 'evidence_ids': [rid]})
            task = request('/v1/tasks/claim', 'analyst', {})
            request('/v1/tasks/report', 'analyst', {'id': task['id'], 'claim_token': task['claim_token'], 'result': 'Synthetic observation only', 'uncertainty': ['not real phone evidence']})
            request('/v1/tasks/review', 'manager', {'id': task['id'], 'decision': 'accept', 'reason': 'Compared synthetic source'})
            request('/v1/tasks/close', 'manager', {'id': task['id']})
            request('/v1/entries', 'manager', {'id': 'synthetic-section', 'kind': 'packet', 'payload': {'text': 'بخش آزمایشی؛ داده‌ها ساختگی هستند.'}})
            delivery = request('/v1/outbox/claim', body={})[0]
            request('/v1/outbox/ack', body={**delivery, 'receipt_ref': 'synthetic-receipt-no-send'})
        finally:
            stop(process)
        process = start()
        try:
            rows = request('/v1/records')
            assert len(rows) == 1 and rows[0]['revision'] == 2 and rows[0]['payload']['qty'] == 124
            request('/v1/config', body={'categories': [], 'role_categories': {}})
            assert request('/v1/records') == []
            request('/v1/privacy/delete', body={'confirm': 'delete_private_runtime_records'})
            try:
                request('/v1/status')
            except HTTPError as exc:
                assert exc.code == 403
            else:
                raise AssertionError('Deleted credentials still accepted')
        finally:
            stop(process)
    print(json.dumps({'synthetic_http_restart_smoke': 'passed', 'real_device': 'unverified', 'channel_send': 'not_performed'}))


if __name__ == '__main__':
    main()
