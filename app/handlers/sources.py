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
        "⚠️ توجه: ربات باید در کانال/گروه عضو باشد!\n\n"
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
    
    # بررسی دسترسی ربات به کانال
    try:
        chat = await context.bot.get_chat(chat_id)
        chat_name = chat.title if chat.title else "بدون نام"
        
        if db.add_source(chat_id):
            await update.message.reply_text(
                f"✅ مبدا با موفقیت اضافه شد:\n\n"
                f"📌 نام: {chat_name}\n"
                f"🆔 Chat ID: `{chat_id}`",
                parse_mode='Markdown',
                reply_markup=source_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ این مبدا قبلاً اضافه شده است!",
                reply_markup=source_menu_keyboard()
            )
    except Exception as e:
        await update.message.reply_text(
            f"❌ خطا در دسترسی به کانال!\n\n"
            f"احتمالاً:\n"
            f"• ربات عضو کانال نیست\n"
            f"• Chat ID اشتباه است\n"
            f"• کانال خصوصی است\n\n"
            f"Chat ID: `{chat_id}`\n"
            f"خطا: {str(e)[:100]}",
            parse_mode='Markdown',
            reply_markup=source_menu_keyboard()
        )
    
    return ConversationHandler.END

async def list_sources(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست مبداها"""
    sources = db.get_sources()
    
    if not sources:
        await update.message.reply_text(
            "❌ هیچ مبدایی تعریف نشده است!\n\n"
            "برای افزودن مبدا، روی دکمه «➕ افزودن مبدا» بزنید.",
            reply_markup=source_menu_keyboard()
        )
        return
    
    text = "📜 لیست مبداها:\n\n"
    
    for idx, source in enumerate(sources, 1):
        try:
            chat = await context.bot.get_chat(source)
            chat_name = chat.title if chat.title else "بدون نام"
            chat_username = chat.username if hasattr(chat, 'username') and chat.username else None
            
            if chat_username:
                # اگه یوزرنیم داره، لینک بده
                text += f"{idx}. [{chat_name}](https://t.me/{chat_username})\n"
                text += f"   🆔 `{source}`\n\n"
            else:
                # اگه یوزرنیم نداره، فقط اسم و آیدی
                text += f"{idx}. **{chat_name}**\n"
                text += f"   🆔 `{source}`\n\n"
        except Exception as e:
            # اگه دسترسی نداره، فقط Chat ID نشون بده
            text += f"{idx}. ⚠️ دسترسی ندارد\n"
            text += f"   🆔 `{source}`\n"
            text += f"   (ربات احتماً عضو کانال نیست)\n\n"
    
    await update.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=source_menu_keyboard(),
        disable_web_page_preview=True
    )

async def remove_source_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع حذف مبدا"""
    sources = db.get_sources()
    
    if not sources:
        await update.message.reply_text(
            "❌ هیچ مبدایی برای حذف وجود ندارد!",
            reply_markup=source_menu_keyboard()
        )
        return ConversationHandler.END
    
    text = "➖ حذف مبدا:\n\n"
    text += "📋 لیست مبداها:\n\n"
    
    for idx, source in enumerate(sources, 1):
        try:
            chat = await context.bot.get_chat(source)
            chat_name = chat.title if chat.title else "بدون نام"
            text += f"{idx}. {chat_name}\n"
            text += f"   🆔 `{source}`\n\n"
        except:
            text += f"{idx}. 🆔 `{source}`\n\n"
    
    text += "💬 Chat ID مبدایی که می‌خواهید حذف کنید را ارسال کنید:"
    
    await update.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=cancel_keyboard()
    )
    return WAITING_SOURCE_REMOVE

async def receive_source_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت Chat ID مبدا برای حذف"""
    chat_id = update.message.text.strip()
    
    if db.remove_source(chat_id):
        try:
            chat = await context.bot.get_chat(chat_id)
            chat_name = chat.title if chat.title else "بدون نام"
            await update.message.reply_text(
                f"✅ مبدا حذف شد:\n\n"
                f"📌 نام: {chat_name}\n"
                f"🆔 Chat ID: `{chat_id}`",
                parse_mode='Markdown',
                reply_markup=source_menu_keyboard()
            )
        except:
            await update.message.reply_text(
                f"✅ مبدا با Chat ID زیر حذف شد:\n`{chat_id}`",
                parse_mode='Markdown',
                reply_markup=source_menu_keyboard()
            )
    else:
        await update.message.reply_text(
            f"❌ این مبدا یافت نشد!\n\n"
            f"Chat ID وارد شده: `{chat_id}`",
            parse_mode='Markdown',
            reply_markup=source_menu_keyboard()
        )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو عملیات"""
    await update.message.reply_text(
        "❌ عملیات لغو شد.",
        reply_markup=main_menu_keyboard()
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
