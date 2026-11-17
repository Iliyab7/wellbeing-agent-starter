"""Private SQLite primary memory. No encryption or external synchronization implied."""
from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import sqlite3
from .core import private_path, participant_zone

ROLES = ('manager', 'analyst', 'coach', 'companion', 'host', 'intake')
CATEGORIES = ('metrics', 'workouts', 'symptoms', 'stateOfMind', 'ecg',
              'heartRateNotification', 'cycleTracking', 'medications')


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def packed(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':'))


def digest(value):
    if not isinstance(value, str):
        raise ValueError('Expected text')
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


class Denied(ValueError):
    pass


SCHEMA = (
    'CREATE TABLE IF NOT EXISTS participants(id TEXT PRIMARY KEY, config TEXT NOT NULL)',
    'CREATE TABLE IF NOT EXISTS tokens(hash TEXT PRIMARY KEY,participant TEXT NOT NULL,role TEXT NOT NULL,revoked INTEGER DEFAULT 0)',
    'CREATE TABLE IF NOT EXISTS records(participant TEXT,id TEXT,category TEXT,metric TEXT,event_at TEXT,received_at TEXT,payload TEXT,revision INTEGER DEFAULT 1,PRIMARY KEY(participant,id))',
    'CREATE TABLE IF NOT EXISTS revisions(participant TEXT,id TEXT,revision INTEGER,payload TEXT,changed_at TEXT,PRIMARY KEY(participant,id,revision))',
    'CREATE TABLE IF NOT EXISTS receipts(id TEXT PRIMARY KEY,participant TEXT,kind TEXT,created_at TEXT,result TEXT)',
    'CREATE TABLE IF NOT EXISTS entries(participant TEXT,id TEXT,kind TEXT,actor TEXT,payload TEXT,updated_at TEXT,PRIMARY KEY(participant,id))',
    'CREATE TABLE IF NOT EXISTS tasks(participant TEXT,id TEXT,role TEXT,status TEXT,contract TEXT,report TEXT,review TEXT,lease_until TEXT,claim_hash TEXT,PRIMARY KEY(participant,id))',
    "CREATE TABLE IF NOT EXISTS outbox(participant TEXT,id TEXT,kind TEXT,payload TEXT,status TEXT DEFAULT 'pending',created_at TEXT,lease_until TEXT,claim_hash TEXT,delivery_receipt TEXT,PRIMARY KEY(participant,id))",
    'CREATE TABLE IF NOT EXISTS pairing(hash TEXT PRIMARY KEY,participant TEXT,expires_at TEXT,used INTEGER DEFAULT 0)',
    'CREATE INDEX IF NOT EXISTS records_category ON records(participant,category,event_at)',
)


class Database:
    def __init__(self, home=None):
        self.home = private_path(home or os.environ.get('WELLBEING_MVP_HOME') or Path.home() / '.wellbeing-mvp')
        self.home.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.path = self.home / 'memory.sqlite3'
        for suffix in ('', '-wal', '-shm'):
            if Path(str(self.path) + suffix).is_symlink():
                raise ValueError('Refusing symlink database files')
        c = self._open()
        try:
            version = c.execute('PRAGMA user_version').fetchone()[0]
            if version > 1:
                raise ValueError('Unsupported database version; restore compatible runtime')
            c.execute('PRAGMA journal_mode=WAL')
            c.execute('BEGIN IMMEDIATE')
            for statement in SCHEMA:
                c.execute(statement)
            c.execute('PRAGMA user_version=1')
            c.commit()
        except BaseException:
            c.rollback()
            raise
        finally:
            c.close()
        if os.name != 'nt':
            self.home.chmod(0o700)
            for suffix in ('', '-wal', '-shm'):
                path = Path(str(self.path) + suffix)
                if path.exists():
                    path.chmod(0o600)

    def _open(self):
        c = sqlite3.connect(self.path, timeout=20, isolation_level=None)
        c.row_factory = sqlite3.Row
        c.execute('PRAGMA foreign_keys=ON')
        c.execute('PRAGMA busy_timeout=20000')
        c.execute('PRAGMA synchronous=FULL')
        c.execute('PRAGMA secure_delete=ON')
        return c

    @contextmanager
    def connect(self):
        c = self._open()
        try:
            c.execute('BEGIN IMMEDIATE')
            yield c
            c.commit()
        except BaseException:
            c.rollback()
            raise
        finally:
            c.close()

    def provision(self, participant='owner', timezone_name='Asia/Tehran'):
        participant_zone(timezone_name)
        if not isinstance(participant, str) or not participant or len(participant) > 100:
            raise ValueError('Invalid participant identifier')
        with self.connect() as c:
            if c.execute('SELECT 1 FROM participants WHERE id=?', (participant,)).fetchone():
                raise ValueError('Participant already exists; resume or explicitly recover credentials')
            cfg = {'timezone': timezone_name, 'enabled': True, 'categories': [], 'retention_days': 30,
                   'role_categories': {r: [] for r in ROLES if r != 'intake'},
                   'reminders': {'enabled': False, 'meals': {}, 'quiet_start': '22:00',
                                 'quiet_end': '08:00', 'grace_minutes': 120, 'daily_budget': 3},
                   'host_capabilities': {}, 'native_instances': {}, 'opengym': {'enabled': False}}
            c.execute('INSERT INTO participants VALUES(?,?)', (participant, packed(cfg)))
            result = {}
            for role in ROLES:
                token = secrets.token_urlsafe(32)
                c.execute('INSERT INTO tokens(hash,participant,role) VALUES(?,?,?)', (digest(token), participant, role))
                result[role] = token
        return result

    def principal(self, token):
        if not isinstance(token, str) or not token or len(token) > 1024:
            raise Denied('Invalid or revoked credential')
        with self.connect() as c:
            key = digest(token)
            row = c.execute('SELECT participant,role FROM tokens WHERE hash=? AND revoked=0', (key,)).fetchone()
        if not row:
            raise Denied('Invalid or revoked credential')
        return {**dict(row), '_credential_hash': key}

    def authorize(self, p, c):
        if not isinstance(p, dict) or not isinstance(p.get('_credential_hash'), str):
            raise Denied('Authenticated principal required')
        row = c.execute('SELECT participant,role FROM tokens WHERE hash=? AND revoked=0', (p['_credential_hash'],)).fetchone()
        if not row or row['participant'] != p.get('participant') or row['role'] != p.get('role'):
            raise Denied('Invalid or revoked credential')

    def config(self, participant, c=None):
        if c is None:
            with self.connect() as conn:
                return self.config(participant, conn)
        row = c.execute('SELECT config FROM participants WHERE id=?', (participant,)).fetchone()
        if not row:
            raise Denied('Unknown participant')
        return json.loads(row[0])

    def receipt(self, c, participant, kind, result):
        rid = 'receipt-' + secrets.token_hex(12)
        c.execute('INSERT INTO receipts VALUES(?,?,?,?,?)', (rid, participant, kind, utcnow(), packed(result)))
        return rid
