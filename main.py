import asyncio
import sys
sys.path.append('app')

from config import SUPER_ADMIN_ID
from database.db import Database


def main():
    print("✅ شروع راه‌اندازی ربات...")
    
    # ایجاد دیتابیس و اضافه کردن SUPER ADMIN
    db = Database()
    
    # 🔥 اضافه کردن SUPER ADMIN اگر وجود نداشته باشد
    if not db.is_admin(SUPER_ADMIN_ID):
        db.add_admin(SUPER_ADMIN_ID, username="SUPER_ADMIN", first_name="Super Admin")
        print(f"✅ SUPER ADMIN با ID {SUPER_ADMIN_ID} اضافه شد!")
    else:
        print(f"✅ SUPER ADMIN با ID {SUPER_ADMIN_ID} قبلاً موجود است!")
    
    # اجرای ربات از bot.py
    from app.bot import main as bot_main
    bot_main()


if __name__ == "__main__":
    try:
        print("✅ همه چیز آماده است! منتظر پیام‌ها...")
        main()
    except Exception as e:
        print(f"❌ خطای بحرانی رخ داد!")
        print(f"📛 نوع خطا: {type(e).__name__}")
        print(f"💬 پیام خطا: {str(e)}")
        print(f"📋 جزئیات کامل خطا:\n{e}")
