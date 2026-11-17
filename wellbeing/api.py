"""Authenticated API + protected iPhone pairing. Run behind a trusted HTTPS proxy."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import html
import json
import os
import secrets
from urllib.parse import parse_qs

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from .database import CATEGORIES, Database, Denied, digest, packed, utcnow
from .iphone import export_links, validate_public_url
from .service import Service, require_role


def create_app(home=None, public_url=None, scheduler=True):
    db = Database(home)
    service = Service(db)
    base = public_url or os.environ.get('WELLBEING_PUBLIC_URL', '')

    async def ticker():
        while True:
            try:
                with db.connect() as c:
                    participants = [r[0] for r in c.execute('SELECT id FROM participants')]
                for participant in participants:
                    await asyncio.to_thread(service.tick, participant)
            except Exception:
                # No payloads in logs. Status/doctor must surface scheduler failure.
                app.state.scheduler_error = 'scheduler_failed'
            await asyncio.sleep(60)

    @asynccontextmanager
    async def lifespan(app):
        task = asyncio.create_task(ticker()) if scheduler else None
        yield
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    app = FastAPI(title='Wellbeing MVP tools', version='0.2.0', lifespan=lifespan)
    app.state.db, app.state.service = db, service
    app.state.scheduler_error = None

    @app.middleware('http')
    async def guard(request, call_next):
        # Bound streamed as well as Content-Length requests, before JSON decoding.
        max_size = 8 * 1024 * 1024
        try:
            if int(request.headers.get('content-length', '0')) > max_size:
                return JSONResponse({'error': 'Payload too large; enable batching'}, 413)
        except ValueError:
            return JSONResponse({'error': 'Invalid Content-Length'}, 400)
        if request.method == 'POST':
            data = bytearray()
            async for part in request.stream():
                data.extend(part)
                if len(data) > max_size:
                    return JSONResponse({'error': 'Payload too large; enable batching'}, 413)
            request._body = bytes(data)
        try:
            response = await call_next(request)
        except (ValueError, KeyError, TypeError):
            return JSONResponse({'error': 'Malformed input; inspect schema'}, 422)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Content-Security-Policy'] = "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'"
        return response

    @app.exception_handler(Denied)
    async def denied(request, exc):
        return JSONResponse({'error': str(exc)}, 403)

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        return JSONResponse({'error': str(exc)}, 422)

    def auth(request):
        value = request.headers.get('authorization', '')
        if not value.startswith('Bearer '):
            raise Denied('Bearer credential required')
        return db.principal(value[7:])

    @app.get('/healthz')
    def healthz():
        return {'service': 'wellbeing-mvp', 'version': '0.2.0', 'ok': True,
                'scheduler_error': app.state.scheduler_error}

    @app.get('/v1/status')
    def status(request: Request):
        return service.status(auth(request))

    @app.get('/v1/config')
    def config(request: Request):
        p = auth(request); require_role(p, 'host', 'manager')
        return db.config(p['participant'])

    @app.post('/v1/config')
    def configure(request: Request, body: dict):
        return service.configure(auth(request), body)

    @app.post('/v1/intake/health')
    def intake(request: Request, body: dict):
        return service.ingest(auth(request), body)

    @app.get('/v1/records')
    def records(request: Request, category: str | None = None, metric: str | None = None, limit: int = 100):
        return service.records(auth(request), category, metric, limit)

    @app.get('/v1/entries')
    def entries(request: Request, kind: str | None = None):
        return service.entries(auth(request), kind)

    @app.post('/v1/entries')
    def entry(request: Request, body: dict):
        return service.write_entry(auth(request), body)

    @app.get('/v1/packet')
    def packet(request: Request):
        return service.packet(auth(request))

    @app.post('/v1/tasks/{operation}')
    def task(request: Request, operation: str, body: dict):
        return service.task(auth(request), operation, body)

    @app.get('/v1/tasks')
    def tasks(request: Request):
        p = auth(request); service.active(p)
        with db.connect() as c:
            rows = c.execute('SELECT id,role,status FROM tasks WHERE participant=?', (p['participant'],))
            return [dict(r) for r in rows if p['role'] in ('host', 'manager', r['role'])]

    @app.post('/v1/outbox/claim')
    def claim(request: Request):
        p = auth(request); require_role(p, 'host')
        service.tick(p['participant'])
        return service.claim_outbox(p)

    @app.post('/v1/outbox/ack')
    def ack(request: Request, body: dict):
        return service.acknowledge(auth(request), body)

    @app.post('/v1/privacy/delete')
    def delete(request: Request, body: dict):
        if body.get('confirm') != 'delete_private_runtime_records':
            raise ValueError('Explicit deletion confirmation required')
        return service.delete(auth(request))

    @app.post('/v1/pairing')
    def pairing(request: Request):
        p = auth(request); require_role(p, 'host', 'manager'); service.active(p)
        validate_public_url(base)
        nonce = secrets.token_urlsafe(32)
        expiry = (datetime.now(timezone.utc) + timedelta(minutes=20)).isoformat()
        with db.connect() as c:
            c.execute('DELETE FROM pairing WHERE expires_at<? OR used=1', (utcnow(),))
            c.execute('INSERT INTO pairing VALUES(?,?,?,0)', (digest(nonce), p['participant'], expiry))
        return {'setup_url': base + '/pair/' + nonce, 'expires_at': expiry,
                'note': 'Private, single-use setup link. Do not publish or forward.'}

    def get_pair(nonce, c):
        row = c.execute('SELECT * FROM pairing WHERE hash=? AND used=0 AND expires_at>?', (digest(nonce), utcnow())).fetchone()
        if not row:
            raise Denied('Pairing link expired or used; ask host for a new one')
        return row

    @app.get('/pair/{nonce}', response_class=HTMLResponse)
    def pair_page(nonce: str):
        with db.connect() as c:
            get_pair(nonce, c)
        checks = ''.join(f'<label><input type="checkbox" name="category" value="{cat}" {"checked" if cat in ("metrics", "workouts") else ""}> {cat}</label><br>' for cat in CATEGORIES)
        return page('اتصال داده‌های آیفون', '<p>Health Auto Export را از اپ‌استور نصب کن و Premium/آزمایش آن را فعال کن. داده‌ها مستقیم به سرور انتخابی خودت می‌روند.</p>'
                    '<p>دسته‌های مجاز را انتخاب کن. در مرحلهٔ بعد دسترسی Apple Health و فعال‌سازی خروجی‌ها را خودت تأیید می‌کنی.</p>'
                    f'<form method="post">{checks}<p><label><input type="checkbox" name="all_metrics" value="yes"> همهٔ سنجه‌های موجود Health؛ در غیر این صورت مجموعهٔ پایهٔ خواب، فعالیت، ضربان و وزن</label></p>'
                    '<p>نگهداری اولیه ۳۰ روز؛ قابل تغییر از دستیار. میزبان، مدیر، تحلیلگر و مربی به دسته‌های انتخابی دسترسی خواهند داشت. همراه هیجانی فقط به State of Mind در صورت انتخاب آن دسترسی دارد.</p>'
                    '<label><input type="checkbox" name="consent" value="yes" required> این دسترسی و نگهداری را انتخاب می‌کنم.</label><p><button>ساخت اتصال‌ها</button></p></form>')

    @app.post('/pair/{nonce}', response_class=HTMLResponse)
    async def pair_confirm(nonce: str, request: Request):
        origin = request.headers.get('origin')
        if origin and origin.rstrip('/') != base.rstrip('/'):
            raise Denied('Unexpected setup origin')
        form = parse_qs((await request.body()).decode('utf-8'))
        if form.get('consent') != ['yes']:
            raise ValueError('Participant selection required')
        cats = form.get('category', [])
        if not cats or set(cats) - set(CATEGORIES):
            raise ValueError('Choose at least one valid category')
        with db.connect() as c:
            row = get_pair(nonce, c)
            pid = row['participant']
            cfg = db.config(pid, c)
            if not cfg['enabled']:
                raise Denied('Service paused')
            cfg.update(categories=cats, role_categories={r: cats for r in ('host', 'manager', 'analyst', 'coach')})
            cfg['role_categories']['companion'] = ['stateOfMind'] if 'stateOfMind' in cats else []
            c.execute('UPDATE participants SET config=? WHERE id=?', (packed(cfg), pid))
            # New iPhone pairing invalidates old intake credentials, never role credentials.
            c.execute("UPDATE tokens SET revoked=1 WHERE participant=? AND role='intake'", (pid,))
            token = secrets.token_urlsafe(32)
            c.execute("INSERT INTO tokens(hash,participant,role) VALUES(?,?,'intake')", (digest(token), pid))
            c.execute('UPDATE pairing SET used=1 WHERE hash=?', (digest(nonce),))
            db.receipt(c, pid, 'device_scope_selected', {'categories': cats, 'all_metrics': form.get('all_metrics') == ['yes']})
        links = export_links(base, token, cats, form.get('all_metrics') == ['yes'])
        buttons = ''.join(f'<p><a href="{html.escape(link, quote=True)}">تنظیم {html.escape(cat)}</a></p>' for cat, link in links.items())
        return page('تنظیم خروجی‌ها', '<p>هر دکمه یک خروجی می‌سازد. در اپ مرورش کن، مجوز Health را بده و Enabled را روشن کن. سپس یک Manual Upload انجام بده.</p>' + buttons +
                    '<p>هنوز دریافت داده تأیید نشده است؛ دستیار پس از دیدن رسید واقعی خبر می‌دهد. اگر این صفحه بسته شد، لینک تازه بگیر.</p>')

    return app


def page(title, body):
    return '<!doctype html><html lang="fa" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + title + '</title><style>body{font:18px system-ui;line-height:1.9;max-width:640px;margin:40px auto;padding:20px;color:#172522;background:#f5f8f6}button,a{font:inherit;padding:12px;color:#075d49}input{width:20px;height:20px}label{display:inline-block;margin:6px}</style><h1>' + title + '</h1>' + body + '</html>'


def main():
    import uvicorn
    uvicorn.run(create_app(), host=os.environ.get('WELLBEING_BIND', '127.0.0.1'),
                port=int(os.environ.get('PORT', '8787')), access_log=False)


if __name__ == '__main__':
    main()
