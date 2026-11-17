# استقرار و بازیابی MVP

این راهنما و [Caddy template](../../templates/Caddyfile.example) اجرا یا استقرار تأییدشده نیستند. میزبان واقعی هنوز یک gate مربوط به مالک/حساب/دسترسی است. هیچ منبع پولی یا دامنه‌ای با این بسته ایجاد نمی‌شود.

## ترتیب تصمیم پیشنهادی

1. ابتدا رایانه یا سرویس همیشه‌روشنِ صریحاً مجازِ موجود را پیدا کنید؛ private storage، مالک عملیاتی، restart و دسترسی executor را بررسی کنید.
2. همان محیط را با proxy یا tunnel HTTPS پایدار و حساب واقعاً در دسترس وصل کنید. URL باید از آیفون قابل‌دسترسی و هویت TLS معتبر باشد. cloud task دات را دارای inbound port دائمی فرض نکنید. تونل نیز مجوز، پایداری و سیاست نگهداری خودش را دارد.
3. اگر این مسیر موجود نیست، مانع و کوچک‌ترین تصمیم لازم دربارهٔ محیط را برگردانید. تهیهٔ hosting پولی تازه فقط با اختیار مربوط انجام شود؛ قیمت یا deployment اختراع نشود.

لپ‌تاپ خاموش، اتصال قطع، اپ لازم بسته یا پایان job می‌تواند intake/اجرای میزبان را متوقف کند. «همیشه روشن» باید با restart و غیبت کاربر سنجیده شود. تولید صف داخل API جای job واقعی Dot یا اتصال WhatsApp نیست.

## سرویس Python پیشنهادی

از root و Python دارای وابستگی‌های pinشده:

```text
python scripts/bootstrap.py --install --home <PRIVATE_HOME> --public-url https://<APPROVED_HOST>
```

سپس با Python همان `runtime-venv`، محیط خصوصی `WELLBEING_MVP_HOME` و `WELLBEING_PUBLIC_URL` را تنظیم و `python scripts/run_server.py` را زیر supervisor موجود اجرا کنید. bind پیش‌فرض `127.0.0.1:8787` است؛ پشت proxy حفظ شود. در Windows از supervisor مجاز موجود و ACL همان حساب استفاده کنید. در Linux نیز سرویس اختصاصی کم‌اختیار و سیاست restart لازم است؛ این راهنما ثبت چنین سرویسی را ادعا نمی‌کند.

Caddy روی همان ماشین می‌تواند HTTPS را به loopback بدهد. نام واقعی دامنه، DNS، دسترسی certificate و firewall باید بررسی شوند. نمونهٔ فایل access log را فعال نمی‌کند؛ pairing URL و deep link کلید دارند و نباید در proxy/tunnel/analytics ثبت شوند. مسیر پایهٔ پیشنهادی origin بدون prefix است؛ route prefix نیازمند تنظیم و آزمون جداست. `/healthz` فقط سلامت فرایند/DB/producer را نشان می‌دهد، نه سلامت گوشی یا ارسال.

## Docker اختیاری

از `compose.yaml` موجود، `WELLBEING_PUBLIC_URL` را در محیط خصوصی تنظیم کنید. initialization و اجرای زیر با همان URL انجام شوند:

```text
docker compose build
docker compose run --rm wellbeing python scripts/bootstrap.py --home /state --public-url https://<APPROVED_HOST>
docker compose up -d
docker compose ps
```

volume خصوصی، UID/GID 10001، bind loopback و proxy لازم‌اند. Docker image/Compose در شواهد تأمین‌شده آزموده نشده‌اند. اجرای کانتینر مستقل از نصب ابزار روی Dot است؛ credential خصوصی باید از مسیر مجاز به executor برسد، نه داخل compose عمومی. فایل‌سیستم read-only جای رمزگذاری volume را نمی‌گیرد.

## نسخهٔ پشتیبان سازگار با SQLite

مالک باید مقصد خصوصیِ محافظت‌شده، زمان نگهداری و اختیار backup را مشخص کند. SQLite این MVP رمزگذاری داخلی ندارد؛ disk/volume encryption و ACL مسئولیت محیط‌اند. backup هم حاوی دادهٔ سلامت است. نمونهٔ زیر فقط دستور پیشنهادی است و اجرا نشده:

1. jobهای host، ارسال و intake را متوقف/آرام کنید؛ claimهای حل‌نشده و تاریخچهٔ ارسال را حفظ کنید. در این بازه configuration و pairing تغییر نکند.
2. با همان حساب سرویس، از API آنلاین SQLite backup بگیرید؛ DB زنده و فایل WAL را با copy ساده پشتیبان نگیرید. مسیرهای نمونه را با مسیرهای خصوصی واقعی جایگزین کنید:

```python
import sqlite3
from pathlib import Path

source = Path('/PRIVATE/state/memory.sqlite3').resolve()
target = Path('/PRIVATE/backup/snapshot/memory.sqlite3').resolve()
# Parent must already have restrictive permissions; target must be fresh.
if not source.is_file() or target.exists():
    raise RuntimeError('Expected existing source and fresh private target')
with sqlite3.connect(source.as_uri() + '?mode=ro', uri=True) as src:
    with sqlite3.connect(target) as dst:
        src.backup(dst)
        if dst.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError('Backup integrity failure')
```

3. در همان بازهٔ بدون تغییر، credentials/setup/mcp/capabilities و در صورت استفاده opengym.private.json را با ابزار امن محیط در snapshot خصوصی نگه دارید؛ مقدار secret environment از secret store مجاز بازیابی شود. کپی فایل‌ها به تنهایی receipt سازگاری configuration نیست. revision برنامه، نسخهٔ dependency، زمان و hash فایل‌ها را در فهرست خصوصی ثبت کنید. token یا payload را در گزارش عمومی ننویسید.
4. سرویس را ادامه دهید و backup را طبق توافق نگه دارید. حذف/کاهش scope در primary store، snapshot قدیمی را پاک نمی‌کند.

## restore و rollback

ابتدا اصل خراب/نسخهٔ فعلی را حفظ کنید. snapshot را در private home تازه و شبکه/ارسال ایزوله restore کنید؛ endpoint گوشی و jobهای host هنوز به آن وصل نشوند. نسخهٔ برنامه سازگار با schema انتخاب شود؛ DB با user_version بالاتر را downgrade نکنید. integrity_check، doctor و خواندن scoped چند رکورد با مرجع خصوصی بررسی شوند؛ خروجی سلامت منتشر نشود. bootstrap نباید برای پوشاندن credential مفقود کلید تازه بسازد.

قبل از فعال‌سازی، پیام‌های ارسال‌شده بعد از snapshot را با تاریخچهٔ واقعی کانال تطبیق دهید. pending قدیمی ممکن است قبلاً ارسال شده باشد؛ lease/uncertain را با ابزار reconciliation و رسید واقعی حل کنید. اگر pending قبلاً ارسال شده ولی عملیات موجود امکان ثبت آن را نمی‌دهد، ارسال را متوقف نگه دارید تا recovery مجاز انجام شود؛ DB را حدسی ویرایش نکنید. scope، pause و tokenهای منسوخ را با تصمیم فعلی مالک تطبیق دهید. تنها بعد از readback و reconciliation، intake و delivery را وصل کنید. restore می‌تواند داده/مجوز حذف‌شده را برگرداند؛ موفقیت integrity این مشکل را حل نمی‌کند.

## پذیرش عملیاتی

رسید لازم: محیط و مالک، restart سرویس، TLS از گوشی، POST/خواندن احرازشده، رد token نامعتبر، عدم افشای URL خصوصی در لاگ، backup و restore ایزوله، و رفع uncertain-send. همهٔ این موارد تا اجرای واقعی unverified هستند. rollback نرم‌افزار نباید DB جدید را با runtime ناسازگار باز کند.
