"""Import an authorized Health Auto Export attachment without a web service."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.bootstrap import bootstrap
from wellbeing.core import PilotError, participant_zone, private_path, read_json
from wellbeing.database import CATEGORIES, Database
from wellbeing.service import Service

MAX_ATTACHMENT_BYTES = 30 * 1024 * 1024


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('Nonfinite JSON number')


def decode_attachment(raw):
    if not raw or len(raw) > MAX_ATTACHMENT_BYTES:
        raise ValueError('Attachment must be nonempty and below 30 MiB')
    try:
        return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique_object,
                          parse_constant=reject_constant)
    except (ValueError, RecursionError):
        raise ValueError('Expected a Health Auto Export JSON v2 attachment') from None


def open_store(home, role):
    folder = private_path(home or os.environ.get('WELLBEING_MVP_HOME') or Path.home() / '.wellbeing-mvp')
    credentials = folder / 'credentials.private.json'
    if not (folder / 'memory.sqlite3').is_file() or not credentials.is_file() or credentials.is_symlink():
        raise ValueError('Private Wellbeing store unavailable. Use init for a new store.')
    db = Database(folder)
    principal = db.principal(read_json(credentials)[role])
    if principal['role'] != role:
        raise ValueError('Role credential does not match')
    return Service(db), principal


def import_attachment(service, principal, raw, stream, observed_at):
    payload = decode_attachment(raw)
    return service.ingest(principal, payload, file_import={
        'sha256': hashlib.sha256(raw).hexdigest(),
        'stream': stream,
        'observed_at': observed_at,
    })


def demo():
    now = datetime.now(timezone.utc)
    raw = json.dumps({'data': {'metrics': [
        {'name': 'step_count', 'units': 'count', 'data': [{'date': now.isoformat(), 'qty': 123}]}
    ]}}).encode()
    with tempfile.TemporaryDirectory(prefix='wellbeing-inbox-demo-') as folder:
        bootstrap(folder, timezone_name='UTC')
        service, host = open_store(folder, 'host')
        service.configure(host, {'categories': ['metrics'], 'role_categories': {
            'host': ['metrics'], 'analyst': ['metrics'],
        }})
        first = import_attachment(service, host, raw, 'synthetic-metrics', now.isoformat())
        service, host = open_store(folder, 'host')
        replay = import_attachment(service, host, raw, 'synthetic-metrics', now.isoformat())
        coverage = service.status(host)['categories']
        if first['inserted'] != 1 or replay['status'] != 'already_imported' or coverage[0]['count'] != 1:
            raise RuntimeError('Synthetic attachment import or restart check failed')
        return {'status': 'synthetic_demo_passed', 'first': first, 'replay': replay,
                'coverage': coverage, 'channel_verified': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', help='Private directory outside the checkout')
    commands = parser.add_subparsers(dest='command', required=True)
    init = commands.add_parser('init', help='Create or resume a private store without installing HTTP/MCP packages')
    init.add_argument('--timezone', default='UTC', help='New store timezone, e.g. UTC+03:30')
    scope = commands.add_parser('scope', help='Apply participant-approved categories and retention')
    scope.add_argument('--categories', nargs='+', choices=CATEGORIES, required=True)
    scope.add_argument('--retention-days', required=True, type=int)
    scope.add_argument('--timezone', required=True)
    ingest = commands.add_parser('import', help='Read a JSON attachment from a private path or stdin (-)')
    ingest.add_argument('attachment')
    ingest.add_argument('--stream', required=True, help='Stable label for one phone export automation')
    ingest.add_argument('--observed-at', required=True, help='Connector delivery/version time with UTC offset')
    commands.add_parser('status', help='Show imported coverage and freshness without raw measurements')
    records = commands.add_parser('records', help='Read actual scoped records through an authorized executor')
    records.add_argument('--category', choices=CATEGORIES)
    records.add_argument('--metric')
    records.add_argument('--limit', type=int, default=50)
    commands.add_parser('demo', help='Run disposable synthetic import/restart/replay verification')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            result = demo()
        elif args.command == 'init':
            participant_zone(args.timezone)
            setup = bootstrap(args.home, timezone_name=args.timezone)
            result = {'status': 'private_store_ready', 'version': setup['version'],
                      'transport': 'file_inbox', 'phone_verified': False}
        else:
            service, host = open_store(args.home, 'host')
            if args.command == 'scope':
                categories = list(dict.fromkeys(args.categories))
                current = service.db.config(host['participant'])['role_categories']
                grants = {role: [category for category in allowed if category in categories]
                          for role, allowed in current.items()}
                grants['host'] = categories
                service.configure(host, {'categories': categories, 'retention_days': args.retention_days,
                                         'timezone': args.timezone, 'role_categories': grants})
                result = {'status': 'scope_saved', 'categories': categories}
            elif args.command == 'import':
                if args.attachment == '-':
                    raw = sys.stdin.buffer.read(MAX_ATTACHMENT_BYTES + 1)
                else:
                    with Path(args.attachment).open('rb') as attachment:
                        raw = attachment.read(MAX_ATTACHMENT_BYTES + 1)
                result = import_attachment(service, host, raw, args.stream, args.observed_at)
            elif args.command == 'status':
                result = service.status(host)
            else:
                result = service.records(host, category=args.category, metric=args.metric, limit=args.limit)
    except (ValueError, OSError, PilotError, KeyError, TypeError, RecursionError):
        print(json.dumps({'status': 'rejected', 'command': args.command,
                          'help': 'Check private store, approved scope, source time and JSON v2 attachment.'}))
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
