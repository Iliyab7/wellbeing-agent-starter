"""Authenticated REST tools and private iPhone setup; proxy must preserve HTTPS."""
from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
import html
import json
import os
from urllib.parse import parse_qs, urlsplit
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from .database import CATEGORIES, Database, Denied, utcnow
from .iphone import validate_public_url
from .service import Service, require_role, READ_KINDS


def page(title, body):
    return '<!doctype html><html lang="fa" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + html.escape(title) + '</title><style>body{font:18px system-ui;line-height:1.9;max-width:680px;margin:32px auto;padding:20px}label{display:block;margin:8px}button,a{font:inherit;padding:10px}</style><h1>' + html.escape(title) + '</h1>' + body + '</html>'


def strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    def reject(value):
        raise ValueError('Nonfinite JSON')
    return json.loads(raw, object_pairs_hook=unique, parse_constant=reject)


def create_app(home=None, public_url=None, scheduler=True):
    db = Database(home); service = Service(db)
    configured = public_url if public_url is not None else os.environ.get('WELLBEING_PUBLIC_URL', '')
    base = validate_public_url(configured) if configured else ''

    async def ticker():
        while True:
            try:
                with db.connect() as c:
                    participants = [r[0] for r in c.execute('SELECT id FROM participants')]
                for participant in participants:
                    await asyncio.to_thread(service.tick, participant)
                app.state.scheduler_error = None
                app.state.scheduler_last_tick = utcnow()
            except Exception:
                app.state.scheduler_error = 'queue_producer_failed'
            await asyncio.sleep(60)

    @asynccontextmanager
    async def lifespan(app):
        task = asyncio.create_task(ticker()) if scheduler else None
        try:
            yield
        finally:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    app = FastAPI(title='Wellbeing MVP tools', version='0.2.0', lifespan=lifespan)
    app.state.db = db; app.state.service = service
    app.state.scheduler_error = None; app.state.scheduler_last_tick = None

    def headers(response):
        response.headers.update({'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer',
            'X-Content-Type-Options': 'nosniff',
            'Content-Security-Policy': "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'"})
        return response

    @app.middleware('http')
    async def guard(request, call_next):
        maximum = 8 * 1024 * 1024
        try:
            length = int(request.headers.get('content-length', '0'))
            if length < 0:
                raise ValueError()
        except ValueError:
            return headers(JSONResponse({'error': 'Invalid Content-Length'}, 400))
        if length > maximum:
            return headers(JSONResponse({'error': 'Payload too large; use batching'}, 413))
        try:
            if request.method in ('POST', 'PUT', 'PATCH'):
                body = bytearray()
                async for chunk in request.stream():
                    if len(body) + len(chunk) > maximum:
                        return headers(JSONResponse({'error': 'Payload too large; use batching'}, 413))
                    body.extend(chunk)
                request._body = bytes(body)
                if body and 'application/json' in request.headers.get('content-type', ''):
                    strict_json(bytes(body))
            response = await call_next(request)
        except Denied:
            response = JSONResponse({'error': 'Operation denied'}, 403)
        except (ValueError, KeyError, TypeError, OverflowError):
            response = JSONResponse({'error': 'Malformed input; inspect operation schema'}, 422)
        return headers(response)

    @app.exception_handler(Denied)
    async def denied(request, exc):
        return JSONResponse({'error': 'Operation denied'}, 403)

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        return JSONResponse({'error': 'Invalid operation input'}, 422)

    @app.exception_handler(RequestValidationError)
    async def validation(request, exc):
        # FastAPI's default error detail can echo private input.
        return JSONResponse({'error': 'Request does not match operation schema'}, 422)

    def auth(request):
        value = request.headers.get('authorization', '')
        if not value.startswith('Bearer '):
            raise Denied('Bearer credential required')
        return db.principal(value[7:])

    @app.get('/healthz')
    def healthz():
        with db.connect() as c:
            c.execute('SELECT 1').fetchone()
        return {'service': 'wellbeing-mvp', 'version': '0.2.0', 'ok': app.state.scheduler_error is None,
                'queue_producer': {'enabled': scheduler, 'last_tick': app.state.scheduler_last_tick, 'error': app.state.scheduler_error},
                'channel_delivery': 'external_host_required'}

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

    @app.get('/v1/tasks')
    def tasks(request: Request):
        return service.tasks(auth(request))

    @app.post('/v1/tasks/{operation}')
    def task(request: Request, operation: str, body: dict):
        return service.task(auth(request), operation, body)

    @app.post('/v1/outbox/claim')
    def claim(request: Request):
        p = auth(request); require_role(p, 'host'); service.active(p)
        service.tick(p['participant'])
        return service.claim_outbox(p)

    @app.post('/v1/outbox/ack')
    def acknowledge(request: Request, body: dict):
        return service.acknowledge(auth(request), body)

    @app.post('/v1/outbox/reconcile')
    def reconcile(request: Request, body: dict):
        return service.reconcile_delivery(auth(request), body)

    @app.post('/v1/privacy/delete')
    def delete(request: Request, body: dict):
        if body.get('confirm') != 'delete_private_runtime_records':
            raise ValueError('Explicit deletion confirmation required')
        return service.delete(auth(request))

    @app.post('/v1/pairing')
    def pairing(request: Request):
        return service.create_pairing(auth(request), base)

    @app.get('/pair/{nonce}', response_class=HTMLResponse)
    def pairing_page(nonce: str):
        cfg = service.pairing_options(nonce)
        categories = ''.join('<label><input type="checkbox" name="category" value="' + cat + '"' + (' checked' if cat in cfg['categories'] else '') + '> ' + cat + '</label>' for cat in CATEGORIES)
        recipients = ''.join('<label><input type="checkbox" name="recipient" value="' + role + '"' + (' checked' if cfg['role_categories'].get(role) else '') + '> ' + role + '</label>' for role in READ_KINDS)
        return page('اتصال آیفون', '<p>Health Auto Export را روی آیفون نصب کن؛ انتخاب خرید یا آزمایش Premium و مجوزهای Apple Health با توست. داده‌ها در حافظهٔ خصوصی سرور ذخیره می‌شوند؛ رمزگذاری دیسک را میزبان فراهم می‌کند.</p>'
            '<form method="post"><fieldset><legend>دسته‌های داده</legend>' + categories + '</fieldset><fieldset><legend>گیرندگان مجاز؛ همراه فقط State of Mind</legend>' + recipients + '</fieldset>'
            '<label><input type="checkbox" name="all_metrics" value="yes"> همهٔ سنجه‌ها؛ در غیر این صورت مجموعهٔ پایهٔ خواب، فعالیت، ضربان و وزن</label>'
            '<label>روزهای نگهداری <input type="number" min="1" max="3650" name="retention_days" value="' + str(cfg['retention_days']) + '" required></label>'
            '<p>فرکانس پس‌زمینه را iOS تعیین می‌کند. دسترسی دسته‌ها در سرور اعمال می‌شود؛ انتخاب سنجه‌های خروجی را در اپ هم بررسی کن. میزبان مشترک ممکن است محتوای گفت‌وگو را ببیند.</p>'
            '<label><input type="checkbox" name="consent" value="yes" required> این محدوده، گیرندگان و نگهداری را انتخاب می‌کنم.</label><button>ساخت اتصال‌ها</button></form>')

    @app.post('/pair/{nonce}', response_class=HTMLResponse)
    async def pairing_confirm(nonce: str, request: Request):
        origin = request.headers.get('origin')
        parsed = urlsplit(base)
        expected_origin = parsed.scheme + '://' + parsed.netloc
        if origin and origin.rstrip('/') != expected_origin:
            raise Denied('Unexpected origin')
        if request.headers.get('sec-fetch-site') == 'cross-site':
            raise Denied('Cross-site setup denied')
        form = parse_qs((await request.body()).decode('utf-8'), max_num_fields=40)
        if set(form) - {'category', 'recipient', 'retention_days', 'all_metrics', 'consent'} or form.get('consent') != ['yes']:
            raise ValueError('Explicit participant selection required')
        options = service.pairing_options(nonce)
        days = form.get('retention_days', [str(options['retention_days'])])
        if len(days) != 1:
            raise ValueError('One retention value required')
        recipients = form.get('recipient', [role for role, cats in options['role_categories'].items() if cats])
        links = service.confirm_pairing(nonce, base, form.get('category', []), recipients, int(days[0]), form.get('all_metrics') == ['yes'])
        buttons = ''.join('<p><a href="' + html.escape(link, quote=True) + '">تنظیم ' + html.escape(cat) + '</a></p>' for cat, link in links.items())
        return page('تنظیم خروجی‌ها', '<p>هر خروجی را در اپ بررسی کن، مجوز بده و Enabled را روشن کن. سپس Manual Upload انجام بده. این صفحه حاوی کلید خصوصی است؛ آن را به اشتراک نگذار.</p>' + buttons + '<p>دریافت واقعی داده هنوز تأیید نشده است.</p>')

    @app.post('/v1/opengym/{operation}')
    async def opengym(request: Request, operation: str, body: dict):
        from .opengym import OpenGym
        p = auth(request); require_role(p, 'host', 'manager', 'analyst', 'coach')
        cfg = service.active(p)
        if not cfg['opengym']['enabled']:
            return {'status': 'not_configured'}
        return await OpenGym.from_environment(db.home).run(operation, body)

    return app


def main():
    import uvicorn
    uvicorn.run(create_app(), host=os.environ.get('WELLBEING_BIND', '127.0.0.1'),
                port=int(os.environ.get('PORT', '8787')), access_log=False, proxy_headers=False)


if __name__ == '__main__':
    main()
