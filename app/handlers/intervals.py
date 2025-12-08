# app/handlers/intervals.py
from telegram import Update
from telegram.ext import (
    ConversationHandler,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)
from app.keyboards.keyboards import send_mode_menu_keyboard, cancel_keyboard, main_menu_keyboard
from app.database import Database
import asyncio

db = Database()

# State
WAITING_INTERVAL_VALUE = 0

async def send_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منوی حالت ارسال"""
    from app.handlers.forwarding import is_forwarding
    
    await update.message.reply_text(
        "⏰ حالت ارسال:\n"
        "نوع بازه زمانی را انتخاب کنید:",
        reply_markup=send_mode_menu_keyboard(is_forwarding=is_forwarding)
    )

async def select_interval_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """انتخاب نوع بازه زمانی"""
    text = update.message.text
    
    if "ثانیه" in text:
        interval_type = "second"
        type_fa = "ثانیه"
    elif "دقیقه" in text:
        interval_type = "minute"
        type_fa = "دقیقه"
    elif "ساعت" in text:
        interval_type = "hour"
        type_fa = "ساعت"
    else:
        return ConversationHandler.END
    
    context.user_data['interval_type'] = interval_type
    
    await update.message.reply_text(
        f"⏱ تنظیم زمان به {type_fa}:\n\n"
        f"لطفاً تعداد {type_fa} را وارد کنید:\n"
        "(مثال: 5)",
        reply_markup=cancel_keyboard()
    )
    return WAITING_INTERVAL_VALUE

async def receive_interval_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت مقدار زمان فوروارد"""
    import app.handlers.forwarding as forwarding_module
    
    value = update.message.text.strip()
    
    if not value.isdigit() or int(value) <= 0:
        await update.message.reply_text(
            "❌ لطفاً یک عدد معتبر وارد کنید! (مثال: 5)",
            reply_markup=cancel_keyboard()
        )
        return WAITING_INTERVAL_VALUE
    
    interval_type = context.user_data.get('interval_type', 'second')
    db.set_forward_interval(int(value), interval_type)
    
    type_fa = {"second": "ثانیه", "minute": "دقیقه", "hour": "ساعت"}
    
    await update.message.reply_text(
        f"✅ زمان فوروارد به هر {value} {type_fa[interval_type]} یکبار تنظیم شد!",
        reply_markup=send_mode_menu_keyboard(is_forwarding=forwarding_module.is_forwarding)
    )
    
    # راه‌اندازی مجدد فوروارد در صورت فعال بودن
    if forwarding_module.is_forwarding and forwarding_module.forwarding_task:
        forwarding_module.forwarding_task.cancel()
        forwarding_module.forwarding_task = asyncio.create_task(forwarding_module.forward_loop(context.application))
    
    return ConversationHandler.END

async def show_current_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش زمان فعلی"""
    from app.handlers.forwarding import is_forwarding
    
    interval, interval_type = db.get_forward_interval()
    type_fa = {"second": "ثانیه", "minute": "دقیقه", "hour": "ساعت"}
    
    await update.message.reply_text(
        f"⏰ زمان فعلی: هر {interval} {type_fa[interval_type]} یکبار",
        reply_markup=send_mode_menu_keyboard(is_forwarding=is_forwarding)
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو عملیات"""
    await update.message.reply_text(
        "❌ عملیات لغو شد.",
        reply_markup=main_menu_keyboard()
    )
    return ConversationHandler.END

def intervals_handlers():
    """بازگشت لیست handler های زمان‌بندی"""
    send_mode_handler = MessageHandler(filters.Regex("^⏰ حالت ارسال$"), send_mode)
    current_interval_handler = MessageHandler(filters.Regex("^📊 زمان کنونی$"), show_current_interval)
    
    interval_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^⏱ ثانیه‌ای$"), select_interval_type),
            MessageHandler(filters.Regex("^⏲ دقیقه‌ای$"), select_interval_type),
            MessageHandler(filters.Regex("^⏰ ساعتی$"), select_interval_type)
        ],
        states={
            WAITING_INTERVAL_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^❌ لغو$"), receive_interval_value)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Regex("^❌ لغو$"), cancel)
        ],
        per_message=False,
        per_chat=True,
        per_user=True
    )
    
    return [send_mode_handler, current_interval_handler, interval_conv]
