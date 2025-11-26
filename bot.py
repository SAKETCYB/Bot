#!/usr/bin/env python3
import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message
from aiogram.filters import Command
import json, requests, threading, time
from datetime import datetime, timedelta

# ---------------------------
# Configuration (ENV vars)
# ---------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN", "8570268104:AAFM1z5-gQ0f7cNlCGPLle4UOjyUBZMT6uQ")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8296875526"))  # your telegram id as integer
MERCHANT_ID = os.getenv("MERCHANT_ID", "7b8436b7-5905-494a-892a-4cb9cc03840b")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@aiogramnews")  # channel username or id like -100123...
BASE_URL = os.getenv("BASE_URL", "https://your-render-app.onrender.com")  # public URL for payment callback
PREMIUM_PRICE_TOMAN = int(os.getenv("PREMIUM_PRICE_TOMAN", "20000"))  # 20,000 by default

# ---------------------------
# Simple JSON DB helpers
# ---------------------------
DB_FILE = "db.json"
CODES_FILE = "codes.json"

def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

def load_codes():
    try:
        with open(CODES_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_codes(c):
    with open(CODES_FILE, "w") as f:
        json.dump(c, f, indent=2, ensure_ascii=False)

# ---------------------------
# Utilities
# ---------------------------
def is_premium(uid):
    db = load_db()
    s = db.get(str(uid))
    if not s: 
        return False
    exp = s.get("premium_until")
    if not exp:
        return False
    try:
        exp_dt = datetime.fromisoformat(exp)
        return exp_dt > datetime.utcnow()
    except Exception:
        return False

def add_premium(uid, days):
    db = load_db()
    now = datetime.utcnow()
    key = str(uid)
    cur = db.get(key)
    if cur and cur.get("premium_until"):
        try:
            cur_until = datetime.fromisoformat(cur["premium_until"])
        except Exception:
            cur_until = now
        new_until = max(now, cur_until) + timedelta(days=days)
    else:
        new_until = now + timedelta(days=days)
    db[key] = {"premium_until": new_until.isoformat()}
    save_db(db)

# ---------------------------
# Join-check decorator
# ---------------------------
async def is_member(bot: Bot, user_id: int):
    try:
        # CHANNEL_USERNAME can be '@channel' or '-100...' id; bot.get_chat_member supports both
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        # statuses: 'creator', 'administrator', 'member', 'restricted', 'left', 'kicked'
        return member.status in ("creator", "administrator", "member", "restricted")
    except Exception:
        return False

def require_join(handler):
    async def wrapper(message: Message):
        bot = message.bot
        ok = await is_member(bot, message.from_user.id)
        if not ok:
            await message.answer(f"❗ برای استفاده از ربات ابتدا باید در کانال ما عضو شوی:\n{CHANNEL_USERNAME}\n\nبعد دوباره امتحان کن.")
            return
        return await handler(message)
    return wrapper

# ---------------------------
# Bot setup
# ---------------------------
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Admin-only commands
@dp.message(Command(commands=["start"]))
async def cmd_start(message: Message):
    # auto create user row if not exist
    db = load_db()
    if str(message.from_user.id) not in db:
        db[str(message.from_user.id)] = {}
        save_db(db)
    txt = ("سلام! من RoastMate هستم — حاضرپاسخ شخصی تو 😎\n\n"
           "برای خرید پرمیوم: /buy\nبرای وارد کردن کد هدیه: redeem CODE\nبرای فعال کردن فوش: /toggle_fosh\n\n"
           "اگر مدیر هستی: /makecode 7")
    await message.answer(txt)

# Admin: make one-time code
@dp.message(Command(commands=["makecode"]))
async def cmd_makecode(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("فقط مدیر می‌تواند این دستور را اجرا کند.")
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("Usage: /makecode <days>\nمثال: /makecode 7")
        return
    try:
        days = int(parts[1])
    except:
        await message.reply("تعداد روز نامعتبر است.")
        return
    import random, string
    code = "GIFT-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    codes = load_codes()
    codes[code] = {"days": days, "used": False, "used_by": None, "created_by": str(message.from_user.id), "created_at": datetime.utcnow().isoformat()}
    save_codes(codes)
    await message.reply(f"🎁 کد ساخته شد:\n\n{code}\n\nمدت: {days} روز\nقابل استفاده: یک‌بار")

# Admin: list codes
@dp.message(Command(commands=["codes"]))
async def cmd_codes(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    codes = load_codes()
    if not codes:
        await message.reply("هیچ کدی ساخته نشده.")
        return
    out = "کدهای ساخته شده:\n\n"
    for k,v in codes.items():
        out += f"{k} — days: {v['days']} — used: {v['used']}\n"
    await message.reply(out)

# Admin: grant manually
@dp.message(Command(commands=["grant"]))
async def cmd_grant(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) < 3:
        await message.reply("Usage: /grant <tg_id> <days>")
        return
    try:
        tg = int(parts[1]); days = int(parts[2])
    except:
        await message.reply("پارامترها نامعتبر هستند.")
        return
    add_premium(tg, days)
    await message.reply(f"✅ به {tg} برای {days} روز اشتراک داده شد.")

# Admin: info
@dp.message(Command(commands=["info"]))
async def cmd_info(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("Usage: /info <tg_id>")
        return
    try:
        tg = int(parts[1])
    except:
        await message.reply("tg_id نامعتبر است.")
        return
    db = load_db()
    u = db.get(str(tg))
    await message.reply(f"اطلاعات: {u}")

# Redeem code (no need to be admin)
@dp.message(F.text.startswith("redeem "))
@require_join
async def redeem(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("فرمت: redeem CODE")
        return
    code = parts[1].strip()
    codes = load_codes()
    if code not in codes:
        await message.reply("❌ کد معتبر نیست.")
        return
    if codes[code]["used"]:
        await message.reply("❌ این کد قبلاً استفاده شده است.")
        return
    days = int(codes[code]["days"])
    uid = message.from_user.id
    add_premium(uid, days)
    codes[code]["used"] = True
    codes[code]["used_by"] = str(uid)
    codes[code]["used_at"] = datetime.utcnow().isoformat()
    save_codes(codes)
    await message.reply(f"🎉 اشتراک {days} روزه فعال شد!")

# Toggle fosh flag
@dp.message(Command(commands=["toggle_fosh"]))
@require_join
async def toggle_fosh(message: Message):
    db = load_db()
    u = db.get(str(message.from_user.id), {})
    cur = u.get("fosh_enabled", False)
    u["fosh_enabled"] = not cur
    db[str(message.from_user.id)] = u
    save_db(db)
    await message.reply(f"حالت فوش {'فعال' if not cur else 'غیرفعال'} شد.")

# Buy command - start Zarinpal payment (amount in Toman)
@dp.message(Command(commands=["buy"]))
@require_join
async def buy(message: Message):
    uid = message.from_user.id
    amount = PREMIUM_PRICE_TOMAN
    callback = f"{BASE_URL}/verify?uid={uid}"
    payload = {
        "merchant_id": MERCHANT_ID,
        "amount": amount,
        "callback_url": callback
    }
    try:
        r = requests.post("https://api.zarinpal.com/pg/v4/payment/request.json", json=payload, timeout=10).json()
        if r.get("data", {}).get("code") == 100:
            authority = r["data"]["authority"]
            link = f"https://www.zarinpal.com/pg/StartPay/{authority}"
            await message.reply(f"برای پرداخت {amount:,} تومان روی لینک زیر کلیک کن:\n{link}\n\nبعد از پرداخت، صفحه به سایت بازگردانده می‌شود و اشتراک شما فعال می‌شود.")
        else:
            await message.reply("❌ خطا در ایجاد پرداخت. لطفاً بعداً تلاش کن.")
    except Exception as e:
        await message.reply("❌ خطا در ارتباط با زرین‌پال.")

# Simple responses: free vs premium
@dp.message()
@require_join
async def responder(message: Message):
    txt = message.text or ""
    uid = message.from_user.id
    db = load_db()
    user = db.get(str(uid), {})
    fosh = user.get("fosh_enabled", False)
    if is_premium(uid):
        # Premium response (tougher)
        if fosh:
            resp = f"🔥 (پرمیوم فوش) پاسخ تو: {txt} — بیا ببینم کی جرئت داره باهات کل‌کل کنه 😏"
        else:
            resp = f"🔥 (پرمیوم) پاسخ تو: {txt} — جوابِ پرمیوم و مخصوصِ خودت!"
    else:
        resp = f"🙂 (رایگان) جوابِ ساده: {txt}\nبرای پرمیوم بزن /buy"
    await message.reply(resp)

# ---------------------------
# Small Flask app for verification callback
# ---------------------------
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/verify", methods=["GET", "POST"])
def verify():
    # Zarinpal redirects the user's browser to this URL with Authority & Status
    uid = request.args.get("uid")
    authority = request.args.get("Authority") or request.args.get("authority")
    status = request.args.get("Status") or request.args.get("status")
    if not uid or not authority:
        return "Invalid parameters", 400
    # If status is OK, call verify API
    if status and status.lower() == "ok":
        payload = {
            "merchant_id": MERCHANT_ID,
            "amount": PREMIUM_PRICE_TOMAN,
            "authority": authority
        }
        try:
            r = requests.post("https://api.zarinpal.com/pg/v4/payment/verify.json", json=payload, timeout=10).json()
            if r.get("data", {}).get("code") == 100 or r.get("data", {}).get("code") == 101:
                # payment successful
                try:
                    add_premium(int(uid), 30)  # give 30 days as example; you can customize mapping
                except:
                    pass
                return "<h3>پرداخت موفق بود. اشتراک شما فعال شد. می‌توانید ربات را ببندید و ادامه را در تلگرام ببینید.</h3>", 200
            else:
                return "<h3>پرداخت ناموفق یا نامعتبر.</h3>", 400
        except Exception as e:
            return "<h3>خطا هنگام بررسی پرداخت.</h3>", 500
    else:
        return "<h3>کاربر پرداخت را لغو کرد یا وضعیت نامشخص است.</h3>", 400

def run_flask():
    # Run Flask server on 0.0.0.0:10000 (Render gives public port via env PORT)
    port = int(os.getenv("PORT", "10000"))
    # Note: in Render you should expose $PORT. For local testing default 10000.
    app.run(host="0.0.0.0", port=port)

# ---------------------------
# Entrypoint
# ---------------------------
async def main():
    # Start Flask in a background thread so both bot polling and web server run
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    print("Starting RoastMate...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopping...")
