# app/handlers/start.py
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from app.keyboards.keyboards import main_menu_keyboard
from app.database import Database


db = Database()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /start"""
    user = update.effective_user
    user_id = user.id
    
    # بررسی ادمین بودن
    if not db.is_admin(user_id):
        await update.message.reply_text(
            f"❌ دسترسی غیرمجاز!\n\n"
            f"سلام {user.first_name}! 👋\n"
            f"شما به این ربات دسترسی ندارید.\n\n"
            f"🆔 User ID شما: `{user_id}`\n\n"
            f"برای دریافت دسترسی، این User ID را به ادمین ربات بدهید.",
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text(
        f"سلام {user.first_name}! 👋\n\n"
        "به ربات فوروارد خودکار خوش اومدی! 🚀\n"
        "از منوی زیر گزینه مورد نظرت رو انتخاب کن:",
        reply_markup=main_menu_keyboard(user_id=user_id)  # 🔥 ارسال user_id
    )


# ایجاد handler
start_handler = CommandHandler("start", start)
