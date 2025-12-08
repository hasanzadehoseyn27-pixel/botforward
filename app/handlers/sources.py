# app/handlers/sources.py
from telegram import Update
from telegram.ext import (
    ConversationHandler,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)
from app.keyboards.keyboards import source_menu_keyboard, cancel_keyboard, main_menu_keyboard
from app.database import Database

db = Database()

# States
WAITING_SOURCE = 0
WAITING_SOURCE_REMOVE = 1

async def manage_sources(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت مبداها"""
    await update.message.reply_text(
        "📤 مدیریت مبداها:\n"
        "یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=source_menu_keyboard()
    )

async def add_source_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع افزودن مبدا"""
    await update.message.reply_text(
        "➕ افزودن مبدا جدید:\n\n"
        "لطفاً Chat ID کانال یا گروه مبدا را ارسال کنید:\n"
        "(مثال: -1001234567890)\n\n"
        "برای لغو روی دکمه لغو بزنید.",
        reply_markup=cancel_keyboard()
    )
    return WAITING_SOURCE

async def receive_source(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت Chat ID مبدا"""
    chat_id = update.message.text.strip()
    
    if not chat_id.lstrip('-').isdigit():
        await update.message.reply_text(
            "❌ فرمت Chat ID اشتباه است!\n"
            "Chat ID باید عدد باشد (مثال: -1001234567890)",
            reply_markup=cancel_keyboard()
        )
        return WAITING_SOURCE
    
    if db.add_source(chat_id):
        await update.message.reply_text(
            f"✅ مبدا با Chat ID زیر با موفقیت اضافه شد:\n`{chat_id}`",
            parse_mode='Markdown',
            reply_markup=source_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ این مبدا قبلاً اضافه شده است!",
            reply_markup=source_menu_keyboard()
        )
    
    return ConversationHandler.END

async def list_sources(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست مبداها"""
    sources = db.get_sources()
    if sources:
        text = "📜 لیست مبداها:\n\n"
        
        for idx, source in enumerate(sources, 1):
            # دریافت اطلاعات کانال
            try:
                chat = await context.bot.get_chat(source)
                chat_name = chat.title if chat.title else f"کانال {idx}"
                chat_link = f"https://t.me/{chat.username}" if chat.username else None
                
                if chat_link:
                    text += f"{idx}. [{chat_name}]({chat_link})\n"
                else:
                    text += f"{idx}. {chat_name}\n"
            except:
                text += f"{idx}. `{source}`\n"
    else:
        text = "❌ هیچ مبدایی تعریف نشده است!"
    
    await update.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=source_menu_keyboard(),
        disable_web_page_preview=True
    )

async def remove_source_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع حذف مبدا"""
    sources = db.get_sources()
    if sources:
        text = "➖ حذف مبدا:\n\n"
        text += "لیست مبداها:\n"
        for idx, source in enumerate(sources, 1):
            text += f"{idx}. `{source}`\n"
        text += "\nChat ID مبدایی که می‌خواهید حذف کنید را ارسال کنید:"
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=cancel_keyboard()
        )
        return WAITING_SOURCE_REMOVE
    else:
        await update.message.reply_text(
            "❌ هیچ مبدایی برای حذف وجود ندارد!",
            reply_markup=source_menu_keyboard()
        )
        return ConversationHandler.END

async def receive_source_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت Chat ID مبدا برای حذف"""
    chat_id = update.message.text.strip()
    
    if db.remove_source(chat_id):
        await update.message.reply_text(
            f"✅ مبدا با Chat ID زیر حذف شد:\n`{chat_id}`",
            parse_mode='Markdown',
            reply_markup=source_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ این مبدا یافت نشد!",
            reply_markup=source_menu_keyboard()
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

def sources_handlers():
    """بازگشت لیست handler های مبدا"""
    # Handler برای منوی مبداها
    sources_menu_handler = MessageHandler(filters.Regex("^📤 تعیین مبدا$"), manage_sources)
    list_sources_handler = MessageHandler(filters.Regex("^📜 لیست مبدا$"), list_sources)
    
    # ConversationHandler برای افزودن مبدا
    add_source_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ افزودن مبدا$"), add_source_start)],
        states={
            WAITING_SOURCE: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^❌ لغو$"), receive_source)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Regex("^❌ لغو$"), cancel)
        ],
        per_message=False,
        per_chat=True,
        per_user=True
    )
    
    # ConversationHandler برای حذف مبدا
    remove_source_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➖ حذف مبدا$"), remove_source_start)],
        states={
            WAITING_SOURCE_REMOVE: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^❌ لغو$"), receive_source_remove)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Regex("^❌ لغو$"), cancel)
        ],
        per_message=False,
        per_chat=True,
        per_user=True
    )
    
    return [sources_menu_handler, list_sources_handler, add_source_conv, remove_source_conv]
