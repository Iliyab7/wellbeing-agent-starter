"""Host-neutral operations. Authentication/role checks apply equally to HTTP and MCP."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import re
import secrets
from zoneinfo import ZoneInfo

from .database import CATEGORIES, Database, Denied, digest, packed, utcnow


def instant(value):
    if not isinstance(value, str):
        return None
    try:
        d = datetime.fromisoformat(value.replace('Z', '+00:00').replace(' ', 'T', 1))
        return d.astimezone(timezone.utc).isoformat() if d.tzinfo else None
    except ValueError:
        return None


def require_role(principal, *roles):
    if principal['role'] not in roles:
        raise Denied('Operation unavailable to this role')


class Service:
    def __init__(self, db: Database):
        self.db = db

    def active(self, p, c=None):
        cfg = self.db.config(p['participant'], c)
        if not cfg['enabled']:
            raise Denied('Participant service paused')
        return cfg

    def configure(self, p, patch):
        require_role(p, 'host', 'manager')
        allowed = {'timezone', 'enabled', 'categories', 'role_categories', 'retention_days',
                   'reminders', 'host_capabilities', 'native_instances', 'opengym'}
        if not isinstance(patch, dict) or set(patch) - allowed:
            raise ValueError('Unknown configuration fields')
        with self.db.connect() as c:
            cfg = self.db.config(p['participant'], c)
            cfg.update(patch)
            ZoneInfo(cfg['timezone'])
            if type(cfg['enabled']) is not bool:
                raise ValueError('enabled must be boolean')
            if not isinstance(cfg['categories'], list) or set(cfg['categories']) - set(CATEGORIES):
                raise ValueError('Unknown Health data category')
            if type(cfg['retention_days']) is not int or not 1 <= cfg['retention_days'] <= 3650:
                raise ValueError('retention_days must be 1..3650')
            if not isinstance(cfg['role_categories'], dict):
                raise ValueError('role_categories must be an object')
            for role, cats in cfg['role_categories'].items():
                if role not in ('host', 'manager', 'analyst', 'coach', 'companion') or not isinstance(cats, list) or set(cats) - set(cfg['categories']):
                    raise ValueError('Role categories exceed active permission')
            r = cfg['reminders']
            if type(r.get('enabled')) is not bool or not isinstance(r.get('meals'), dict):
                raise ValueError('Invalid reminder configuration')
            if not 1 <= r.get('daily_budget', 3) <= 10 or not 1 <= r.get('grace_minutes', 120) <= 360:
                raise ValueError('Invalid reminder limits')
            for key, value in r['meals'].items():
                if key not in ('breakfast', 'lunch', 'dinner'):
                    raise ValueError('Unknown meal')
                self._time(value)
            self._time(r.get('quiet_start', '22:00'))
            self._time(r.get('quiet_end', '08:00'))
            c.execute('UPDATE participants SET config=? WHERE id=?', (packed(cfg), p['participant']))
            # Revoke queued work when permission changes; old prepared outputs must not leak.
            if any(k in patch for k in ('enabled', 'categories', 'role_categories')):
                c.execute("UPDATE tasks SET status='cancelled' WHERE participant=? AND status NOT IN ('closed','cancelled')", (p['participant'],))
                c.execute("UPDATE outbox SET status='cancelled' WHERE participant=? AND status IN ('pending','leased')", (p['participant'],))
            if 'reminders' in patch:
                c.execute("UPDATE outbox SET status='cancelled' WHERE participant=? AND kind='meal_reminder' AND status IN ('pending','leased')", (p['participant'],))
            self.db.receipt(c, p['participant'], 'configuration', {'changed': sorted(patch)})
        return cfg

    @staticmethod
    def _time(value):
        if not isinstance(value, str) or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', value):
            raise ValueError('Time must be HH:MM')
        return int(value[:2]) * 60 + int(value[3:])

    def ingest(self, p, payload):
        require_role(p, 'intake', 'host')
        if not isinstance(payload, dict):
            raise ValueError('Expected JSON object')
        data = payload.get('data', payload)
        if not isinstance(data, dict):
            raise ValueError('Expected data object')
        # Export versions are validated by shape; support all eight documented HAE categories.
        present = set(data) & set(CATEGORIES)
        if not present:
            raise ValueError('No supported Health Auto Export category found')
        counts = {'inserted': 0, 'updated': 0, 'unchanged': 0, 'unknown_time': 0}
        with self.db.connect() as c:
            cfg = self.active(p, c)
            if present - set(cfg['categories']):
                raise Denied('Upload contains an unapproved Health category; no records saved')
            items = []
            for category in sorted(present):
                rows = data[category]
                if not isinstance(rows, list):
                    raise ValueError('Category must be an array')
                for row in rows:
                    if not isinstance(row, dict):
                        raise ValueError('Record must be an object')
                    if category == 'metrics':
                        name = row.get('name')
                        if not isinstance(name, str) or not isinstance(row.get('data'), list):
                            raise ValueError('Metric requires name and data')
                        for sample in row['data']:
                            if not isinstance(sample, dict):
                                raise ValueError('Metric sample must be object')
                            items.append((category, name, {'name': name, 'units': row.get('units'), **sample}))
                    else:
                        items.append((category, '', row))
            if len(items) > 50000:
                raise ValueError('Too many records; use HAE batching')
            now = utcnow()
            for category, metric, item in items:
                event_at = instant(item.get('start') or item.get('startDate') or item.get('date'))
                if not event_at:
                    counts['unknown_time'] += 1
                # Stable IDs retain corrections rather than summing overlapping exports.
                identity = item.get('id') or item.get('uuid')
                if not identity:
                    identity = {k: item.get(k) for k in ('name', 'source', 'date', 'start', 'end', 'startDate', 'endDate', 'value')}
                    if not any(identity.get(k) for k in ('date', 'start', 'startDate')):
                        identity = item  # no timestamp: content-addressed, never infer occurrence
                rid = digest(packed([category, metric, identity]))
                body = packed(item)
                old = c.execute('SELECT payload,revision FROM records WHERE participant=? AND id=?', (p['participant'], rid)).fetchone()
                if old and old['payload'] == body:
                    counts['unchanged'] += 1
                    continue
                rev = old['revision'] + 1 if old else 1
                if old:
                    c.execute('INSERT INTO revisions VALUES(?,?,?,?,?)', (p['participant'], rid, old['revision'], old['payload'], now))
                c.execute('INSERT OR REPLACE INTO records VALUES(?,?,?,?,?,?,?,?)', (p['participant'], rid, category, metric, event_at, now, body, rev))
                counts['updated' if old else 'inserted'] += 1
            self._purge(c, p['participant'], cfg)
            receipt = self.db.receipt(c, p['participant'], 'health_intake', counts)
        return {**counts, 'receipt_id': receipt, 'received_at': now, 'source': 'health_auto_export'}

    def _purge(self, c, participant, cfg):
        cutoff = (datetime.now(timezone.utc) - timedelta(days=cfg['retention_days'])).isoformat()
        c.execute('DELETE FROM revisions WHERE participant=? AND changed_at<?', (participant, cutoff))
        c.execute('DELETE FROM records WHERE participant=? AND received_at<?', (participant, cutoff))
        c.execute('DELETE FROM entries WHERE participant=? AND updated_at<?', (participant, cutoff))
        c.execute('DELETE FROM receipts WHERE participant=? AND created_at<?', (participant, cutoff))
        c.execute('DELETE FROM outbox WHERE participant=? AND created_at<?', (participant, cutoff))
        # Tasks contain copied evidence/reports and belong to the same retention envelope.
        for row in c.execute('SELECT id,contract FROM tasks WHERE participant=?', (participant,)).fetchall():
            if json.loads(row['contract']).get('created_at', '') < cutoff:
                c.execute('DELETE FROM tasks WHERE participant=? AND id=?', (participant, row['id']))

    def records(self, p, category=None, metric=None, limit=100):
        if p['role'] == 'intake':
            raise Denied('Intake credential is write-only')
        with self.db.connect() as c:
            cfg = self.active(p, c)
            self._purge(c, p['participant'], cfg)
            cats = cfg['role_categories'].get(p['role'], [])
            if category and category not in cats:
                raise Denied('Category not shared with this role')
            if not cats:
                return []
            query = 'SELECT * FROM records WHERE participant=? AND category IN (' + ','.join('?' for _ in cats) + ')'
            params = [p['participant'], *cats]
            if category:
                query += ' AND category=?'
                params.append(category)
            if metric:
                query += ' AND metric=?'
                params.append(metric)
            query += ' ORDER BY received_at DESC,id LIMIT ?'
            params.append(max(1, min(int(limit), 500)))
            return [{**dict(r), 'payload': json.loads(r['payload'])} for r in c.execute(query, params)]

    def status(self, p):
        require_role(p, 'host', 'manager', 'analyst', 'coach', 'companion')
        with self.db.connect() as c:
            cfg = self.active(p, c)
            self._purge(c, p['participant'], cfg)
            cats = cfg['role_categories'].get(p['role'], [])
            rows = c.execute('SELECT category,COUNT(*) AS count,MAX(received_at) AS last_received,MAX(event_at) AS last_event FROM records WHERE participant=? GROUP BY category', (p['participant'],)).fetchall()
            pending = c.execute("SELECT COUNT(*) FROM outbox WHERE participant=? AND status='pending'", (p['participant'],)).fetchone()[0]
        return {'role': p['role'], 'categories': [dict(r) for r in rows if r['category'] in cats],
                'pending_deliveries': pending if p['role'] in ('host', 'manager') else None,
                'host_capabilities': cfg['host_capabilities'] if p['role'] in ('host', 'manager') else {},
                'agents': cfg['native_instances'] if p['role'] in ('host', 'manager') else {},
                'freshness_note': 'last_received is transport time; last_event is observation time. Missing is not zero.'}

    def write_entry(self, p, value):
        require_role(p, 'host', 'manager', 'analyst', 'coach', 'companion')
        self.active(p)
        kind = value.get('kind')
        allowed = {'host': {'meal', 'workout_report', 'emotion', 'context', 'packet'},
                   'manager': {'packet', 'context'}, 'analyst': {'finding'},
                   'coach': {'plan', 'meal', 'workout_report'}, 'companion': {'emotion', 'support'}}
        if kind not in allowed[p['role']]:
            raise Denied('Entry kind unavailable to role')
        eid = value.get('id')
        if not isinstance(eid, str) or not 1 <= len(eid) <= 200:
            raise ValueError('Stable source-message ID required')
        payload = value.get('payload')
        if not isinstance(payload, dict):
            raise ValueError('Entry payload must be an object')
        if kind == 'meal':
            if payload.get('meal') not in ('breakfast', 'lunch', 'dinner', 'snack'):
                raise ValueError('Meal type required')
            if not instant(payload.get('occurred_at')):
                raise ValueError('Meal occurrence needs explicit timezone; ask if unknown')
            if payload.get('source_kind') not in ('self_report', 'photo_estimate', 'label', 'weighed'):
                raise ValueError('Meal provenance required')
            if payload.get('source_kind') == 'photo_estimate' and payload.get('nutrient_certainty') != 'estimate':
                raise ValueError('Photo-derived nutrients must be labelled estimate')
        with self.db.connect() as c:
            old = c.execute('SELECT * FROM entries WHERE participant=? AND id=?', (p['participant'], eid)).fetchone()
            if old and old['actor'] != p['role'] and p['role'] not in ('host', 'manager'):
                raise Denied('Cannot overwrite another role entry')
            now = utcnow()
            if old and old['payload'] != packed(payload):
                rev_id = 'entry:' + eid
                rev = c.execute('SELECT COALESCE(MAX(revision),0)+1 FROM revisions WHERE participant=? AND id=?', (p['participant'], rev_id)).fetchone()[0]
                c.execute('INSERT INTO revisions VALUES(?,?,?,?,?)', (p['participant'], rev_id, rev, old['payload'], now))
            c.execute('INSERT OR REPLACE INTO entries VALUES(?,?,?,?,?,?)', (p['participant'], eid, kind, p['role'], packed(payload), now))
            if kind == 'packet':
                # Fully prepared output, so CoS only needs routing/attention and channel action.
                delivery_id = 'packet:' + eid + ':' + digest(packed(payload))[:12]
                c.execute('INSERT OR IGNORE INTO outbox(participant,id,kind,payload,created_at) VALUES(?,?,?,?,?)',
                          (p['participant'], delivery_id, 'wellbeing_packet', packed(payload), now))
            if kind == 'meal':
                cfg = self.db.config(p['participant'], c)
                local = datetime.fromisoformat(instant(payload['occurred_at'])).astimezone(ZoneInfo(cfg['timezone']))
                reminder_id = f"meal:{local.date()}:{payload['meal']}"
                c.execute("UPDATE outbox SET status='cancelled' WHERE participant=? AND id=? AND status IN ('pending','leased')", (p['participant'], reminder_id))
            receipt = self.db.receipt(c, p['participant'], 'entry', {'id': eid, 'kind': kind, 'actor': p['role']})
        return {'id': eid, 'receipt_id': receipt, 'status': 'stored'}

    def entries(self, p, kind=None):
        self.active(p)
        kinds = {'host': ('meal', 'workout_report', 'context', 'packet', 'plan', 'finding'),
                 'manager': ('meal', 'workout_report', 'context', 'packet', 'plan', 'finding'),
                 'analyst': ('meal', 'workout_report', 'context', 'finding'),
                 'coach': ('meal', 'workout_report', 'context', 'plan'),
                 'companion': ('emotion', 'support')}.get(p['role'], ())
        if kind and kind not in kinds:
            raise Denied('Entry not shared with role')
        with self.db.connect() as c:
            self._purge(c, p['participant'], self.db.config(p['participant'], c))
            rows = c.execute('SELECT * FROM entries WHERE participant=? ORDER BY updated_at DESC LIMIT 500', (p['participant'],)).fetchall()
        return [{**dict(r), 'payload': json.loads(r['payload'])} for r in rows if r['kind'] in kinds and (not kind or r['kind'] == kind)]

    def tick(self, participant, now=None):
        now = now or datetime.now(timezone.utc)
        with self.db.connect() as c:
            cfg = self.db.config(participant, c)
            self._purge(c, participant, cfg)
            if not cfg['enabled'] or not cfg['reminders']['enabled']:
                return []
            local = now.astimezone(ZoneInfo(cfg['timezone']))
            minute = local.hour * 60 + local.minute
            r = cfg['reminders']
            start, end = self._time(r['quiet_start']), self._time(r['quiet_end'])
            quiet = (start <= minute < end) if start < end else (minute >= start or minute < end) if start != end else False
            if quiet:
                return []
            created = []
            for meal, when in r['meals'].items():
                if not 0 <= minute - self._time(when) < r.get('grace_minutes', 120):
                    continue
                eid = f'meal:{local.date()}:{meal}'
                logged = False
                for row in c.execute("SELECT payload FROM entries WHERE participant=? AND kind='meal'", (participant,)):
                    v = json.loads(row[0])
                    at = instant(v.get('occurred_at'))
                    if at and v.get('meal') == meal and datetime.fromisoformat(at).astimezone(ZoneInfo(cfg['timezone'])).date() == local.date():
                        logged = True
                        break
                if logged:
                    continue
                count = c.execute("SELECT COUNT(*) FROM outbox WHERE participant=? AND id LIKE ? AND status!='cancelled'", (participant, f'meal:{local.date()}:%')).fetchone()[0]
                if count >= r.get('daily_budget', 3):
                    break
                fa = {'breakfast': 'صبحانه', 'lunch': 'ناهار', 'dinner': 'شام'}[meal]
                payload = {'text': f'اگر {fa} خوردی، یک عکس یا ویس کوتاه بفرست تا ثبتش کنم؛ اگر نخوردی یا نمی‌خواهی ثبت کنی هم بگو.',
                           'meal': meal, 'expires_at': (now + timedelta(minutes=r.get('grace_minutes', 120) - (minute-self._time(when)))).isoformat(),
                           'delivery': 'host-selected channel; pending until real receipt'}
                cur = c.execute('INSERT OR IGNORE INTO outbox(participant,id,kind,payload,created_at) VALUES(?,?,?,?,?)',
                                (participant, eid, 'meal_reminder', packed(payload), now.isoformat()))
                if cur.rowcount:
                    created.append(eid)
        return created

    def claim_outbox(self, p, now=None):
        require_role(p, 'host')
        self.active(p)
        now = now or datetime.now(timezone.utc)
        with self.db.connect() as c:
            rows = c.execute("SELECT * FROM outbox WHERE participant=? AND (status='pending' OR (status='leased' AND lease_until<?)) ORDER BY created_at LIMIT 20", (p['participant'], now.isoformat())).fetchall()
            result = []
            for row in rows:
                payload = json.loads(row['payload'])
                if payload.get('expires_at') and datetime.fromisoformat(payload['expires_at']) < now:
                    c.execute("UPDATE outbox SET status='expired' WHERE participant=? AND id=?", (p['participant'], row['id']))
                    continue
                claim = secrets.token_urlsafe(24)
                c.execute("UPDATE outbox SET status='leased',lease_until=?,claim_hash=? WHERE participant=? AND id=?", ((now+timedelta(minutes=5)).isoformat(), digest(claim), p['participant'], row['id']))
                result.append({'id': row['id'], 'kind': row['kind'], 'payload': payload, 'claim_token': claim})
            return result

    def acknowledge(self, p, value):
        require_role(p, 'host')
        self.active(p)
        if not value.get('receipt_ref'):
            raise ValueError('Actual host/channel receipt required')
        with self.db.connect() as c:
            row = c.execute('SELECT * FROM outbox WHERE participant=? AND id=?', (p['participant'], value['id'])).fetchone()
            if not row or row['status'] != 'leased' or row['claim_hash'] != digest(value.get('claim_token', '')) or row['lease_until'] < utcnow():
                raise Denied('Invalid or expired delivery lease')
            c.execute("UPDATE outbox SET status='delivered',delivery_receipt=? WHERE participant=? AND id=?", (value['receipt_ref'], p['participant'], value['id']))
        return {'status': 'delivered', 'evidence_kind': 'host_supplied_receipt', 'read_or_acted': 'unknown'}

    def task(self, p, operation, v):
        self.active(p)
        pid = p['participant']
        with self.db.connect() as c:
            if operation == 'create':
                require_role(p, 'host', 'manager')
                if v.get('role') not in ('manager', 'analyst', 'coach', 'companion') or not v.get('id') or not v.get('objective') or not v.get('acceptance'):
                    raise ValueError('Task needs id, role, objective and acceptance')
                # Use record references, never copy all Health data into task contracts.
                for rid in v.get('evidence_ids', []):
                    row = c.execute('SELECT category FROM records WHERE participant=? AND id=?', (pid, rid)).fetchone()
                    cfg = self.db.config(pid, c)
                    if not row or row[0] not in cfg['role_categories'].get(v['role'], []):
                        raise Denied('Task evidence exceeds recipient permission')
                old = c.execute('SELECT contract FROM tasks WHERE participant=? AND id=?', (pid, v['id'])).fetchone()
                if old:
                    prior = json.loads(old[0]); prior.pop('created_at', None)
                    if prior != v:
                        raise ValueError('Task ID already used for different work')
                    return {'id': v['id'], 'status': 'existing'}
                c.execute('INSERT INTO tasks(participant,id,role,status,contract) VALUES(?,?,?,?,?)', (pid, v['id'], v['role'], 'prepared', packed({**v, 'created_at': utcnow()})))
                return {'id': v['id'], 'status': 'prepared', 'dispatched': False}
            if operation == 'claim':
                require_role(p, 'manager', 'analyst', 'coach', 'companion')
                row = c.execute("SELECT * FROM tasks WHERE participant=? AND role=? AND (status='prepared' OR (status='running' AND lease_until<?)) ORDER BY id LIMIT 1", (pid, p['role'], utcnow())).fetchone()
                if not row:
                    return None
                claim = secrets.token_urlsafe(24)
                c.execute("UPDATE tasks SET status='running',claim_hash=?,lease_until=? WHERE participant=? AND id=?", (digest(claim), (datetime.now(timezone.utc)+timedelta(minutes=15)).isoformat(), pid, row['id']))
                return {'id': row['id'], 'contract': json.loads(row['contract']), 'claim_token': claim}
            row = c.execute('SELECT * FROM tasks WHERE participant=? AND id=?', (pid, v['id'])).fetchone()
            if not row:
                raise ValueError('Task not found')
            if operation == 'report':
                if p['role'] != row['role'] or row['status'] != 'running' or row['claim_hash'] != digest(v.get('claim_token', '')) or row['lease_until'] < utcnow():
                    raise Denied('Invalid task role or lease')
                if not isinstance(v.get('result'), str) or not v.get('result') or not isinstance(v.get('uncertainty'), list):
                    raise ValueError('Report requires result and uncertainty array')
                c.execute("UPDATE tasks SET status='report_received',report=? WHERE participant=? AND id=?", (packed(v), pid, v['id']))
                return {'status': 'report_received', 'verified': False}
            require_role(p, 'host', 'manager')
            if operation == 'review':
                if row['status'] != 'report_received' or v.get('decision') not in ('accept', 'revise') or not v.get('reason'):
                    raise ValueError('Review requires report, decision and reason')
                state = 'verified' if v['decision'] == 'accept' else 'prepared'
                c.execute('UPDATE tasks SET status=?,review=? WHERE participant=? AND id=?', (state, packed(v), pid, v['id']))
                return {'status': state}
            if operation == 'close':
                if row['status'] != 'verified':
                    raise ValueError('Only verified tasks can close')
                c.execute("UPDATE tasks SET status='closed' WHERE participant=? AND id=?", (pid, v['id']))
                return {'status': 'closed'}
            raise ValueError('Unknown task operation')

    def packet(self, p):
        require_role(p, 'host', 'manager')
        # Descriptive packet, not an invented personalized coaching recommendation.
        return {'kind': 'wellbeing_section', 'status': self.status(p),
                'entries': self.entries(p, 'packet'), 'observed_records': self.records(p, limit=20),
                'unknowns': ['No diagnosis or causal conclusion follows from these records.',
                             'Delivery, adoption, execution and observed change require separate evidence.'],
                'next_owner': 'manager: prepare concise Persian interpretation for host/newsletter'}

    def delete(self, p):
        require_role(p, 'host')
        with self.db.connect() as c:
            for table in ('records', 'revisions', 'entries', 'tasks', 'outbox', 'receipts', 'pairing'):
                c.execute(f'DELETE FROM {table} WHERE participant=?', (p['participant'],))
            c.execute('UPDATE tokens SET revoked=1 WHERE participant=?', (p['participant'],))
            cfg = self.db.config(p['participant'], c)
            cfg.update(enabled=False, categories=[], role_categories={})
            c.execute('UPDATE participants SET config=? WHERE id=?', (packed(cfg), p['participant']))
        return {'status': 'deleted_and_credentials_revoked', 'limits': 'Logical primary-store deletion; SQLite pages/WAL, backups, host chats and external copies require separate handling.'}
