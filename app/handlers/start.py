# app/handlers/start.py
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from app.keyboards.keyboards import main_menu_keyboard

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /start"""
    from app.handlers.forwarding import is_forwarding
    
    user = update.effective_user
    await update.message.reply_text(
        f"سلام {user.first_name}! 👋\n\n"
        "به ربات فوروارد خودکار خوش اومدی! 🚀\n"
        "از منوی زیر گزینه مورد نظرت رو انتخاب کن:",
        reply_markup=main_menu_keyboard(is_forwarding=is_forwarding)
    )

# ایجاد handler
start_handler = CommandHandler("start", start)
