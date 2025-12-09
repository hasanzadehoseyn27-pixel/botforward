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
        "⚠️ توجه: ربات باید در کانال/گروه Admin باشد!\n\n"
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
    
    # بررسی دسترسی ربات به کانال
    try:
        chat = await context.bot.get_chat(chat_id)
        chat_name = chat.title if chat.title else "بدون نام"
        
        if db.add_destination(chat_id):
            await update.message.reply_text(
                f"✅ مقصد با موفقیت اضافه شد:\n\n"
                f"📌 نام: {chat_name}\n"
                f"🆔 Chat ID: `{chat_id}`",
                parse_mode='Markdown',
                reply_markup=destination_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ این مقصد قبلاً اضافه شده است!",
                reply_markup=destination_menu_keyboard()
            )
    except Exception as e:
        await update.message.reply_text(
            f"❌ خطا در دسترسی به کانال!\n\n"
            f"احتمالاً:\n"
            f"• ربات Admin نیست\n"
            f"• Chat ID اشتباه است\n"
            f"• کانال خصوصی است\n\n"
            f"Chat ID: `{chat_id}`\n"
            f"خطا: {str(e)[:100]}",
            parse_mode='Markdown',
            reply_markup=destination_menu_keyboard()
        )
    
    return ConversationHandler.END

async def list_destinations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست مقاصد"""
    destinations = db.get_destinations()
    
    if not destinations:
        await update.message.reply_text(
            "❌ هیچ مقصدی تعریف نشده است!\n\n"
            "برای افزودن مقصد، روی دکمه «➕ افزودن مقصد» بزنید.",
            reply_markup=destination_menu_keyboard()
        )
        return
    
    text = "📜 لیست مقاصد:\n\n"
    
    for idx, dest in enumerate(destinations, 1):
        try:
            chat = await context.bot.get_chat(dest)
            chat_name = chat.title if chat.title else "بدون نام"
            chat_username = chat.username if hasattr(chat, 'username') and chat.username else None
            
            if chat_username:
                # اگه یوزرنیم داره، لینک بده
                text += f"{idx}. [{chat_name}](https://t.me/{chat_username})\n"
                text += f"   🆔 `{dest}`\n\n"
            else:
                # اگه یوزرنیم نداره، فقط اسم و آیدی
                text += f"{idx}. **{chat_name}**\n"
                text += f"   🆔 `{dest}`\n\n"
        except Exception as e:
            # اگه دسترسی نداره، فقط Chat ID نشون بده
            text += f"{idx}. ⚠️ دسترسی ندارد\n"
            text += f"   🆔 `{dest}`\n"
            text += f"   (ربات احتماً Admin نیست)\n\n"
    
    await update.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=destination_menu_keyboard(),
        disable_web_page_preview=True
    )

async def remove_destination_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع حذف مقصد"""
    destinations = db.get_destinations()
    
    if not destinations:
        await update.message.reply_text(
            "❌ هیچ مقصدی برای حذف وجود ندارد!",
            reply_markup=destination_menu_keyboard()
        )
        return ConversationHandler.END
    
    text = "➖ حذف مقصد:\n\n"
    text += "📋 لیست مقاصد:\n\n"
    
    for idx, dest in enumerate(destinations, 1):
        try:
            chat = await context.bot.get_chat(dest)
            chat_name = chat.title if chat.title else "بدون نام"
            text += f"{idx}. {chat_name}\n"
            text += f"   🆔 `{dest}`\n\n"
        except:
            text += f"{idx}. 🆔 `{dest}`\n\n"
    
    text += "💬 Chat ID مقصدی که می‌خواهید حذف کنید را ارسال کنید:"
    
    await update.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=cancel_keyboard()
    )
    return WAITING_DESTINATION_REMOVE

async def receive_destination_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت Chat ID مقصد برای حذف"""
    chat_id = update.message.text.strip()
    
    if db.remove_destination(chat_id):
        try:
            chat = await context.bot.get_chat(chat_id)
            chat_name = chat.title if chat.title else "بدون نام"
            await update.message.reply_text(
                f"✅ مقصد حذف شد:\n\n"
                f"📌 نام: {chat_name}\n"
                f"🆔 Chat ID: `{chat_id}`",
                parse_mode='Markdown',
                reply_markup=destination_menu_keyboard()
            )
        except:
            await update.message.reply_text(
                f"✅ مقصد با Chat ID زیر حذف شد:\n`{chat_id}`",
                parse_mode='Markdown',
                reply_markup=destination_menu_keyboard()
            )
    else:
        await update.message.reply_text(
            f"❌ این مقصد یافت نشد!\n\n"
            f"Chat ID وارد شده: `{chat_id}`",
            parse_mode='Markdown',
            reply_markup=destination_menu_keyboard()
        )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو عملیات"""
    await update.message.reply_text(
        "❌ عملیات لغو شد.",
        reply_markup=main_menu_keyboard()
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
