# app/bot.py
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from config import BOT_TOKEN

# Import handlers با مسیر کامل
from app.handlers.start import start_handler
from app.handlers.sources import sources_handlers
from app.handlers.destinations import destinations_handlers
from app.handlers.posts import posts_handlers
from app.handlers.intervals import intervals_handlers
from app.handlers.forwarding import forwarding_handlers, channel_post_handler


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بازگشت به منوی اصلی"""
    from app.keyboards.keyboards import main_menu_keyboard
    
    await update.message.reply_text(
        "منوی اصلی:\n"
        "گزینه مورد نظر را انتخاب کنید:",
        reply_markup=main_menu_keyboard()
    )


def main():
    """راه‌اندازی ربات"""
    try:
        print("✅ شروع راه‌اندازی ربات...")
        
        # ساخت Application
        print("⏳ در حال ساخت Application...")
        application = Application.builder().token(BOT_TOKEN).build()
        print("✅ Application ساخته شد!")
        
        # اضافه کردن Handler ها
        print("⏳ در حال اضافه کردن Handler ها...")
        
        # دستور start
        application.add_handler(start_handler)
        
        # Handler بازگشت به منوی اصلی (با دکمه Reply Keyboard)
        application.add_handler(MessageHandler(filters.Regex("^🔙 بازگشت$"), back_to_main))
        
        # Handler های مبدا
        for handler in sources_handlers():
            application.add_handler(handler)
        
        # Handler های مقصد
        for handler in destinations_handlers():
            application.add_handler(handler)
        
        # Handler های پست‌ها
        for handler in posts_handlers():
            application.add_handler(handler)
        
        # Handler های زمان‌بندی
        for handler in intervals_handlers():
            application.add_handler(handler)
        
        # Handler های فوروارد
        for handler in forwarding_handlers():
            application.add_handler(handler)
        
        # Handler کانال پست
        application.add_handler(channel_post_handler)
        
        print("✅ تمام Handler ها اضافه شدند!")
        
        # راه‌اندازی ربات
        print("🤖 ربات در حال اجرا...")
        print("✅ همه چیز آماده است! منتظر پیام‌ها...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        print(f"\n❌ خطای بحرانی رخ داد!")
        print(f"📛 نوع خطا: {type(e).__name__}")
        print(f"💬 پیام خطا: {e}")
        print("\n📋 جزئیات کامل خطا:\n")
        import traceback
        traceback.print_exc()
