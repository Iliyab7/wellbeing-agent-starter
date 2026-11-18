"""Resumable private installation. Output contains paths/status, never credentials."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wellbeing.core import atomic_json, read_json
from wellbeing import __version__
from wellbeing.database import Database, ROLES, Denied
from wellbeing.iphone import validate_public_url


def bootstrap(home=None, public_url=None, *, timezone_name='Asia/Tehran'):
    # Validate before creating state, credentials or a venv.
    chosen = validate_public_url(public_url) if public_url else None
    db = Database(home)
    lock = db.home / '.bootstrap-lock'
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ValueError('Bootstrap active or stale lock; investigate before retry') from exc
    try:
        os.close(fd)
        credentials_path = db.home / 'credentials.private.json'
        setup_path = db.home / 'setup.private.json'
        for path in (credentials_path, setup_path, db.home / 'mcp.private.json', db.home / 'capabilities.private.json'):
            if path.is_symlink():
                raise ValueError('Refusing symlink private configuration')
        old_setup = read_json(setup_path) if setup_path.exists() else {}
        if chosen is None and old_setup.get('public_url'):
            chosen = validate_public_url(old_setup['public_url'])
        if credentials_path.exists():
            credentials = read_json(credentials_path)
            if not isinstance(credentials, dict) or set(credentials) != set(ROLES):
                raise ValueError('Incomplete credentials file; explicit recovery needed')
            for role, token in credentials.items():
                try:
                    principal = db.principal(token)
                except Denied:
                    # Pairing deliberately rotates intake; its old bootstrap copy is not restored.
                    if role == 'intake':
                        continue
                    raise ValueError('Role credential invalid; explicit recovery needed') from None
                if principal['role'] != role or principal['participant'] != 'owner':
                    raise ValueError('Credential identity mismatch; explicit recovery needed')
        else:
            with db.connect() as c:
                if c.execute('SELECT COUNT(*) FROM participants').fetchone()[0] or c.execute('SELECT COUNT(*) FROM tokens').fetchone()[0]:
                    raise ValueError('Credentials missing from existing store; explicit recovery needed')
            credentials = db.provision(timezone_name=timezone_name)
            atomic_json(credentials_path, credentials)
        caps = db.home / 'capabilities.private.json'
        if not caps.exists():
            atomic_json(caps, {'status': 'awaiting_actual_host_probe', 'receipts': {}})
        required = {'WELLBEING_MVP_HOME': str(db.home)}
        if chosen:
            required['WELLBEING_PUBLIC_URL'] = chosen
        servers = {}
        for role, token in credentials.items():
            if role != 'intake':
                servers['wellbeing-' + role] = {'command': sys.executable,
                    'args': [str(ROOT / 'scripts' / 'run_mcp.py')],
                    'env': {**required, 'WELLBEING_ROLE_TOKEN': token}}
        mcp_path = db.home / 'mcp.private.json'
        atomic_json(mcp_path, {'mcpServers': servers})
        receipt = {'version': __version__,
            'private_home': str(db.home), 'database': 'initialized',
            'credentials': 'preserved_in_private_file', 'mcp_config': str(mcp_path),
            'capabilities': 'actual_host_receipts_required', 'agents': 'definitions_not_spawned',
            'iphone': 'awaiting_actual_device_intake', 'channel': 'actual_host_connector_required',
            'scheduler': 'external_registration_required', 'encryption_at_rest': 'not_provided',
            'serve_command': [sys.executable, str(ROOT / 'scripts' / 'run_server.py')],
            'host_tick_command': [sys.executable, str(ROOT / 'scripts' / 'host_tick.py'), '--help'],
            'required_environment': required}
        if chosen:
            receipt['public_url'] = chosen
        atomic_json(setup_path, receipt)
        return receipt
    finally:
        lock.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--home'); parser.add_argument('--public-url')
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    if args.public_url:
        validate_public_url(args.public_url)
    if args.install:
        import venv
        db = Database(args.home); runtime = db.home / 'runtime-venv'
        if runtime.is_symlink():
            raise ValueError('Refusing symlink runtime directory')
        python = runtime / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        if not python.exists():
            venv.create(runtime, with_pip=True)
        subprocess.run([str(python), '-m', 'pip', 'install', '--disable-pip-version-check', '-r', str(ROOT / 'requirements-mvp.txt')], check=True)
        command = [str(python), str(Path(__file__).resolve()), '--home', str(db.home)]
        if args.public_url:
            command += ['--public-url', args.public_url]
        subprocess.run(command, check=True)
    else:
        print(json.dumps(bootstrap(args.home, args.public_url), ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
