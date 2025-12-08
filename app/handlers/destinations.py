# app/handlers/destinations.py
from telegram import Update
from telegram.ext import (
    ConversationHandler,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)
from app.keyboards.keyboards import destination_menu_keyboard, cancel_keyboard, main_menu_keyboard
from app.database import Database

db = Database()

# States
WAITING_DESTINATION = 0
WAITING_DESTINATION_REMOVE = 1

async def manage_destinations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت مقاصد"""
    await update.message.reply_text(
        "📥 مدیریت مقاصد:\n"
        "یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=destination_menu_keyboard()
    )

async def add_destination_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع افزودن مقصد"""
    await update.message.reply_text(
        "➕ افزودن مقصد جدید:\n\n"
        "لطفاً Chat ID کانال یا گروه مقصد را ارسال کنید:\n"
        "(مثال: -1001234567890)\n\n"
        "برای لغو روی دکمه لغو بزنید.",
        reply_markup=cancel_keyboard()
    )
    return WAITING_DESTINATION

async def receive_destination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت Chat ID مقصد"""
    chat_id = update.message.text.strip()
    
    if not chat_id.lstrip('-').isdigit():
        await update.message.reply_text(
            "❌ فرمت Chat ID اشتباه است!\n"
            "Chat ID باید عدد باشد (مثال: -1001234567890)",
            reply_markup=cancel_keyboard()
        )
        return WAITING_DESTINATION
    
    if db.add_destination(chat_id):
        await update.message.reply_text(
            f"✅ مقصد با Chat ID زیر با موفقیت اضافه شد:\n`{chat_id}`",
            parse_mode='Markdown',
            reply_markup=destination_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ این مقصد قبلاً اضافه شده است!",
            reply_markup=destination_menu_keyboard()
        )
    
    return ConversationHandler.END

async def list_destinations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست مقاصد"""
    destinations = db.get_destinations()
    if destinations:
        text = "📜 لیست مقاصد:\n\n"
        
        for idx, dest in enumerate(destinations, 1):
            # دریافت اطلاعات کانال
            try:
                chat = await context.bot.get_chat(dest)
                chat_name = chat.title if chat.title else f"کانال {idx}"
                chat_link = f"https://t.me/{chat.username}" if chat.username else None
                
                if chat_link:
                    text += f"{idx}. [{chat_name}]({chat_link})\n"
                else:
                    text += f"{idx}. {chat_name}\n"
            except:
                text += f"{idx}. `{dest}`\n"
    else:
        text = "❌ هیچ مقصدی تعریف نشده است!"
    
    await update.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=destination_menu_keyboard(),
        disable_web_page_preview=True
    )

async def remove_destination_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع حذف مقصد"""
    destinations = db.get_destinations()
    if destinations:
        text = "➖ حذف مقصد:\n\n"
        text += "لیست مقاصد:\n"
        for idx, dest in enumerate(destinations, 1):
            text += f"{idx}. `{dest}`\n"
        text += "\nChat ID مقصدی که می‌خواهید حذف کنید را ارسال کنید:"
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=cancel_keyboard()
        )
        return WAITING_DESTINATION_REMOVE
    else:
        await update.message.reply_text(
            "❌ هیچ مقصدی برای حذف وجود ندارد!",
            reply_markup=destination_menu_keyboard()
        )
        return ConversationHandler.END

async def receive_destination_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت Chat ID مقصد برای حذف"""
    chat_id = update.message.text.strip()
    
    if db.remove_destination(chat_id):
        await update.message.reply_text(
            f"✅ مقصد با Chat ID زیر حذف شد:\n`{chat_id}`",
            parse_mode='Markdown',
            reply_markup=destination_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ این مقصد یافت نشد!",
            reply_markup=destination_menu_keyboard()
        )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو عملیات"""
    from app.handlers.forwarding import is_forwarding
    await update.message.reply_text(
        "❌ عملیات لغو شد.",
        reply_markup=main_menu_keyboard(is_forwarding=is_forwarding)
    )
    return ConversationHandler.END

def destinations_handlers():
    """بازگشت لیست handler های مقصد"""
    destinations_menu_handler = MessageHandler(filters.Regex("^📥 تعیین مقصد$"), manage_destinations)
    list_destinations_handler = MessageHandler(filters.Regex("^📜 لیست مقصد$"), list_destinations)
    
    add_destination_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ افزودن مقصد$"), add_destination_start)],
        states={
            WAITING_DESTINATION: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^❌ لغو$"), receive_destination)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Regex("^❌ لغو$"), cancel)
        ],
        per_message=False,
        per_chat=True,
        per_user=True
    )
    
    remove_destination_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➖ حذف مقصد$"), remove_destination_start)],
        states={
            WAITING_DESTINATION_REMOVE: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^❌ لغو$"), receive_destination_remove)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Regex("^❌ لغو$"), cancel)
        ],
        per_message=False,
        per_chat=True,
        per_user=True
    )
    
    return [destinations_menu_handler, list_destinations_handler, add_destination_conv, remove_destination_conv]
