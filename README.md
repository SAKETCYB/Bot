
# RoastMate - Telegram Bot (Render-ready)

این بسته شامل یک ربات تلگرام است که ویژگی‌های زیر را دارد:
- جوین اجباری (کاربر باید عضو کانال شود)
- سیستم پرمیوم با قیمت 20,000 تومان
- خرید از طریق زرین‌پال (merchant_id در ENV تنظیم شود)
- کد هدیه یک‌بار مصرف ساخته‌شده توسط مدیر (/makecode)
- پنل مدیریتی ساده از طریق دستورات ربات
- مناسب برای دپلوی روی Render (یا هر جا که python اجرا شود)

## فایل‌ها
- bot.py : کد اصلی (aiogram + Flask برای callback)
- db.json : دیتابیس ساده JSON برای کاربران
- codes.json : کدهای هدیه
- requirements.txt : پکیج‌های لازم

## نحوه‌ی استفاده (Render)
1. ریپوی گیت‌هاب بساز و این فایل‌ها را داخلش قرار بده.
2. ساخت سرویس Web Service در Render و اتصال به ریپو.
3. Environment Variables لازم (در بخش Environment) را تنظیم کن:
   - BOT_TOKEN = توکن ربات تلگرام
   - ADMIN_ID = شناسه عددی مدیر (مثلاً 123456789)
   - MERCHANT_ID = 7b8436b7-5905-494a-892a-4cb9cc03840b
   - CHANNEL_USERNAME = @YourChannel
   - BASE_URL = https://your-render-app.onrender.com (آدرس سرویس در Render)
   - PREMIUM_PRICE_TOMAN = 20000
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `python bot.py`
6. در Render، Port به صورت ENV متغیر PORT در دسترس است و Flask این پورت را استفاده خواهد کرد.

## نحوه پرداخت و فعال‌سازی
- کاربر /buy را می‌زند، ربات یک لینک پرداخت زرین‌پال می‌سازد و می‌فرستد.
- پس از پرداخت، زرین‌پال کاربر را به `BASE_URL/verify?uid=<tg_id>&Authority=...&Status=OK` ریدایرکت می‌کند.
- صفحه‌ی verify در سرور وضعیت پرداخت را بررسی می‌کند و در صورت موفقیت، اشتراک کاربر فعال می‌شود.

## نکات امنیتی و عملیاتی
- لطفاً `BOT_TOKEN` و `MERCHANT_ID` و `ADMIN_ID` را در محیط (Environment Variables) نگه دارید — هرگز در گیت عمومی قرار ندهید.
- این پروژه برای MVP است. در production بهتر است از دیتابیس واقعی (Postgres) و وب‌سرور مناسب استفاده شود.
- در صورت فعال کردن حالت فوش، مسئولیت محتوای تولیدی با مدیر است — از قوانین محتوایی تلگرام پیروی کن.
