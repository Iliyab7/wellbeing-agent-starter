# تصمیم‌های پژوهشی MVP — ۲۰۲۶-۱۱-۱۷

این سند از منابع اولیه و بستهٔ مرجعِ تأمین‌شده توسط هماهنگ‌کننده استفاده می‌کند؛ کارگر آرتیفکت مرور وب یا آزمون تازه انجام نداده است. [ورودی پژوهش](research-input.md) جزئیات بررسی منابع را نگه می‌دارد. ادعای منبع، تصمیم مهندسی و شاهد اجرای محصول سه چیز جدا هستند.

| موضوع و منبع اولیه | تصمیم و دلیل | پیاده‌سازی و محدودیت |
|---|---|---|
| [Dot computers/apps](https://learn.chatgpt.com/docs/dots/computers-and-apps.md) | میزبان مشخص، ChatGPT Dot است. ابتدا ابزار واقعی را کشف کند؛ مسیر پیشنهادی، مأموریت محدود Work/Codex است. | قرارداد [میزبان](host-contract.md)؛ رایانهٔ ابری Dot تضمین سرویس ورودی دائمی نیست. قابلیت حساب خصوصی بررسی نشده است. |
| [ChatGPT MCP](https://learn.chatgpt.com/docs/extend/mcp.md)، [remote MCP](https://developers.openai.com/api/docs/guides/custom-mcp-server.md)، [OAuth](https://developers.openai.com/plugins/build/auth.md) | REST/OpenAPI و تنظیم محلی Codex را پلاگین وب ننامیم. آداپتور remote authenticated MCP/OAuth مرحلهٔ جداست. | `wellbeing/api.py` و `wellbeing/mcp_server.py` مسیر فعلی‌اند؛ نصب/ثبت پلاگین وب انجام نشده است. |
| [HAE REST](https://help.healthyapps.dev/en/health-auto-export/automations/rest-api/)، [deep links](https://help.healthyapps.dev/en/health-auto-export/automations/deep-link/) | خروجی انتخابی JSON v2 با یک automation برای هر datatype؛ لینک تنظیم خصوصی، با مرور و فعال‌سازی روی گوشی. سریع‌تر از ساخت اپ HealthKit اختصاصی است. | `wellbeing/iphone.py`؛ headers به شکل `Authorization,Bearer TOKEN`، percent encoding، routes خاموش، automation ابتدا غیرفعال. لینک حاوی کلید است. |
| [HAE automation](https://help.healthyapps.dev/en/health-auto-export/automations/)، [catalog](https://help.healthyapps.dev/en/health-auto-export/getting-started/supported-data/) | تاریخچهٔ محدود و سپس بازپخش اخیر؛ تازگی با event time و دریافت سنجیده شود. | `wellbeing/service.py`؛ iOS، قفل گوشی و محدودیت پس‌زمینه مانع تضمین تناوب‌اند. وجود دسته در کاتالوگ، وجود داده روی هر گجت نیست. |
| [HAE pricing](https://help.healthyapps.dev/en/health-auto-export/purchases/pricing/) | REST خودکار به Premium نیاز دارد؛ انتخاب خرید انسانی است. | بررسی تأمین‌شده: آزمایش ۷روزه، آمریکا $6.99 سالانه یا $24.99 مادام‌العمر؛ صفحهٔ محلی خرید مرجع نهایی است. خریدی انجام نشده است. |
| [MCP transports](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports)، [Python SDK v1](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x) | SDK رسمی، stdout مختص پروتکل، نسخهٔ pinشده. | MCP==1.30.0 در `requirements-mvp.txt`؛ stdio محلی و client اختیاری Streamable HTTP، نه endpoint ساختگی MCP. |
| [OpenGym MCP](https://github.com/DuarteSantos8/openGym/blob/main/mcp/README.md)، [media notice](https://github.com/DuarteSantos8/openGym/blob/main/catalogue/media/NOTICE.md) | پل اختیاری خواندن/جست‌وجو/پیش‌نمایش؛ لینک بومی به جای استخراج رسانه. | `wellbeing/opengym.py`؛ نام ابزار از سرور واقعی و بازبینی خصوصی، نه حدس. نوشتن غیرفعال است. |
| [WHO PFA](https://www.who.int/publications-detail-redirect/9789241548205)، [NIDDK portions](https://www.niddk.nih.gov/health-information/weight-management/just-enough-food-portions) | حمایت عملی و شنیدن؛ ثبت غذا همراه عدم قطعیت مقدار. | `skills/wellbeing-emotional-support/SKILL.md` و `skills/wellbeing-meal-intake/SKILL.md`؛ این منابع شاهد اثربخشی درمانی AI یا دقت کالری عکس نیستند. |

## قالب واقعی Health و هویت رکورد

[metrics](https://help.healthyapps.dev/en/health-auto-export/export-format/health-metrics/) دارای name/units/data است؛ [workouts](https://help.healthyapps.dev/en/health-auto-export/export-format/workouts/) زمان، مدت و گاهی ID دارد؛ وزنه/تکرار از وجود workout استنتاج نمی‌شود. دسته‌های دیگر: [symptoms](https://help.healthyapps.dev/en/health-auto-export/export-format/symptoms/)، [cycleTracking](https://help.healthyapps.dev/en/health-auto-export/export-format/cycle-tracking/)، [ecg](https://help.healthyapps.dev/en/health-auto-export/export-format/ecg/)، [medications](https://help.healthyapps.dev/en/health-auto-export/export-format/medications/)، [stateOfMind](https://help.healthyapps.dev/en/health-auto-export/export-format/state-of-mind/) و [heartRateNotifications](https://help.healthyapps.dev/en/health-auto-export/export-format/heart-rate-notifications/).

`wellbeing/hae.py` جمعِ `heartRateNotifications` روی سیم را پیش از مجوز/هویت به دستهٔ داخلی مفرد `heartRateNotification` تبدیل می‌کند؛ datatype لینک نیز مفرد است. wrapper پشتیبانی‌شده `data` است؛ فرم bare قبلی هم پذیرفته می‌شود. کلید ناشناخته خطاست، نه دادهٔ نادیده‌گرفته‌شده. دو alias یکسان dedupe می‌شوند؛ تعارض یک هویت در همان درخواست کل تراکنش را رد می‌کند.

`id`/`uuid` واقعی اولویت دارد. fallback رکورد تاریخ‌دار از زمان/منبع/name استفاده می‌کند؛ برای دارو displayText/nickname/codings و برای اعلان heartNotification اضافه می‌شود. مقدار، dosage/status و threshold هویت نیستند و اصلاحشان revision می‌سازد. تغییر زمان/منبع/توصیف بدون ID پایدار ممکن است رکورد تازه بسازد؛ رویدادهای هم‌زمان غیرقابل‌تمایز ابهام دارند. رکورد بی‌زمان از محتوا هویت می‌گیرد. مهاجرت/ادغام شناسه‌های قدیمی خودکار نیست. فاصله پیش از offset عددی پذیرفته می‌شود؛ زمان فاقد timezone یا نامعتبر، unknown می‌ماند، نه زمان دریافت یا epoch تو‌در‌تو.

## اقتباس معماری ECC و V2

شناسه‌های زیر منابع مجازِ بستهٔ تأمین‌شده‌اند؛ متن خام خصوصی بازنشر نمی‌شود. V2 پیشنهاد آزمایشگاهی است، نه سیاست مصوب شرکت.

| مرجع تأمین‌شده | مکانیزم انتخابی و اتصال واقعی | چیزی که ادعا نمی‌شود |
|---|---|---|
| ECC `agents/architect.md` | جداسازی storage/service/transport در [database](../../wellbeing/database.py)، [service](../../wellbeing/service.py)، [API](../../wellbeing/api.py)؛ مرز اختیاری [OpenGym](../../wellbeing/opengym.py) | نیاز فعلی به microservices، Redis یا نقش نرم‌افزاری در تیم سلامت |
| V2 `method/skills/delivery-method/SKILL.md` | ورودی کوتاه README→INSTALL و بارگیری انتخابی `skills/`؛ قرارداد هدف/حدود/پذیرش در task | نصب متد مرکزی یا دستورهای آن در حساب میزبان |
| V2 `method/guides/memory.md` | تراکنش SQLite، revision، رسید و ادامه از واقعیت جاری؛ `Service.status/tasks/records` | CAS عمومی، event sourcing کامل، hash approval یا sync چندرایانه‌ای؛ اینها در MVP حاضر پیاده نشده‌اند |
| V2 `method/guides/verify-close.md` و ECC `skills/verification-loop/SKILL.md` | شاهد همان نسخه، آزمون منفی مجوز، جداسازی fixture/محلی/دستگاه در [پذیرش](ACCEPTANCE-FA.md) | pass همگانی، پوشش ۸۰٪، lint/typecheck یا hooks اجراشده بدون خروجی واقعی |

حافظه و محتوای ابزار خارجی شاهدند، نه منشأ اختیار. هیچ global hook، observer یا تنظیم حسابی از این مراجع وارد نمی‌شود. ردپای ادامهٔ توسعه در `.second-brain/entries/` عمومی و بدون دادهٔ شرکت‌کننده است؛ حافظهٔ خصوصی محصول SQLite جداگانه می‌ماند.
