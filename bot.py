import asyncio
import sqlite3

from aiogram import Bot, Dispatcher
from aiogram.types import Message

# ======================
# تنظیمات
# ======================

BOT_TOKEN = "8655104602:AAEcDgXuR6lY_FAjZg51pGWM_46RolcgQB4"
ADMIN_ID = 8107344396

# ======================
# راه‌اندازی
# ======================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ======================
# دیتابیس
# ======================

db = sqlite3.connect("data.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    admin_message_id INTEGER PRIMARY KEY,
    user_id INTEGER
)
""")

db.commit()

# ======================
# هندلر پیام‌ها
# ======================

@dp.message()
async def handle_message(message: Message):

    # پاسخ ادمین به کاربران
    if message.chat.id == ADMIN_ID:

        if not message.reply_to_message:
            return

        reply_id = message.reply_to_message.message_id

        cursor.execute(
            "SELECT user_id FROM messages WHERE admin_message_id=?",
            (reply_id,)
        )

        result = cursor.fetchone()

        if result:
            user_id = result[0]

            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=message.text
                )
            except:
                pass

        return

    # دریافت پیام کاربر

    copied = await bot.copy_message(
        chat_id=ADMIN_ID,
        from_chat_id=message.chat.id,
        message_id=message.message_id
    )

    cursor.execute(
        "INSERT OR REPLACE INTO messages VALUES (?, ?)",
        (copied.message_id, message.from_user.id)
    )

    db.commit()

    username = message.from_user.username

    if username:
        info = f"👤 @{username}"
    else:
        info = f"👤 {message.from_user.first_name}\n🆔 {message.from_user.id}"

    await bot.send_message(
        chat_id=ADMIN_ID,
        text=info,
        reply_to_message_id=copied.message_id
    )

# ======================
# اجرا
# ======================

async def main():
    print("Bot Started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
``
