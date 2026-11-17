# پذیرش اصلاح قالب ورودی HAE

این سند مکمل محدودِ [پژوهش](research.md)، [نیازمندی‌ها](requirements.json) و [دستور تحویل](CLI-HANDOFF.md) است. مثال‌ها ساختگی‌اند و تاریخشان هنگام آزمون تازه می‌شود. کارگر تولید آرتیفکت هیچ آزمونی اجرا نکرده و فایل‌ها هنوز اعمال نشده‌اند؛ نتیجهٔ هر مورد فعلاً «اجرانشده» است.

| مورد | انتظار قابل بررسی | شاهد پیشنهادی |
|---|---|---|
| هشت آرایهٔ رسمی | metrics، workouts، symptoms، cycleTracking، ecg، medications، stateOfMind و heartRateNotifications واقعاً ذخیره و پس از بازگشایی SQLite خوانده شوند؛ هیچ نمونه به علت تاریخ قدیمی از آزمون حذف نشود. | `test_all_eight_official_wire_arrays_replay_and_restart` |
| تفاوت نام روی سیم و تنظیمات | مطابق [قالب رسمی اعلان ضربان](https://help.healthyapps.dev/en/health-auto-export/export-format/heart-rate-notifications/)، ورودی جمع به دستهٔ داخلی مفرد تبدیل شود؛ datatype لینک همچنان heartRateNotification باشد. | `test_notification_deep_link_datatype_remains_singular` و `test_http_plural_upload_readback_and_retry` |
| مجوز و نام مستعار | هر دو املای مفرد و جمع زیر همان مجوز باشند؛ ارسال هم‌زمان باعث دور زدن لغو مجوز یا ذخیرهٔ تکراری نشود. | آزمون‌های alias در `tests/test_hae_wire.py` |
| اتمی بودن | نسخه‌های یکسان یک رکورد در دو نام، یک ذخیره داشته باشند؛ نسخه‌های متعارض کل درخواست را رد کنند، بدون تغییر رکورد قبلی یا ثبت رسید موفق. | `test_alias_conflicts_are_atomic_and_do_not_record_receipt` |
| دارو و اعلان هم‌زمان | دو داروی متفاوت در یک زمان و دو نوع اعلان در یک زمان چهار رکورد مستقل داشته باشند؛ تغییر مقدار دارو، وضعیت یا آستانه، نسخهٔ همان رکورد را اصلاح کند. | `test_simultaneous_medications_and_notification_types_then_corrections` بر اساس [قالب دارو](https://help.healthyapps.dev/en/health-auto-export/export-format/medications/) |
| زمان نامعلوم | قالب دارای فاصله پیش از ‎+0330 به UTC تبدیل شود؛ زمان غایب یا فاقد منطقهٔ زمانی از زمان دریافت یا دادهٔ تو‌در‌تو حدس زده نشود. | `test_missing_or_naive_event_is_unknown_not_nested_or_receipt_time` |
| دستهٔ ناشناخته | کلید ناشناخته، حتی در کنار دادهٔ معتبر، خطا بدهد؛ پاسخ HTTP برابر 422 باشد و ذخیرهٔ جزئی رخ ندهد. | آزمون‌های unknown در `tests/test_hae_wire.py` |
| محدودیت نقش‌ها | intake همچنان فقط ورودی بدهد، analyst نتواند ورودی سلامت بنویسد و companion فقط دستهٔ مجاز خود را بخواند. | `test_all_eight_official_wire_arrays_replay_and_restart` و آزمون‌های موجود MVP |

هویت جایگزین تضمین صادرکننده نیست. بدون id یا uuid پایدار، تغییر زمان رویداد، منبع یا توصیف‌های هویتی دارو/نوع اعلان قابل تطبیق خودکار با رکورد قبلی نیست. دو رویداد غیرقابل‌تمایز هم‌زمان ممکن است همان هویت را داشته باشند؛ تعارض در یک درخواست باید خطا بدهد. برای دادهٔ بدون زمان و بدون شناسه، تغییر محتوا لزوماً اصلاح همان رکورد شناخته نمی‌شود. شناسه‌های قدیمی SQLite مهاجرت یا ادغام خودکار نمی‌شوند؛ تطبیق احتمالی به بررسی مجاز و صریح نیاز دارد.

پس از اعمال، هماهنگ‌کننده باید `python -m unittest discover -s tests -v`، `python scripts/demo.py`، `python scripts/mvp_smoke.py`، `python scripts/build_release.py` و `python scripts/validate_package.py` را اجرا و شکست‌ها و موارد ردشده از اجرا را ثبت کند. آزمون HTTP پیشنهادی از TestClient و اجرای درون‌فرایندی استفاده می‌کند؛ این شاهد TCP، HTTPS عمومی یا گوشی نیست. عبور گزارش‌شدهٔ نسخهٔ قبلی از ۹۲ آزمون و smoke نیز اصلاح حاضر را تأیید نمی‌کند. پذیرش واقعی آیفون، HAE، میزبان و کانال ارسال همچنان به اجرای جداگانه و رسید واقعی نیاز دارد.
