# پذیرش MVP: شاهد کد، میزبان و گوشی

آخرین baseline تأمین‌شدهٔ هماهنگ‌کننده در `2026-11-17T13:48:05Z`: اجرای ۱۱۵ unittest در 9.049s با OK و یک skip مربوط به Windows symlink؛ loopback TCP/restart smoke و legacy demo نیز موفق بودند. سه دقت زمانی غذا و projection چهارمسئولیتی catalog به سه نقش legacy بدون گسترش مجوزهای legacy محلی آزموده شده‌اند. [QA](../../qa/mvp-verification.json) محل سوابق و ثبت نتیجهٔ نسخهٔ نهایی است.

این baseline پیش از اصلاح باقی‌ماندهٔ reminder و بررسی نهایی بسته است. کارگر این آرتیفکت هیچ ابزاری اجرا نکرده؛ آزمون‌های گزارش‌شده را هماهنگ‌کننده واقعاً اجرا کرده است. گوشی، Dot، WhatsApp، HTTPS واقعی، Docker، OpenGym زنده و backup/restore هنوز unverified هستند.

سطوح شاهد: S=fixture/کد، L=محلی/transport، H=میزبان/کانال واقعی، D=گوشی، P=عملیات ماندگار. هر نتیجه revision/hash، محیط، فرمان/عمل، زمان، pass/fail/not-run، محدودیت و مرجع شاهد داشته باشد. شاهد خصوصی فقط طبق توافق شرکت‌کننده نگهداری شود؛ گزارش عمومی دادهٔ سلامت ندارد.

| شناسه/سطح | معیار قابل شکست | وضعیت |
|---|---|---|
| A01 S/L | suite، demo، smoke، build و validate روی نسخهٔ ترکیبی؛ مسیر legacy بدون HTTP/MCP usable و skipها آشکار. | baseline محلی موفق؛ final package pending |
| A02 L/H | URL root بدون prompt دوم به INSTALL و executor واقعی برسد؛ capability probe، bootstrap دوباره بدون تغییر کلید/داده، readback پس از restart. | local baseline؛ Dot واقعی pending |
| A03 P/D | مالک و حساب محیط مجاز مشخص؛ supervisor restart شود و HTTPS از گوشی در دسترس باشد؛ cloud task موقت کافی نیست. | pending؛ Docker/template شاهد deployment نیست |
| A04 D | pairing خصوصی، انتخاب انسانی مجوز/خرید/scope؛ automation مرور و فعال، Manual Upload و تطبیق نمونهٔ گوشی با receipt/readback. | pending |
| A05 S/L | هشت آرایهٔ HAE، alias جمع/مفرد اعلان، replay/concurrency، conflict atomic، revision، restart، زمان unknown و رد کلید ناشناخته. | synthetic baseline موفق؛ `tests/test_hae_wire.py` |
| A06 S/D | تاریخچهٔ محدود و incremental/replay؛ تأخیر و خطای منبع explicit، missing صفر نباشد و fallback identity محدودیتش را حفظ کند. | بخشی synthetic؛ device pending |
| A07 S/H | intake فقط write، scope نقش/شرکت‌کننده، invalidation derived/task، pause، retention، delete و revocation؛ نسخه‌های خارجی جدا بررسی شوند. | local synthetic؛ external copies pending |
| A08 S/H | task create/claim/report/review/close و revise؛ catalog چهارمسئولیتی با legacy سازگار؛ native فقط با receipt وگرنه virtual، CoS بیرون تیم. | local catalog/lifecycle موفق؛ host pending |
| A09 S/H | photo/voice واقعی با source-message ID پایدار، correction، estimate غذایی و skipped/declined بدون صفرسازی. | service synthetic؛ رسانه/کانال واقعی pending |
| A10 S/H | exact/day/unknown با schema زیر؛ صبحانهٔ امروز بدون ساعت، suppression همان روز/meal و correction همان ID. | precision محلی آزموده؛ dialogue واقعی pending؛ A16 جدا |
| A11 S/H | quiet hours، budget، stop؛ claim→send واقعی→ack، uncertain-send و retry فقط با not_sent مستند. | queue synthetic؛ job و WhatsApp pending |
| A12 H | Manager بخش فارسی آماده با تاریخ/ابهام/قدم بعد/لینک بدهد؛ CoS ارائه یا تعویق کند؛ delivery/adoption/execution/outcome جدا بمانند. | pending host |
| A13 H | Companion حمایت غیرپزشکی، یادداشت حداقلی و گیرندگان مجاز؛ بدون درمان یا پایش اضطراری خودکار؛ محدودیت میزبان مشترک روشن. | host evaluation pending |
| A14 S/H | OpenGym not_configured صادقانه؛ initialize/list و mapping reviewed، search واقعی، رد write و عدم استخراج رسانه. | local adapter checks؛ live server pending |
| A15 P | Connection.backup، restore ایزوله و scoped readback؛ تطبیق scope/token و history ارسال پیش از فعال‌سازی delivery. | procedure موجود؛ اجرا pending |
| A16 S/L | correction وعدهٔ امروز به روز قبل/unknown، reminder cancelled واجد شرایط و هرگز ارسال‌نشده را درست rearm کند؛ پیام ارسال‌شده/نامعلوم خودکار تکرار نشود. | patch و regression مستقل pending؛ baseline ۱۱۵ شاهد آن نیست |

## پذیرش دقیق غذا

دقیقاً سه مقدار `time_precision` وجود دارد: exact، day، unknown. `meal` برابر breakfast/lunch/dinner/snack است؛ فیلد slot نسازید. تخمین nutrients عکس مقدار چهارم temporal precision نیست.

نمونهٔ exact:

```json
{"meal":"breakfast","time_precision":"exact","occurred_at":"2026-11-17T08:10:00+03:30","source_kind":"self_report"}
```

باید timestamp دارای timezone نگه دارد و occurred_date نداشته باشد؛ time_precision=exact در ورودی سازگار قدیمی اختیاری است.

برای «صبحانهٔ امروز»، ابتدا امروز در timezone شرکت‌کننده از زمینهٔ معتبر حل شود. اگر تاریخ محلی اعلام‌شده 2026-11-17 است:

```json
{"meal":"breakfast","time_precision":"day","occurred_date":"2026-11-17","source_kind":"photo_estimate","nutrient_certainty":"estimate"}
```

باید تاریخ YYYY-MM-DD و timezone عرضه‌شده یا فعلی شرکت‌کننده حفظ شود، occurred_at ساخته نشود، و فقط reminder همان تاریخ/meal سرکوب شود. سؤال ساعت لازم نیست مگر تصمیمی واقعاً به آن وابسته باشد. تاریخ نمونه جای امروز واقعی ننشیند.

```json
{"meal":"snack","time_precision":"unknown","source_kind":"self_report"}
```

باید هیچ occurrence field نداشته باشد و هیچ reminder تاریخ‌دار را سرکوب نکند. هر نمونه داخل entry با kind=meal و ID پایدار ثبت/readback شود؛ correction همان ID را نگه دارد. A16 ادامهٔ مستقل بررسی correction است، نه نشانهٔ پیاده‌نبودن خود precision.

## بررسی نسخهٔ نهایی

پس از اعمال اصلاح باقی‌مانده و نصب وابستگی‌های pinشده، از root:

```text
python -m unittest discover -s tests -v
python scripts/demo.py
python scripts/mvp_smoke.py
python scripts/build_release.py
python scripts/validate_package.py
```

هماهنگ‌کننده نتیجهٔ واقعی و failure/skip را در QA ثبت کند. TestClient شاهد HTTP درون‌فرایندی، smoke شاهد loopback TCP، و MCP subprocess شاهد ابزار محلی است؛ هیچ‌کدام TLS عمومی، iOS background یا ارسال WhatsApp نیستند. بسته/manifest نسخهٔ 0.2.0 و entrypointهای جدید را پوشش دهند. pass نهایی نرم‌افزار جای gateهای H/D/P یا پذیرش فایده توسط شرکت‌کننده نیست.
