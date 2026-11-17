"""Host-neutral operations; imported content is evidence, never executable instructions."""
from __future__ import annotations
from datetime import date, datetime, timedelta, timezone
import json
import re
import secrets
from .core import participant_zone
from .database import CATEGORIES, ROLES, Denied, digest, packed, utcnow
from .hae import fallback_identity, health_data
from .iphone import export_links, validate_public_url

READ_KINDS = {
    'host': ('meal', 'workout_report', 'context', 'packet', 'plan', 'finding'),
    'manager': ('meal', 'workout_report', 'context', 'packet', 'plan', 'finding'),
    'analyst': ('meal', 'workout_report', 'context', 'finding'),
    'coach': ('meal', 'workout_report', 'context', 'plan'),
    'companion': ('emotion', 'support'),
}
WRITE_KINDS = {'host': ('meal', 'workout_report', 'emotion', 'context', 'packet'),
               'manager': ('packet', 'context'), 'analyst': ('finding',),
               'coach': ('plan', 'meal', 'workout_report'), 'companion': ('emotion', 'support')}
DERIVED = ('context', 'packet', 'plan', 'finding')


def instant(value):
    if not isinstance(value, str):
        return None
    try:
        # HAE examples use "YYYY-MM-DD HH:MM:SS +HHMM". Remove only
        # whitespace before an explicit offset; never assume a missing zone.
        value = re.sub(r'\s+([+-]\d{2}:?\d{2})$', r'\1', value)
        d = datetime.fromisoformat(value.replace('Z', '+00:00').replace(' ', 'T', 1))
        return d.astimezone(timezone.utc).isoformat() if d.tzinfo and d.utcoffset() is not None else None
    except (ValueError, OverflowError):
        return None


def require_role(p, *roles):
    if not isinstance(p, dict) or p.get('role') not in roles:
        raise Denied('Operation unavailable to this role')


def text(value, limit=2000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError('Nonempty bounded text required')
    return value


def string_list(value, choices=None, limit=100):
    if not isinstance(value, list) or len(value) > limit or any(not isinstance(x, str) for x in value):
        raise ValueError('Expected bounded text array')
    if len(value) != len(set(value)) or (choices is not None and set(value) - set(choices)):
        raise ValueError('Unknown or duplicate array values')
    return value


def meal_day(payload, timezone_name):
    """Validate occurrence precision; return a reminder date or no dated evidence."""
    precision = payload.get('time_precision', 'exact')
    if precision not in ('exact', 'day', 'unknown'):
        raise ValueError('Unknown meal time precision')
    zone_name = payload.get('timezone', timezone_name)
    if not isinstance(zone_name, str):
        raise ValueError('Meal timezone must be text')
    participant_zone(zone_name)
    if precision == 'unknown':
        if 'occurred_at' in payload or 'occurred_date' in payload:
            raise ValueError('Unknown precision cannot carry occurrence date/time')
        return None
    if precision == 'day':
        if 'occurred_at' in payload:
            raise ValueError('Day precision cannot carry a clock time')
        value = payload.get('occurred_date')
        if not isinstance(value, str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', value):
            raise ValueError('Meal date must be YYYY-MM-DD')
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError('Invalid meal date') from exc
    if 'occurred_date' in payload:
        raise ValueError('Exact precision uses occurred_at only')
    at = instant(payload.get('occurred_at'))
    if not at:
        raise ValueError('Exact meal occurrence requires a timezone-bearing timestamp')
    return datetime.fromisoformat(at).astimezone(participant_zone(timezone_name)).date()


class Service:
    def __init__(self, db):
        self.db = db

    def active(self, p, c=None):
        if c is None:
            with self.db.connect() as conn:
                return self.active(p, conn)
        self.db.authorize(p, c)
        cfg = self.db.config(p['participant'], c)
        if not cfg['enabled']:
            raise Denied('Participant service paused')
        return cfg

    @staticmethod
    def _time(value):
        if not isinstance(value, str) or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', value):
            raise ValueError('Time must be HH:MM')
        return int(value[:2]) * 60 + int(value[3:])

    def _validate(self, cfg):
        participant_zone(cfg['timezone'])
        if type(cfg['enabled']) is not bool or type(cfg['retention_days']) is not int or not 1 <= cfg['retention_days'] <= 3650:
            raise ValueError('Invalid enabled/retention setting')
        string_list(cfg['categories'], CATEGORIES)
        if not isinstance(cfg['role_categories'], dict):
            raise ValueError('Role categories must be an object')
        for role, cats in cfg['role_categories'].items():
            if role not in READ_KINDS:
                raise ValueError('Unknown role')
            string_list(cats, cfg['categories'])
        r = cfg['reminders']
        if not isinstance(r, dict) or set(r) - {'enabled', 'meals', 'quiet_start', 'quiet_end', 'daily_budget', 'grace_minutes'}:
            raise ValueError('Invalid reminder fields')
        if type(r.get('enabled')) is not bool or not isinstance(r.get('meals'), dict):
            raise ValueError('Invalid reminders')
        for name, low, high in (('daily_budget', 0, 10), ('grace_minutes', 1, 360)):
            if type(r.get(name)) is not int or not low <= r[name] <= high:
                raise ValueError('Invalid reminder limits')
        for meal, when in r['meals'].items():
            if meal not in ('breakfast', 'lunch', 'dinner'):
                raise ValueError('Unknown meal')
            self._time(when)
        if (r.get('quiet_start') is None) != (r.get('quiet_end') is None):
            raise ValueError('Specify both quiet times or neither')
        if r.get('quiet_start') is not None:
            self._time(r['quiet_start']); self._time(r['quiet_end'])
        for key in ('host_capabilities', 'native_instances', 'opengym'):
            if not isinstance(cfg[key], dict):
                raise ValueError('Expected settings object')
        for name, cap in cfg['host_capabilities'].items():
            text(name, 100)
            if not isinstance(cap, dict) or cap.get('status') not in ('verified', 'unavailable', 'unknown'):
                raise ValueError('Capability requires explicit status')
            if cap['status'] == 'verified':
                text(cap.get('receipt_ref'), 500)
                if not instant(cap.get('checked_at')):
                    raise ValueError('Verified capability requires checked_at')
        for role, instance in cfg['native_instances'].items():
            if role not in ('manager', 'analyst', 'coach', 'companion') or not isinstance(instance, dict):
                raise ValueError('Invalid native instance')
            text(instance.get('instance_id'), 200); text(instance.get('receipt_ref'), 500)
        if set(cfg['opengym']) - {'enabled'} or type(cfg['opengym'].get('enabled')) is not bool:
            raise ValueError('OpenGym secrets/tool mapping belong in private adapter configuration')
        packed(cfg)

    def _invalidate(self, c, pid):
        # Conservative: unstructured derived text cannot safely be field-redacted.
        c.execute("DELETE FROM entries WHERE participant=? AND kind IN ('context','packet','plan','finding')", (pid,))
        c.execute('DELETE FROM tasks WHERE participant=?', (pid,))
        c.execute("UPDATE outbox SET status='cancelled',payload='{}',claim_hash=NULL WHERE participant=? AND kind='wellbeing_packet'", (pid,))
        c.execute('DELETE FROM revisions WHERE participant=? AND id LIKE ?', (pid, 'entry:%'))

    def _apply_config(self, c, pid, cfg, previous, patch):
        self._validate(cfg)
        changed_scope = cfg['categories'] != previous['categories'] or cfg['role_categories'] != previous['role_categories']
        if changed_scope:
            permitted = set(cfg['categories'])
            for row in c.execute('SELECT id,category FROM records WHERE participant=?', (pid,)).fetchall():
                if row['category'] not in permitted:
                    c.execute('DELETE FROM revisions WHERE participant=? AND id=?', (pid, row['id']))
                    c.execute('DELETE FROM records WHERE participant=? AND id=?', (pid, row['id']))
            self._invalidate(c, pid)
        if changed_scope or not cfg['enabled']:
            c.execute('DELETE FROM pairing WHERE participant=?', (pid,))
            c.execute("UPDATE tasks SET status='cancelled',claim_hash=NULL WHERE participant=?", (pid,))
            c.execute("UPDATE outbox SET status='cancelled',claim_hash=NULL WHERE participant=? AND status IN ('pending','leased','uncertain')", (pid,))
        if 'reminders' in patch or 'timezone' in patch:
            c.execute("UPDATE outbox SET status='cancelled',claim_hash=NULL WHERE participant=? AND kind='meal_reminder' AND status IN ('pending','leased')", (pid,))
        c.execute('UPDATE participants SET config=? WHERE id=?', (packed(cfg), pid))
        self._purge(c, pid, cfg)
        self.db.receipt(c, pid, 'configuration', {'changed': sorted(patch)})

    def configure(self, p, patch):
        require_role(p, 'host', 'manager')
        allowed = {'timezone', 'enabled', 'categories', 'role_categories', 'retention_days', 'reminders', 'host_capabilities', 'native_instances', 'opengym'}
        if not isinstance(patch, dict) or set(patch) - allowed:
            raise ValueError('Unknown configuration fields')
        with self.db.connect() as c:
            self.db.authorize(p, c)
            previous = self.db.config(p['participant'], c)
            cfg = json.loads(packed(previous))
            cfg.update(patch)
            if 'reminders' in patch and isinstance(patch['reminders'], dict):
                cfg['reminders'] = {**previous['reminders'], **patch['reminders']}
            self._apply_config(c, p['participant'], cfg, previous, patch)
        return cfg

    def _purge(self, c, pid, cfg):
        cutoff = (datetime.now(timezone.utc) - timedelta(days=cfg['retention_days'])).isoformat()
        removed = c.execute('DELETE FROM records WHERE participant=? AND (received_at<? OR (event_at IS NOT NULL AND event_at<?))', (pid, cutoff, cutoff)).rowcount
        removed += c.execute('DELETE FROM entries WHERE participant=? AND updated_at<?', (pid, cutoff)).rowcount
        c.execute('DELETE FROM revisions WHERE participant=? AND (changed_at<? OR (id NOT LIKE ? AND NOT EXISTS (SELECT 1 FROM records r WHERE r.participant=revisions.participant AND r.id=revisions.id)))', (pid, cutoff, 'entry:%'))
        c.execute('DELETE FROM receipts WHERE participant=? AND created_at<?', (pid, cutoff))
        c.execute('DELETE FROM outbox WHERE participant=? AND created_at<?', (pid, cutoff))
        c.execute('DELETE FROM pairing WHERE participant=? AND (expires_at<? OR used=1)', (pid, utcnow()))
        for row in c.execute('SELECT id,contract FROM tasks WHERE participant=?', (pid,)).fetchall():
            if json.loads(row['contract']).get('created_at', '') < cutoff:
                c.execute('DELETE FROM tasks WHERE participant=? AND id=?', (pid, row['id']))
        if removed:
            self._invalidate(c, pid)

    def ingest(self, p, payload):
        require_role(p, 'intake', 'host')
        data = health_data(payload)
        packed(payload)
        present = set(data)
        counts = dict(inserted=0, updated=0, unchanged=0, unknown_time=0, expired=0)
        with self.db.connect() as c:
            cfg = self.active(p, c); pid = p['participant']
            self._purge(c, pid, cfg)
            if present - set(cfg['categories']):
                raise Denied('Upload contains an unapproved category; no records saved')
            items = []
            for category in sorted(present):
                if not isinstance(data[category], list):
                    raise ValueError('Category must be array')
                for row in data[category]:
                    if not isinstance(row, dict):
                        raise ValueError('Record must be object')
                    if category == 'metrics':
                        name = text(row.get('name'), 200)
                        if not isinstance(row.get('data'), list):
                            raise ValueError('Metric requires sample array')
                        for sample in row['data']:
                            if not isinstance(sample, dict) or set(sample) & {'name', 'units'}:
                                raise ValueError('Invalid metric sample envelope')
                            items.append((category, name, {**sample, 'name': name, 'units': row.get('units')}))
                    else:
                        items.append((category, '', row))
                    if len(items) > 50000:
                        raise ValueError('Too many records; use batching')
            now = utcnow()
            cutoff = (datetime.now(timezone.utc) - timedelta(days=cfg['retention_days'])).isoformat()
            staged = {}
            for category, metric, item in items:
                event = instant(item.get('start') or item.get('startDate') or item.get('date'))
                if event and event < cutoff:
                    counts['expired'] += 1
                    continue
                if not event:
                    counts['unknown_time'] += 1
                identity = item.get('id') or item.get('uuid')
                if identity is not None:
                    text(identity, 500)
                else:
                    identity = fallback_identity(category, item, event)
                rid = digest(packed([category, metric, identity]))
                body = packed(item)
                if rid in staged and staged[rid] != body:
                    raise ValueError('Conflicting samples in one upload; reconcile source')
                staged[rid] = body
                old = c.execute('SELECT payload,revision FROM records WHERE participant=? AND id=?', (pid, rid)).fetchone()
                if old and old['payload'] == body:
                    counts['unchanged'] += 1
                    continue
                revision = old['revision'] + 1 if old else 1
                if old:
                    c.execute('INSERT INTO revisions VALUES(?,?,?,?,?)', (pid, rid, old['revision'], old['payload'], now))
                c.execute('INSERT OR REPLACE INTO records VALUES(?,?,?,?,?,?,?,?)', (pid, rid, category, metric, event, now, body, revision))
                counts['updated' if old else 'inserted'] += 1
            if counts['updated']:
                self._invalidate(c, pid)
            receipt = self.db.receipt(c, pid, 'health_intake', counts)
        return {**counts, 'receipt_id': receipt, 'received_at': now, 'source': 'health_auto_export'}

    def records(self, p, category=None, metric=None, limit=100):
        require_role(p, *READ_KINDS)
        if type(limit) is not int or not 1 <= limit <= 500:
            raise ValueError('limit must be 1..500')
        with self.db.connect() as c:
            cfg = self.active(p, c); self._purge(c, p['participant'], cfg)
            cats = cfg['role_categories'].get(p['role'], [])
            if category and category not in cats:
                raise Denied('Category not shared with role')
            if not cats:
                return []
            query = 'SELECT * FROM records WHERE participant=? AND category IN (' + ','.join('?' for _ in cats) + ')'
            args = [p['participant'], *cats]
            if category:
                query += ' AND category=?'; args.append(category)
            if metric:
                query += ' AND metric=?'; args.append(text(metric, 200))
            query += ' ORDER BY received_at DESC,id LIMIT ?'; args.append(limit)
            return [{**dict(r), 'payload': json.loads(r['payload'])} for r in c.execute(query, args)]

    def status(self, p):
        require_role(p, *READ_KINDS)
        with self.db.connect() as c:
            self.db.authorize(p, c)
            cfg = self.db.config(p['participant'], c); self._purge(c, p['participant'], cfg)
            cats = cfg['role_categories'].get(p['role'], [])
            rows = c.execute('SELECT category,COUNT(*) AS count,MAX(received_at) AS last_received,MAX(event_at) AS last_event FROM records WHERE participant=? GROUP BY category', (p['participant'],)).fetchall()
            deliveries = {r[0]: r[1] for r in c.execute('SELECT status,COUNT(*) FROM outbox WHERE participant=? GROUP BY status', (p['participant'],))}
            last = c.execute("SELECT id,created_at,result FROM receipts WHERE participant=? AND kind='health_intake' ORDER BY created_at DESC LIMIT 1", (p['participant'],)).fetchone()
        supervisory = p['role'] in ('host', 'manager')
        return {'role': p['role'], 'enabled': cfg['enabled'], 'categories': [dict(r) for r in rows if r['category'] in cats],
                'pending_deliveries': deliveries.get('pending', 0) if supervisory else None,
                'delivery_states': deliveries if supervisory else {},
                'last_intake_receipt': {'id': last['id'], 'received_at': last['created_at']} if last and supervisory else None,
                'host_capabilities': cfg['host_capabilities'] if supervisory else {},
                'agents': cfg['native_instances'] if supervisory else {},
                'encryption_at_rest': 'not_provided', 'device_origin_verified': False,
                'freshness_note': 'Transport receipt is not device acceptance. Event time is observation time; missing is not zero.'}

    def write_entry(self, p, value):
        require_role(p, *WRITE_KINDS)
        if not isinstance(value, dict) or set(value) != {'id', 'kind', 'payload'}:
            raise ValueError('Entry requires id,kind,payload')
        eid = text(value['id'], 200); kind = value['kind']; payload = value['payload']
        if kind not in WRITE_KINDS[p['role']]:
            raise Denied('Entry kind unavailable to role')
        if not isinstance(payload, dict):
            raise ValueError('Entry payload must be object')
        body = packed(payload)
        if len(body.encode('utf-8')) > 131072:
            raise ValueError('Entry too large; keep media in authorized private source')
        if kind == 'meal':
            if payload.get('meal') not in ('breakfast', 'lunch', 'dinner', 'snack'):
                raise ValueError('Meal type required')
            if payload.get('source_kind') not in ('self_report', 'photo_estimate', 'label', 'weighed'):
                raise ValueError('Meal provenance required')
            if payload['source_kind'] == 'photo_estimate' and payload.get('nutrient_certainty') != 'estimate':
                raise ValueError('Photo-derived nutrients require estimate label')
            if payload.get('status', 'logged') not in ('logged', 'skipped', 'declined'):
                raise ValueError('Unknown meal status')
            if payload.get('status') in ('skipped', 'declined') and 'nutrients' in payload:
                raise ValueError('Skipped/declined meal is not measured food')
        with self.db.connect() as c:
            cfg = self.active(p, c); pid = p['participant']; self._purge(c, pid, cfg)
            if kind == 'meal':
                payload = dict(payload)
                if payload.get('time_precision') in ('day', 'unknown'):
                    payload.setdefault('timezone', cfg['timezone'])
                day = meal_day(payload, cfg['timezone'])
                body = packed(payload)
            old = c.execute('SELECT * FROM entries WHERE participant=? AND id=?', (pid, eid)).fetchone()
            if old and (old['kind'] != kind or old['actor'] != p['role']):
                raise Denied('Entry identity is bound to its original role and kind')
            if old and old['payload'] == body:
                return {'id': eid, 'status': 'unchanged'}
            now = utcnow()
            if old:
                self._invalidate(c, pid)
                revision_id = 'entry:' + eid
                revision = c.execute('SELECT COALESCE(MAX(revision),0)+1 FROM revisions WHERE participant=? AND id=?', (pid, revision_id)).fetchone()[0]
                c.execute('INSERT INTO revisions VALUES(?,?,?,?,?)', (pid, revision_id, revision, old['payload'], now))
            c.execute('INSERT OR REPLACE INTO entries VALUES(?,?,?,?,?,?)', (pid, eid, kind, p['role'], body, now))
            if kind == 'packet':
                text(payload.get('text'), 20000)
                delivery_id = 'packet:' + eid + ':' + digest(body)[:16]
                # A cancelled historical content ID is never silently reactivated.
                c.execute('INSERT OR IGNORE INTO outbox(participant,id,kind,payload,created_at) VALUES(?,?,?,?,?)', (pid, delivery_id, 'wellbeing_packet', body, now))
            if kind == 'meal' and day is not None:
                reminder = f"meal:{day}:{payload['meal']}"
                c.execute("UPDATE outbox SET status='cancelled',claim_hash=NULL WHERE participant=? AND id=? AND status IN ('pending','leased')", (pid, reminder))
            receipt = self.db.receipt(c, pid, 'entry', {'kind': kind, 'actor': p['role']})
        return {'id': eid, 'receipt_id': receipt, 'status': 'stored'}

    def entries(self, p, kind=None):
        require_role(p, *READ_KINDS)
        kinds = READ_KINDS[p['role']]
        if kind and kind not in kinds:
            raise Denied('Entry not shared with role')
        selected = (kind,) if kind else kinds
        with self.db.connect() as c:
            cfg = self.active(p, c); self._purge(c, p['participant'], cfg)
            query = 'SELECT * FROM entries WHERE participant=? AND kind IN (' + ','.join('?' for _ in selected) + ') ORDER BY updated_at DESC,id LIMIT 500'
            return [{**dict(r), 'payload': json.loads(r['payload'])} for r in c.execute(query, [p['participant'], *selected])]

    def _quiet(self, cfg, now):
        r = cfg['reminders']; minute = now.astimezone(participant_zone(cfg['timezone'])).hour * 60 + now.astimezone(participant_zone(cfg['timezone'])).minute
        if r.get('quiet_start') is None:
            return False
        start, end = self._time(r['quiet_start']), self._time(r['quiet_end'])
        return start <= minute < end if start < end else (minute >= start or minute < end) if start != end else False

    def tick(self, participant, now=None):
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            raise ValueError('Tick requires aware timestamp')
        now = now.astimezone(timezone.utc)
        with self.db.connect() as c:
            cfg = self.db.config(participant, c); self._purge(c, participant, cfg)
            if not cfg['enabled'] or not cfg['reminders']['enabled'] or self._quiet(cfg, now):
                return []
            zone = participant_zone(cfg['timezone']); local = now.astimezone(zone); r = cfg['reminders']; created = []
            for meal, when in sorted(r['meals'].items(), key=lambda item: item[1]):
                hour, minute = map(int, when.split(':'))
                due = local.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if due > local:
                    due -= timedelta(days=1)
                elapsed = (now - due.astimezone(timezone.utc)).total_seconds() / 60
                if not 0 <= elapsed < r['grace_minutes']:
                    continue
                day = due.date(); eid = f'meal:{day}:{meal}'
                logged = False
                for row in c.execute("SELECT payload FROM entries WHERE participant=? AND kind='meal'", (participant,)):
                    v = json.loads(row[0])
                    if v.get('meal') == meal and meal_day(v, cfg['timezone']) == day:
                        logged = True; break
                if logged:
                    continue
                count = c.execute("SELECT COUNT(*) FROM outbox WHERE participant=? AND id LIKE ? AND status!='cancelled'", (participant, f'meal:{day}:%')).fetchone()[0]
                if count >= r['daily_budget']:
                    continue
                fa = {'breakfast': 'صبحانه', 'lunch': 'ناهار', 'dinner': 'شام'}[meal]
                payload = {'text': f'اگر مایلی {fa} را ثبت کنی، عکس، ویس یا متن بفرست؛ رد کردن یا توقف یادآوری هم ممکن است.',
                           'meal': meal, 'expires_at': (due.astimezone(timezone.utc) + timedelta(minutes=r['grace_minutes'])).isoformat(),
                           'delivery': 'pending_real_host_channel'}
                cur = c.execute('INSERT OR IGNORE INTO outbox(participant,id,kind,payload,created_at) VALUES(?,?,?,?,?)', (participant, eid, 'meal_reminder', packed(payload), now.isoformat()))
                if not cur.rowcount:
                    # Only unclaimed cancellations are demonstrably never attempted.
                    cur = c.execute(
                        "UPDATE outbox SET status='pending',payload=?,created_at=? WHERE participant=? AND id=? AND kind='meal_reminder' AND status='cancelled' AND lease_until IS NULL AND claim_hash IS NULL AND delivery_receipt IS NULL",
                        (packed(payload), now.isoformat(), participant, eid))
                if cur.rowcount:
                    created.append(eid)
            return created

    def claim_outbox(self, p, now=None):
        require_role(p, 'host'); now = now or datetime.now(timezone.utc); now = now.astimezone(timezone.utc)
        with self.db.connect() as c:
            cfg = self.active(p, c); pid = p['participant']; self._purge(c, pid, cfg)
            # A lost acknowledgement may follow a successful external send.
            c.execute("UPDATE outbox SET status='uncertain' WHERE participant=? AND status='leased' AND lease_until<=?", (pid, now.isoformat()))
            rows = c.execute("SELECT * FROM outbox WHERE participant=? AND status='pending' ORDER BY created_at,id LIMIT 20", (pid,)).fetchall()
            result = []
            for row in rows:
                payload = json.loads(row['payload'])
                if payload.get('expires_at') and datetime.fromisoformat(payload['expires_at']) <= now:
                    c.execute("UPDATE outbox SET status='expired' WHERE participant=? AND id=?", (pid, row['id'])); continue
                if row['kind'] == 'meal_reminder' and (not cfg['reminders']['enabled'] or self._quiet(cfg, now)):
                    continue
                claim = secrets.token_urlsafe(24); until = (now + timedelta(minutes=5)).isoformat()
                c.execute("UPDATE outbox SET status='leased',lease_until=?,claim_hash=? WHERE participant=? AND id=?", (until, digest(claim), pid, row['id']))
                result.append({'id': row['id'], 'kind': row['kind'], 'payload': payload, 'claim_token': claim, 'lease_until': until, 'idempotency_key': row['id']})
            return result

    def acknowledge(self, p, value):
        require_role(p, 'host')
        if not isinstance(value, dict):
            raise ValueError('Delivery object required')
        receipt = text(value.get('receipt_ref'), 500); key = text(value.get('id'), 500); claim = text(value.get('claim_token'), 200)
        with self.db.connect() as c:
            self.active(p, c)
            row = c.execute('SELECT * FROM outbox WHERE participant=? AND id=?', (p['participant'], key)).fetchone()
            if not row or row['claim_hash'] != digest(claim):
                raise Denied('Invalid delivery claim')
            if row['status'] == 'delivered' and row['delivery_receipt'] == receipt:
                return {'status': 'delivered', 'read_or_acted': 'unknown'}
            if row['status'] not in ('leased', 'uncertain'):
                raise Denied('Delivery cancelled or unavailable')
            c.execute("UPDATE outbox SET status='delivered',delivery_receipt=? WHERE participant=? AND id=?", (receipt, p['participant'], key))
        return {'status': 'delivered', 'evidence_kind': 'host_supplied_receipt', 'read_or_acted': 'unknown'}

    def reconcile_delivery(self, p, value):
        require_role(p, 'host')
        if not isinstance(value, dict) or value.get('outcome') not in ('delivered', 'not_sent', 'unknown'):
            raise ValueError('Reconciliation requires explicit outcome')
        reference = text(value.get('receipt_ref'), 500); eid = text(value.get('id'), 500)
        with self.db.connect() as c:
            self.active(p, c)
            row = c.execute('SELECT * FROM outbox WHERE participant=? AND id=?', (p['participant'], eid)).fetchone()
            if not row or row['status'] not in ('leased', 'uncertain'):
                raise Denied('No unresolved delivery')
            state = {'delivered': 'delivered', 'not_sent': 'pending', 'unknown': 'uncertain'}[value['outcome']]
            payload = json.loads(row['payload'])
            if state == 'pending' and payload.get('expires_at') and payload['expires_at'] <= utcnow():
                state = 'expired'
            c.execute('UPDATE outbox SET status=?,claim_hash=NULL,lease_until=NULL,delivery_receipt=? WHERE participant=? AND id=?', (state, reference, p['participant'], eid))
            self.db.receipt(c, p['participant'], 'delivery_reconciliation', {'outcome': value['outcome'], 'receipt_ref': reference})
        return {'status': state, 'read_or_acted': 'unknown'}

    def tasks(self, p):
        require_role(p, *READ_KINDS)
        with self.db.connect() as c:
            cfg = self.active(p, c); self._purge(c, p['participant'], cfg)
            rows = c.execute('SELECT id,role,status FROM tasks WHERE participant=? ORDER BY id', (p['participant'],))
            return [dict(r) for r in rows if p['role'] in ('host', 'manager', r['role'])]

    def task(self, p, operation, v):
        if not isinstance(v, dict):
            raise ValueError('Task object required')
        with self.db.connect() as c:
            cfg = self.active(p, c); pid = p['participant']; self._purge(c, pid, cfg)
            if operation == 'create':
                require_role(p, 'host', 'manager')
                if set(v) - {'id', 'role', 'objective', 'acceptance', 'evidence_ids'} or v.get('role') not in ('manager', 'analyst', 'coach', 'companion'):
                    raise ValueError('Invalid bounded task')
                text(v.get('id'), 200); text(v.get('objective'), 4000)
                string_list(v.get('acceptance')); string_list(v.get('evidence_ids', []))
                if not v['acceptance'] or any(not x.strip() for x in v['acceptance']):
                    raise ValueError('Acceptance conditions required')
                for rid in v.get('evidence_ids', []):
                    row = c.execute('SELECT category FROM records WHERE participant=? AND id=?', (pid, rid)).fetchone()
                    if not row or any(row[0] not in cfg['role_categories'].get(role, []) for role in (p['role'], v['role'])):
                        raise Denied('Task evidence exceeds sender or recipient scope')
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
                contract = json.loads(row['contract']); evidence = []
                for rid in contract.get('evidence_ids', []):
                    record = c.execute('SELECT * FROM records WHERE participant=? AND id=?', (pid, rid)).fetchone()
                    if not record or record['category'] not in cfg['role_categories'].get(p['role'], []):
                        raise Denied('Task evidence no longer authorized')
                    evidence.append({**dict(record), 'payload': json.loads(record['payload'])})
                claim = secrets.token_urlsafe(24)
                c.execute("UPDATE tasks SET status='running',report=NULL,review=NULL,claim_hash=?,lease_until=? WHERE participant=? AND id=?", (digest(claim), (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(), pid, row['id']))
                return {'id': row['id'], 'contract': contract, 'evidence': evidence, 'claim_token': claim, 'execution': 'host_required_not_spawned'}
            key = text(v.get('id'), 200)
            row = c.execute('SELECT * FROM tasks WHERE participant=? AND id=?', (pid, key)).fetchone()
            if not row:
                raise ValueError('Task not found')
            if operation == 'get':
                if p['role'] not in ('host', 'manager', row['role']):
                    raise Denied('Task unavailable to role')
                return {k: json.loads(row[k]) if row[k] else None for k in ('contract', 'report', 'review')} | {'id': key, 'status': row['status']}
            if operation == 'report':
                if p['role'] != row['role'] or row['status'] != 'running' or row['claim_hash'] != digest(v.get('claim_token', '')) or row['lease_until'] < utcnow():
                    raise Denied('Invalid task role or lease')
                text(v.get('result'), 20000); string_list(v.get('uncertainty'))
                report = {k: val for k, val in v.items() if k in ('id', 'result', 'uncertainty')}
                c.execute("UPDATE tasks SET status='report_received',report=?,claim_hash=NULL WHERE participant=? AND id=?", (packed(report), pid, key))
                return {'status': 'report_received', 'verified': False}
            require_role(p, 'host', 'manager')
            if operation == 'review':
                if row['status'] != 'report_received' or v.get('decision') not in ('accept', 'revise'):
                    raise ValueError('Review requires report and decision')
                if p['role'] == row['role']:
                    raise Denied('A different responsibility must review the report')
                text(v.get('reason'), 4000)
                state = 'verified' if v['decision'] == 'accept' else 'prepared'
                c.execute('UPDATE tasks SET status=?,review=? WHERE participant=? AND id=?', (state, packed(v), pid, key))
                return {'status': state}
            if operation == 'close':
                if row['status'] != 'verified':
                    raise ValueError('Only verified tasks can close')
                c.execute("UPDATE tasks SET status='closed' WHERE participant=? AND id=?", (pid, key))
                return {'status': 'closed', 'user_delivery': 'not_implied'}
            raise ValueError('Unknown task operation')

    def packet(self, p):
        require_role(p, 'host', 'manager')
        return {'kind': 'wellbeing_section', 'status': self.status(p), 'entries': self.entries(p, 'packet'),
                'observed_records': self.records(p, limit=20),
                'unknowns': ['No diagnosis or causal conclusion is inferred.', 'Delivery, implementation and observed outcome require separate evidence.'],
                'next_owner': 'manager: prepare concise Persian section for host'}

    def create_pairing(self, p, public_url):
        require_role(p, 'host', 'manager'); base = validate_public_url(public_url)
        nonce = secrets.token_urlsafe(32); expiry = (datetime.now(timezone.utc) + timedelta(minutes=20)).isoformat()
        with self.db.connect() as c:
            self.active(p, c)
            c.execute('DELETE FROM pairing WHERE participant=?', (p['participant'],))
            c.execute('INSERT INTO pairing VALUES(?,?,?,0)', (digest(nonce), p['participant'], expiry))
        return {'setup_url': base + '/pair/' + nonce, 'expires_at': expiry, 'note': 'Private single-use link; not a device connection receipt'}

    def _pair(self, c, nonce):
        text(nonce, 200)
        row = c.execute('SELECT * FROM pairing WHERE hash=? AND used=0 AND expires_at>?', (digest(nonce), utcnow())).fetchone()
        if not row or not self.db.config(row['participant'], c)['enabled']:
            raise Denied('Pairing expired, used or paused')
        return row

    def pairing_options(self, nonce):
        with self.db.connect() as c:
            row = self._pair(c, nonce); cfg = self.db.config(row['participant'], c)
            return {k: cfg[k] for k in ('categories', 'role_categories', 'retention_days')}

    def confirm_pairing(self, nonce, public_url, categories, recipients, retention_days, all_metrics=False):
        base = validate_public_url(public_url); string_list(categories, CATEGORIES); string_list(recipients, READ_KINDS)
        if not categories or type(all_metrics) is not bool:
            raise ValueError('Explicit category selection required')
        # Build links before committing single-use credential rotation.
        token = secrets.token_urlsafe(32); links = export_links(base, token, categories, all_metrics)
        with self.db.connect() as c:
            row = self._pair(c, nonce); pid = row['participant']; previous = self.db.config(pid, c)
            cfg = json.loads(packed(previous)); cfg.update(categories=categories, retention_days=retention_days)
            cfg['role_categories'] = {role: (['stateOfMind'] if role == 'companion' and 'stateOfMind' in categories else [] if role == 'companion' else list(categories)) if role in recipients else [] for role in READ_KINDS}
            self._apply_config(c, pid, cfg, previous, {'categories': categories, 'role_categories': cfg['role_categories'], 'retention_days': retention_days})
            c.execute("UPDATE tokens SET revoked=1 WHERE participant=? AND role='intake'", (pid,))
            c.execute("INSERT INTO tokens(hash,participant,role) VALUES(?,?,'intake')", (digest(token), pid))
            c.execute('DELETE FROM pairing WHERE participant=?', (pid,))
            self.db.receipt(c, pid, 'device_scope_selected', {'categories': categories, 'recipients': recipients, 'retention_days': retention_days, 'all_metrics': all_metrics})
        return links

    def delete(self, p):
        require_role(p, 'host')
        with self.db.connect() as c:
            self.db.authorize(p, c)
            for table in ('records', 'revisions', 'entries', 'tasks', 'outbox', 'receipts', 'pairing'):
                c.execute(f'DELETE FROM {table} WHERE participant=?', (p['participant'],))
            c.execute('UPDATE tokens SET revoked=1 WHERE participant=?', (p['participant'],))
            cfg = self.db.config(p['participant'], c); cfg.update(enabled=False, categories=[], role_categories={}, host_capabilities={}, native_instances={}, opengym={'enabled': False})
            c.execute('UPDATE participants SET config=? WHERE id=?', (packed(cfg), p['participant']))
        return {'status': 'deleted_and_credentials_revoked', 'limits': 'Logical primary-store deletion; backups, SQLite files, host chats and external copies need separate handling.'}
