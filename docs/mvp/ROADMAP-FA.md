# نقشهٔ تحویل MVP ۰٫۲ — چه، چرا، چگونه

هدف: روی یک آیفون و میزبان واقعی، دریافت انتخابی سلامت، حافظهٔ ماندگار و یک نتیجهٔ مفیدِ آمادهٔ ارائه نشان دهیم. شرکت‌کننده فقط URL مخزن را به ChatGPT Dot می‌دهد؛ انتخاب‌های فنی با executor است. تعداد ایجنت، سند یا پیام معیار فایده نیست.

## وضعیت فعلی و مسیر منتخب

نسخهٔ ۰٫۲٫۰، سه دقت زمانی غذا، سازگاری catalog با legacy و اصلاح reminder محلی تأیید شده‌اند. نتایج واقعی bridge/app گزارش‌شدهٔ هماهنگ‌کننده در [QA](../../qa/mvp-verification.json) ثبت‌اند: suite ترکیبی ۱۲۴تایی، TCP/restart smoke، demo و validator ساختار/لینک/metadata موفق؛ سپس suite نصب‌شده و no-site پس از تغییر صرفاً fixture موفق بوده‌اند، با skipهای آشکار. preflight ساخت، اعتبارسنجی ۱۲۷ فایل، build تکرارپذیر و اعتبارسنجی نسخهٔ استخراج‌شده موفق است؛ وضعیت بازبینی نهایی metadata پس از تغییر شواهد در QA مرجع است. کد ورودی canonical برابر `0c0bfe0ee62d061d66feec76e6c4048d44973521` پس از آزمون bytes معادل بسته شده است. گوشی، حساب Dot/native workers، کانال/زمان‌بند، HTTPS واقعی، Docker، OpenGym زنده و backup/restore تأیید نشده‌اند.

پیش از اعلام نصب، Dot خواندن مخزن و اجرای مأموریت Work/Codex را واقعاً بررسی کند. مسیر پیش‌فرض، سرویس Python خصوصی روی محیط ماندگارِ مجاز، intake با HTTPS پایدار و احراز هویت، و executor محدودِ واگذارشده از Dot است. cloud task را سرور ورودی دائمی فرض نمی‌کنیم. محل hosting، مالک و حساب در دسترس هنوز gate باز است. [قرارداد میزبان](host-contract.md) و [استقرار](deployment.md) روش اجرا را مشخص می‌کنند؛ شرکت‌کننده بین MCP و API انتخاب نمی‌کند.

SQLite، REST، MCP stdio، pairing، دریافت هشت دستهٔ Health، غذا، صف یادآوری، task/review و پل اختیاری OpenGym در runtime هستند. استنتاج، vision/transcription و ارسال کانال را قابلیت واقعی میزبان فراهم می‌کند؛ اشتراک تازهٔ LLM لازم نیست. ChatGPT web تنظیم محلی Codex را وارد نمی‌کند و OpenAPI خودکار ابزار وب نمی‌شود. remote MCP/OAuth یک آداپتور مستقلِ پیاده‌نشده است.

HAE به دلیل اپ موجود، REST و setup links مستند انتخاب اول است. Shortcuts محرک بازیابی است و محدودیت Health/iOS را حذف نمی‌کند؛ فایل shortcut جعلی نمی‌سازیم. Gmail/Drive فقط fallback با adapter و مجوز و آزمون واقعی‌اند. اپ HealthKit اختصاصی پیش از اثبات این قطعه هزینهٔ نگهداری بیشتری دارد. OpenGym اختیاری و مخصوص ابزار تمرین است. [پژوهش و مراجع](research.md) دلیل انتخاب‌ها و اقتباس محدود ECC/V2 را توضیح می‌دهد؛ V2 سیاست مصوب شرکت نیست.

## وابستگی‌ها و شاهد پایان

| گام | چه و چرا | چگونه و شاهد لازم |
|---|---|---|
| ۱. توان میزبان | شروع از URL به اجرای واقعی برسد | README→INSTALL؛ Dot ابزار خواندن/واگذاری و executor اجرای Python، private home و ابزارهای واقعی را probe کنند. قابلیت verified فقط با receipt و زمان؛ در غیر این صورت unknown/unavailable. |
| ۲. اختیار و زمینه | کمترین سؤال برای نتیجهٔ مفید | هدف، داده، گیرندگان/providers، نگهداری و توجه معتبر موجود بازیابی شود؛ فقط شکاف مؤثر پرسیده شود. محیط و مالک خدمات مشخص شوند. |
| ۳. نصب و حافظه | ادامه بدون از دست دادن کلید/داده | bootstrap دوبار در همان private home، doctor و readback احرازشده پس از restart؛ SQLite خارج checkout و CLI قدیمیِ JSON جدا. |
| ۴. ماندگاری و HTTPS | گوشی پس از پایان جلسه هم endpoint داشته باشد | ابتدا ماشین/سرویس همیشه‌روشنِ صریحاً مجاز موجود؛ سپس proxy/tunnel ثابت با حساب واقعی؛ restart و TLS از گوشی. hosting پولی تازه فقط با اختیار لازم. |
| ۵. یک گوشی | قطعهٔ واقعی سرتاسری | pairing خصوصی ۲۰دقیقه‌ای، انتخاب scope/گیرنده/retention، مرور لینک HAE و فعال‌سازی اپ، Manual Upload و تطبیق نمونه با readback. |
| ۶. تاریخچه و ادامه | زمینهٔ اولیه و اصلاح قابل اعتماد | import محدود در سقف retention با batching، سپس بازپخش اخیر؛ تکرار، correction، تأخیر و خطای منبع بررسی شوند. |
| ۷. نقش و بسته | نتیجهٔ آماده با بار توجه کم | task محدود فقط برای مسئولیت لازم، report/review/close؛ Manager بخش فارسی آماده بسازد و CoS ارائه/تعویق را تصمیم بگیرد. |
| ۸. غذا و تماس | ثبت ساده در کانال فعلی | photo/voice/text واقعی، ID پایدار و اصلاح همان entry؛ زمان‌های انتخابی وعده‌ها، quiet hours، budget، stop و send با receipt مستقل. |
| ۹. عملیات و بسته | موفقیت ظاهری حذف شود | اصلاح reminder و preflight بسته تأیید شده‌اند؛ بازبینی نهایی metadata در QA؛ backup/restore ایزوله و uncertain-send واقعی و پذیرش جدا لازم‌اند. |

فرمان نصب از root:

```text
python scripts/bootstrap.py --install --home <PRIVATE_HOME> --public-url https://<APPROVED_HOST>
```

doctor و اجرای سرویس با Python همان `runtime-venv` انجام شوند:

```text
python scripts/doctor.py --home <PRIVATE_HOME>
python scripts/run_server.py
```

برای سرویس، `WELLBEING_MVP_HOME` و `WELLBEING_PUBLIC_URL` خصوصی تنظیم شوند؛ supervisor واقعی جدا لازم است. اگر HTTPS هنوز تعیین نشده، نصب محلی بدون `--public-url` ممکن است، اما pairing آماده نیست. لپ‌تاپ خاموش، اپ لازم بسته یا پایان task می‌تواند کار را قطع کند. هزینه و دسترسی hosting باید کشف شود؛ template شاهد استقرار نیست.

## دادهٔ سلامت و کار گوشی

شکل نمونهٔ ساختگی HAE JSON v2:

```json
{"data":{"metrics":[{"name":"step_count","units":"count","data":[{"date":"2026-11-17T09:00:00+03:30","qty":123}]}]}}
```

`wellbeing/hae.py` نام روی سیم `heartRateNotifications` را به دستهٔ داخلی مفرد `heartRateNotification` تبدیل می‌کند؛ datatype لینک نیز مفرد است. هشت دسته شامل metrics، workouts، symptoms، cycleTracking، ecg، medications، stateOfMind و اعلان ضربان هستند. پشتیبانی قالب تضمین وجود داده روی هر گجت نیست؛ OS، منطقه، ثبت واقعی و مجوز مؤثرند. وجود workout، وزنه/تکرار را مشخص نمی‌کند. کلید ناشناخته یا تعارض همان هویت در یک درخواست، کل درخواست را رد می‌کند.

scope دسته و نقش در سرور اعمال می‌شود؛ انتخاب ریزِ metric در HAE نیز باید بررسی شود، چون server فیلتر مجوز مستقل برای هر metric ندارد. همهٔ سنجه‌ها انتخاب صریح است؛ حذف پارامتر metrics از لینک این حالت را می‌سازد. routes تمرین پیش‌فرض خاموش‌اند. ID واقعی مقدم است؛ fallback بدون ID پایدار ممکن است با تغییر زمان/منبع/توصیف رکورد تازه بسازد. تکرار double count نیست؛ اصلاح هویت ثابت revision دارد. زمان نامعلوم از receive time حدس زده نمی‌شود. missing یا شکست منبع صفر نیست. تاریخچهٔ قدیمی‌تر از retention، expired می‌شود؛ انتخاب بازه با نگهداری هماهنگ باشد.

کار انسانی: نصب HAE روی آیفون، انتخاب trial/خرید، مجوز Apple Health، مرور هر automation و روشن‌کردن Enabled، سپس upload دستی. زمان انجام تضمین نمی‌شود. قیمت بررسی‌شدهٔ آمریکا در [منبع خرید](https://help.healthyapps.dev/en/health-auto-export/purchases/pricing/): trial هفت‌روزه، Premium سالانه $6.99 یا مادام‌العمر $24.99؛ REST خودکار Premium می‌خواهد. قیمت محلی صفحهٔ گوشی مرجع نهایی است؛ خریدی فرض نمی‌شود. قفل گوشی و محدودیت iOS ممکن است پس‌زمینه را عقب بیندازد؛ تنظیم ساعتی تضمین ساعتی نیست. Manual Upload/Shortcuts/widget مسیر بازیابی‌اند.

## غذا: ساعت فقط وقتی واقعاً معلوم است

در `wellbeing/service.py` دقیقاً سه مقدار زمانی وجود دارد: `exact`، `day` و `unknown`. `meal` یکی از breakfast/lunch/dinner/snack است؛ فیلد ساختگی slot نداریم. تخمین عکس مربوط به `source_kind` و `nutrient_certainty` است، نه مقدار چهارم دقت زمانی.

نمونه‌ها payload هستند و داخل entry با `id` پایدار و `kind: meal` قرار می‌گیرند:

```json
{"meal":"breakfast","time_precision":"exact","occurred_at":"2026-11-17T08:10:00+03:30","source_kind":"self_report"}
```

exact، `occurred_at` دارای timezone نگه می‌دارد و `occurred_date` ندارد؛ برای سازگاری ورودی قبلی، time_precision=exact اختیاری است.

```json
{"meal":"breakfast","time_precision":"day","occurred_date":"2026-11-17","source_kind":"photo_estimate","nutrient_certainty":"estimate","description":"صبحانهٔ امروز؛ مقدار نامعلوم"}
```

این مثال فرض می‌کند تاریخ محلیِ اعلام‌شده/حل‌شدهٔ شرکت‌کننده 2026-11-17 است؛ تاریخ ثابت نمونه را برای «امروز» واقعی کپی نکنید. day، تاریخ YYYY-MM-DD و timezone عرضه‌شده یا timezone فعلی شرکت‌کننده را حفظ می‌کند و `occurred_at` ندارد. ساعت ۰۰:۰۰ یا ساعت دریافت اختراع نمی‌شود. «صبحانهٔ امروز» با تاریخ محلی و `meal=breakfast` کافی است؛ فقط ابهام مؤثر بر تصمیم follow-up می‌خواهد.

```json
{"meal":"snack","time_precision":"unknown","source_kind":"self_report","description":"زمان خوردن مشخص نیست"}
```

unknown هیچ‌یک از occurred_at/occurred_date را ندارد و reminder تاریخ‌دار را سرکوب نمی‌کند. day فقط reminder همان روز و همان meal را سرکوب می‌کند. correction با همان ID انجام شود. ثبت/خواندن این سه حالت محلی آزموده شده است؛ آزمون کانال و فهم رسانهٔ واقعی جداست.

اصلاح rearm پیاده و با ۹ regression در suite ۱۲۴تایی محلی تأیید شده است: اگر وعدهٔ امروز reminder هرگز ارسال‌نشده را cancelled کرده و سپس به روز قبل یا unknown اصلاح شود، فقط reminder واجد شرایط زیر gateهای فعلی زمان، quiet hours و budget دوباره pending می‌شود. delivered/uncertain و شاهد lease/claim/receipt قبلی مانع تکرار خودکارند؛ ارسال کور مجاز نیست.

مقدار و مواد نامعلوم unknown بمانند؛ nutrients عکس estimate هستند و label/weighed فقط به اندازهٔ شاهد اعتبار دارند. skipped/declined یا توقف یادآوری صفر کالری و شکست شرکت‌کننده نیست. گزارش غذا هدف کاهش وزن یا رژیم محدودکننده ایجاد نمی‌کند.

## تیم، توجه و حمایت هیجانی

Manager سازمان‌دهی، ثبت، رفع تعارض، مالک قدم بعد و packet را دارد؛ Analyst مشاهده/کیفیت/فرض/تأیید را جدا می‌کند؛ Coach برای هدف منتخب کمک عملی می‌دهد؛ Companion مسئولیت چهارم برای شنیدن و حمایت غیرپزشکی است. تشخیص، درمان، تقلید شخصیت مشهور و پایش اضطراری خودکار ارائه نمی‌شود. یادداشت حداقلی و اشتراک فقط در scope مجاز؛ در حالت virtual، میزبان ممکن است گفتگو را ببیند و تفکیک API به معنی محرمانگی از خود میزبان نیست.

CoS بیرون تیم، رابط و دروازهٔ توجه می‌ماند. Manager با entry از kind=packet بخش فارسی آماده می‌سازد: مشاهدهٔ تاریخ‌دار، ابهام مهم، قدم اختیاری و مالک بعدی، با لینک آماده در صورت نیاز. CoS طبق توافق، آن را در خبرنامه ارائه یا تعویق می‌کند؛ cadence و زمان صبحگاهی پیش‌فرض عمومی نیستند. همهٔ نقش‌ها pipeline اجباری نیستند و CoS مسئول دانلود/رونویسی مجموعهٔ ویدئوها نمی‌شود. native agent فقط با creation receipt؛ در غیر این صورت virtual صریح.

حافظهٔ اصلی SQLite خصوصی است. Manager ساختار و ثبت را اداره می‌کند؛ Sheets/Notion فقط پس از adapter مجاز و readback/correction/deletion تأییدشده می‌توانند mirror باشند. sync ابری فعال ادعا نمی‌شود. OpenGym نیز فقط پل reviewed read/search/preview است؛ write و استخراج رسانه غیرفعال، لینک بومی آماده مجاز و اتصال زنده pending است.

## شکست، لغو و ادامه

scope فعلی پیش از کار بررسی شود. تغییر scope derived context/packet/plan/finding و taskها را محافظه‌کارانه باطل می‌کند؛ دستهٔ حذف‌شده از primary پاک می‌شود. pause کار و صف در انتظار را متوقف می‌کند و حذف داده نیست. retention روی عملیات runtime/tick اجرا می‌شود، نه تضمین پاک‌سازی فیزیکی در لحظهٔ انقضا. delete منطقی و revocation token، backup/chat/provider copies را حذف نمی‌کند؛ SQLite رمزگذاری داخلی ندارد.

صف delivery lease پنج‌دقیقه‌ای و idempotency key دارد. پایان lease به uncertain می‌رود؛ timeout مجوز retry نیست. میزبان پس از lookup واقعی، delivered/not_sent/unknown را reconcile کند؛ فقط not_sent امکان بازگشت به pending دارد. producer داخل API فقط صف می‌سازد؛ job و کانال واقعی جدا لازم‌اند. cancellation و send خارجی تراکنش اتمی ندارند؛ پیش از ارسال اعتبار فعلی بررسی شود. خواندن، پذیرش، اجرا و نتیجه با receipt تحویل اثبات نمی‌شوند. freshness با event/received و خطای منبع بیان شود، نه threshold بالینی عمومی.

## نمایش جلسهٔ بعد و بررسی نهایی

نمایش خصوصی: یک نمونهٔ انتخابی گوشی → receipt → readback پس از restart → replay/correction → task/review → بخش فارسی آماده → تصمیم CoS و در صورت اختیار send واقعی با receipt. یک «صبحانهٔ امروز» بدون ساعت، correction و توقف یادآوری هم نشان داده شود. شرکت‌کننده فایده و بار توجه را ارزیابی کند؛ نگهداری شواهد شخصی نیازمند توافق است. repo عمومی فقط fixture و خلاصهٔ پالایش‌شده دارد.

آزمون‌های محلی ثبت شده‌اند؛ برای تکرار بررسی و تکمیل gate بسته، با وابستگی‌های pinشده از root اجرا شود:

```text
python -m unittest discover -s tests -v
python scripts/demo.py
python scripts/mvp_smoke.py
python scripts/build_release.py
python scripts/validate_package.py
```

نسخه، محیط، نتیجه، failure و skip در QA ثبت شوند. digest آرشیو داخل QA بسته قرار نگیرد؛ artifact_sha256 null بماند و digest بیرون بسته در `dist/SHA256SUMS.txt` و GitHub asset ارائه شود. مسیر no-site قدیمی با skipهای توضیح‌داده‌شده موفق بوده؛ ۱۶ خطای timezone تلاش قبلی با UTC در fixtureهای عمومی/بین‌شرکت‌کننده اصلاح شد و فقط دو مورد واقعی bootstrap پیش‌فرض تهران بدون IANA data شرطی skip می‌شوند. نصب خصوصی، تکرار bootstrap با نسخهٔ ۰٫۲ و حفظ credentials، و health محلی مشاهده شده‌اند. CI دارای dependency install و TCP smoke است ولی اجرای remote تأیید نشده. build/manifest جای پذیرش گوشی، Dot یا کانال نیست؛ کارگر آرتیفکت ابزار اجرا نکرده است.
