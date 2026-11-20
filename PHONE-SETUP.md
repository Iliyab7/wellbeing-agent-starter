# وصل کردن Apple Health به دات

اول یک نمونه بفرستیم تا دات همان فایل را باز کند و مثلاً قدم‌ها یا خواب ثبت‌شده را بخواند. روی آیفون این کار را یک بار انجام بده. دات تنظیم حساب و بررسی فایل دریافتی را از سمت خودش پیش می‌برد.

1. [Health Auto Export](https://apps.apple.com/us/app/health-auto-export-json-csv/id1115567069) را باز کن. برو به **Export → Automated → New Automation** و نوع را **Email** بگذار.
2. آدرس **همان Gmail خصوصی که دات به آن دسترسی خواندن دارد** را وارد کن. در **Subject Prefix** بنویس `[Wellbeing Health]`. در **Data Type**، گزینهٔ **Health Metrics** و سپس سنجه‌هایی را که می‌خواهی، مثل **Sleep Analysis** و **Step Count**، انتخاب کن. دسترسی Apple Health را برای همان موارد بده.
3. **JSON → Version 2**، بازهٔ **Default** و **Sync Frequency → Every 1 Day** را انتخاب کن. تنظیم را ذخیره کن و در حالت باز بودن قفل گوشی از **Manual Upload** یک بازهٔ کوتاه مثل دیروز را بفرست. دات پیام و محتوای پیوست را بررسی می‌کند. وقتی نمونه خوانده شد **Enabled** را برای ارسال‌های بعدی روشن کن. [راهنمای Email در Health Auto Export](https://help.healthyapps.dev/en/health-auto-export/automations/email/)

برای تمرین‌های ثبت‌شده، اگر می‌خواهی جزئیات Workout هم برسد، یک Automation دیگر با **Data Type → Workouts** و پیشوند `[Wellbeing Workouts]` بساز. گزینهٔ **Include Route Data** را فقط اگر می‌خواهی مسیرهای مکانی منتقل شوند روشن کن. شهر و مختصات برای شروع لازم نیست؛ دات زمان گزارش را با ساعت محلی‌ای که انتخاب کرده‌ای تنظیم می‌کند. داده‌هایی که اپل هلث دارد و مجوزشان را می‌دهی در خروجی می‌آیند. [فهرست داده‌های پشتیبانی‌شده](https://help.healthyapps.dev/en/health-auto-export/getting-started/supported-data/)

اگر Drive از قبل به دات وصل است و دات می‌تواند فایل را باز کند، نوع **Google** را انتخاب کن و فایل JSON را در پوشهٔ خصوصی `Wellbeing Intake` بگذار. اگر خواندن پیوست گیر کرد، همان یک فایل را از آیفون در چت خصوصی دات بارگذاری کن تا اولین گزارش معطل اتصال خودکار نماند. [راهنمای Google Drive](https://help.healthyapps.dev/en/health-auto-export/automations/google-drive/)

ارسال روزانه در Health Auto Export زمان تقریبی دارد. موقع خواندن Health گوشی باید باز باشد. برای اجرای دستی از ویجت **Automations** استفاده کن. اگر خواستی با ساعت، آلارم یا شارژر امتحان کنی، [چهار دستور ساخت شورتکات](docs/mvp/IOS-SHORTCUTS-FA.md) آماده‌اند. [محدودیت‌های اجرای خودکار](https://help.healthyapps.dev/en/health-auto-export/automations/)

اگر اپ برای قابلیت Automated صفحهٔ اشتراک نشان داد، شرایط آزمایش و قیمت همان App Store را ببین. برای اولین نمونه می‌توانی در **Export → Manual Export** یک JSON v2 بگیری و مستقیم در چت خصوصی دات بگذاری. [روش خروجی دستی](https://help.healthyapps.dev/en/health-auto-export/manual-export/)

عنوان پیشنهادی بالا برای تشخیص خروجی این ابزار است. فهرست پیام‌های ورودیِ پایش عمومی باید پیام‌های بدون پیوست و عنوان‌های دیگرِ داخل دامنهٔ مجاز را هم پوشش دهد.
