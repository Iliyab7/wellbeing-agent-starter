"""Private transactional MVP storage, separate from the v0.1 reference JSON CLI."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import sqlite3

from .core import private_path

ROLES = ('manager', 'analyst', 'coach', 'companion', 'host', 'intake')
CATEGORIES = ('metrics', 'workouts', 'symptoms', 'stateOfMind', 'ecg',
              'heartRateNotification', 'cycleTracking', 'medications')


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def packed(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


class Denied(ValueError):
    pass


class Database:
    def __init__(self, home=None):
        self.home = private_path(home or os.environ.get('WELLBEING_MVP_HOME') or Path.home() / '.wellbeing-mvp')
        self.home.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.path = self.home / 'memory.sqlite3'
        if self.path.is_symlink():
            raise ValueError('Refusing symlink database')
        with self.connect() as c:
            c.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS participants(id TEXT PRIMARY KEY, config TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS tokens(hash TEXT PRIMARY KEY, participant TEXT NOT NULL,
                role TEXT NOT NULL, revoked INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS records(participant TEXT, id TEXT, category TEXT, metric TEXT,
                event_at TEXT, received_at TEXT, payload TEXT, revision INTEGER DEFAULT 1,
                PRIMARY KEY(participant,id));
            CREATE TABLE IF NOT EXISTS revisions(participant TEXT,id TEXT,revision INTEGER,payload TEXT,
                changed_at TEXT,PRIMARY KEY(participant,id,revision));
            CREATE TABLE IF NOT EXISTS receipts(id TEXT PRIMARY KEY,participant TEXT,kind TEXT,
                created_at TEXT,result TEXT);
            CREATE TABLE IF NOT EXISTS entries(participant TEXT,id TEXT,kind TEXT,actor TEXT,
                payload TEXT,updated_at TEXT,PRIMARY KEY(participant,id));
            CREATE TABLE IF NOT EXISTS tasks(participant TEXT,id TEXT,role TEXT,status TEXT,
                contract TEXT,report TEXT,review TEXT,lease_until TEXT,claim_hash TEXT,
                PRIMARY KEY(participant,id));
            CREATE TABLE IF NOT EXISTS outbox(participant TEXT,id TEXT,kind TEXT,payload TEXT,
                status TEXT DEFAULT 'pending',created_at TEXT,lease_until TEXT,claim_hash TEXT,
                delivery_receipt TEXT,PRIMARY KEY(participant,id));
            CREATE TABLE IF NOT EXISTS pairing(hash TEXT PRIMARY KEY,participant TEXT,expires_at TEXT,used INTEGER DEFAULT 0);
            CREATE INDEX IF NOT EXISTS records_category ON records(participant,category,event_at);
            ''')
        try:
            self.path.chmod(0o600)
        except OSError:
            pass

    @contextmanager
    def connect(self):
        c = sqlite3.connect(self.path, timeout=20, isolation_level=None)
        c.row_factory = sqlite3.Row
        c.execute('PRAGMA foreign_keys=ON')
        c.execute('PRAGMA busy_timeout=20000')
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
        # Provisioning does not itself grant Health permissions or enable reminders.
        with self.connect() as c:
            c.execute('INSERT OR IGNORE INTO participants VALUES(?,?)', (participant, packed({
                'timezone': timezone_name, 'enabled': True, 'categories': [], 'retention_days': 30,
                'role_categories': {'host': [], 'manager': [], 'analyst': [], 'coach': [], 'companion': []},
                'reminders': {'enabled': False, 'meals': {}, 'quiet_start': '22:00', 'quiet_end': '08:00',
                              'grace_minutes': 120, 'daily_budget': 3},
                'host_capabilities': {}, 'native_instances': {}, 'opengym': {'enabled': False},
            })))
            result = {}
            for role in ROLES:
                token = secrets.token_urlsafe(32)
                c.execute('INSERT INTO tokens(hash,participant,role) VALUES(?,?,?)', (digest(token), participant, role))
                result[role] = token
        return result

    def principal(self, token):
        with self.connect() as c:
            row = c.execute('SELECT participant,role FROM tokens WHERE hash=? AND revoked=0', (digest(token),)).fetchone()
        if not row:
            raise Denied('Invalid or revoked credential')
        return dict(row)

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
