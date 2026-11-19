# قرارداد میزبان برای سرویس اختیاری HTTP

مسیر روزمرهٔ دات از [دستور شروع و ادامه](../../INSTALL.md) با ابزارهای موجود میزبان می‌گذرد. جزئیات زیر زمانی کاربرد دارد که استقرار سرویس HTTP انتخاب شده باشد.

## بررسی کوتاه پیش از اعلام نصب

ChatGPT Dot ابتدا توان واقعی خواندن مخزن و شروع مأموریت Work/Codex را بررسی کند. executor باید اجرای Python، محل خصوصی پایدار، دسترسی بسته‌ها، قابلیت سرویس ماندگار، HTTPS قابل‌دسترسی از گوشی، ابزار رسانه و کانال را جدا بسنجد. برای هر قابلیت `verified` همراه receipt_ref/checked_at، `unavailable` یا `unknown` ثبت شود. `native_instances` فقط پس از ساخت واقعی، instance_id/receipt_ref می‌گیرد؛ این فیلدها گواهی میزبان‌اند و خودشان چیزی نمی‌سازند.

مسیر توصیه‌شده: Dot هماهنگ می‌کند؛ executor محدود Work/Codex نصب خصوصی و فراخوانی Python/REST یا MCP stdio را انجام می‌دهد. executor گزینهٔ فنی را کشف می‌کند؛ شرکت‌کننده نباید بین MCP و API انتخاب کند. ChatGPT web تنظیم محلی Codex را نمی‌خواند و OpenAPI خودبه‌خود ابزار وب نمی‌شود. آداپتور remote MCP/OAuth جدا و در انتظار پیاده‌سازی است؛ endpoint حساس بدون احراز هویت جایگزین مجاز نیست.

اگر توان اجرا وجود ندارد، نتیجه «نصب متوقف در قابلیت X» است. کوچک‌ترین گام اتصال واقعاً لازم توضیح داده شود؛ راهنمای گفت‌وگویی، نصب موفق نامیده نشود. رایانهٔ محلی خاموش یا اپ بسته و پایان cloud task ممکن است اجرای بعدی را قطع کند.

## تحویل executor

با محدودهٔ مخزن و private home خارج از آن کار کند؛ نصب موجود را resume کند. فرمان مرجع:

```text
python scripts/bootstrap.py --install --home <PRIVATE_HOME> --public-url https://<APPROVED_HOST>
python scripts/doctor.py --home <PRIVATE_HOME>
```

اگر HTTPS هنوز تعیین نشده، bootstrap محلی بدون `--public-url` ممکن است؛ pairing تا تعیین endpoint معتبر آماده نیست. `setup.private.json`، credentials و `mcp.private.json` فقط در فضای خصوصی‌اند. رمزها در چت، لاگ، issue یا گزارش عمومی نیایند. اجرای دوباره نباید حافظه/کلید را از نو بسازد؛ کلید مفقود در store موجود نیازمند recovery صریح است.

| نتیجه | شاهد لازم |
|---|---|
| نصب محلی | نسخهٔ دقیق، Python/dependency versions، bootstrap دوباره، doctor و خواندن احرازشده پس از restart |
| سرویس ماندگار | مالک، supervisor واقعی، restart و healthz؛ نه صرف فرمان پیشنهادی |
| گوشی | pairing خصوصی، انتخاب انسانی scope، Manual Upload و تطبیق دادهٔ مجاز با گوشی |
| اجرای نقش | بارگیری role/skill، task ID، claim/report/review/close؛ native receipt یا برچسب virtual |
| ارسال | claim، عمل واقعی کانال و receipt؛ خوانده‌شدن/اجراشدن همچنان unknown |

## مسئولیت و توجه

CoS بیرون تیم است: رابطه، اختیار، هماهنگی و دروازهٔ توجه را نگه می‌دارد. Manager ساختار/ثبت/مالک قدم بعد و بستهٔ آماده را اداره می‌کند؛ Analyst مشاهده/فرض/ابهام، Coach کمک عملی انتخاب‌شده و Companion حمایت هیجانی غیرپزشکی را بر عهده دارند. هیچ pipeline اجباری یا ایجنت دائمی برای هر دامنه لازم نیست. مدل و رسانه از قابلیت موجود میزبان می‌آید؛ اشتراک LLM تازه لازم نیست.

کار با `wellbeing_task` یا `/v1/tasks/{operation}`: create→prepared، claim→running، report→report_received، review→verified یا prepared، close→closed. ساخت task، dispatch یا spawn نیست. نقش مسئول گزارش می‌دهد و مسئولیت متفاوت آن را بازبینی می‌کند. scope، شواهد و قرارداد فعلی پیش از اجرا دوباره بررسی شوند.

Manager یک entry از kind=packet با متن فارسیِ آمادهٔ بخش ول‌بینگ می‌سازد: مشاهدهٔ تاریخ‌دار، محدودیت مهم، پیشنهاد اختیاری در صورت نیاز و قدم بعد. بسته می‌تواند لینک آمادهٔ تمرین داشته باشد؛ CoS مسئول دانلود/رونویسی مجموعهٔ ویدئوها نیست. CoS طبق توافق توجه، ارائه یا تعویق را تصمیم می‌گیرد؛ زمان صبحگاهی یا نسبت تخصیص نمونه‌های شخصی‌اند، نه پیش‌فرض عمومی.

## قرارداد job و تحویل

`scripts/host_tick.py collect --home <PRIVATE_HOME> --output <FRESH_PRIVATE_JOB_JSON>` با token همان نقش در محیط اجرا شود. host job واقعی باید آن را فراخوانی، فایل خصوصی را پردازش و نتیجهٔ واقعی را با `apply --results <PRIVATE_RESULTS_JSON>` ثبت کند. collect یک worker یا scheduler ایجاد نمی‌کند. worker متخصص token خودش را دارد، نه host token.

برای کانال: `wellbeing_delivery_claim` یا `POST /v1/outbox/claim`، سپس ارسال در اختیار/مهلت با idempotency_key، سپس ack شامل id/claim_token/receipt_ref. lease تحویل پنج دقیقه است. ارسال نامعلوم را خودکار تکرار نکنید؛ پس از lookup واقعی، reconcile با delivered/not_sent/unknown. فقط not_sent امکان بازگشت به pending دارد؛ unknown در uncertain می‌ماند. producer دقیقه‌ای API فقط صف می‌سازد. پاسخ HTTP 200، synthetic ack و closed task شاهد پیام واقعی یا اثر آن نیستند. لغو scope میان claim و ارسال نیازمند بازبینی میزبان است؛ تراکنش اتمی با کانال خارجی وجود ندارد.

برای آداپتور وبِ بعدی، follow-up پیشنهادی: `wellbeing/remote_mcp.py`، `wellbeing/oauth.py` و `tests/test_remote_mcp.py`؛ metadata، PKCE S256، audience/resource، redirect و لغو credential باید بررسی شوند. این فایل‌ها در این تحویل ساخته نشده‌اند.
