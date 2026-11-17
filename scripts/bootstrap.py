"""Resumable noninteractive private installation; never print credentials to chat."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wellbeing.database import Database, packed
from wellbeing.iphone import validate_public_url


def bootstrap(home=None, public_url=None):
    db = Database(home)
    cred_file = db.home / 'credentials.private.json'
    if cred_file.is_symlink():
        raise ValueError('Refusing symlink credentials')
    if not cred_file.exists():
        with db.connect() as c:
            if c.execute('SELECT COUNT(*) FROM tokens').fetchone()[0]:
                raise ValueError('Credentials file missing from initialized store; explicit credential recovery needed')
        credentials = db.provision()
        fd = os.open(cred_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(packed(credentials))
    else:
        credentials = json.loads(cred_file.read_text(encoding='utf-8'))
    # A verified capability is always a host-supplied receipt, never a guessed platform name.
    cap = db.home / 'capabilities.private.json'
    if not cap.exists():
        cap.write_text(packed({'host': 'unknown', 'shell': False, 'native_agents': False,
                              'scheduler': False, 'whatsapp': False, 'vision': False,
                              'transcription': False, 'receipts': {}}), encoding='utf-8')
        cap.chmod(0o600)
    host_configs = {}
    for role, token in credentials.items():
        if role == 'intake':
            continue
        host_configs['wellbeing-' + role] = {'command': sys.executable,
            'args': [str(ROOT / 'scripts' / 'run_mcp.py')],
            'env': {'WELLBEING_MVP_HOME': str(db.home), 'WELLBEING_ROLE_TOKEN': token}}
    private_config = db.home / 'mcp.private.json'
    private_config.write_text(json.dumps({'mcpServers': host_configs}, indent=2), encoding='utf-8')
    private_config.chmod(0o600)
    receipt = {'version': '0.2.0', 'private_home': str(db.home), 'database': 'initialized',
               'credentials': 'preserved_in_private_file', 'mcp_config': str(private_config),
               'capabilities': 'awaiting_actual_host_probe', 'agents': 'definitions_ready_not_spawned',
               'iphone': 'awaiting_public_https_and_device_permissions',
               'channel': 'awaiting_host_connector_receipt', 'health_records': 'not_inferred',
               'serve_command': [sys.executable, str(ROOT / 'scripts' / 'run_server.py')],
               'required_environment': {'WELLBEING_MVP_HOME': str(db.home)}}
    if public_url:
        receipt['public_url'] = validate_public_url(public_url)
        receipt['required_environment']['WELLBEING_PUBLIC_URL'] = receipt['public_url']
        receipt['iphone'] = 'awaiting_reachability_probe_then_pairing'
    (db.home / 'setup.private.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return receipt


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--home')
    p.add_argument('--public-url')
    p.add_argument('--install', action='store_true', help='Install pinned optional runtime in a private venv')
    args = p.parse_args()
    if args.install:
        import venv
        private_home = Database(args.home).home
        venv_dir = private_home / 'runtime-venv'
        venv.create(venv_dir, with_pip=True)
        python = venv_dir / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(ROOT / 'requirements-mvp.txt')], check=True)
        subprocess.run([str(python), __file__, '--home', str(private_home)] + (['--public-url', args.public_url] if args.public_url else []), check=True)
        return
    print(json.dumps(bootstrap(args.home, args.public_url), ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
