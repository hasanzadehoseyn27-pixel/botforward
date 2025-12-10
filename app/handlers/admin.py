# app/handlers/admin.py
from telegram import Update
from telegram.ext import (
    ConversationHandler,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)
from app.keyboards.keyboards import admin_panel_keyboard, cancel_keyboard, main_menu_keyboard
from app.database import Database

db = Database()

# States
WAITING_ADMIN_ID = 0
WAITING_ADMIN_REMOVE = 1

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پنل مدیریت"""
    user_id = update.effective_user.id
    
    # بررسی ادمین بودن
    if not db.is_admin(user_id):
        await update.message.reply_text(
            "❌ شما دسترسی به پنل مدیریت ندارید!",
            reply_markup=main_menu_keyboard()
        )
        return
    
    await update.message.reply_text(
        "👑 پنل مدیریت:\n"
        "یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=admin_panel_keyboard()
    )

async def add_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع افزودن ادمین"""
    user_id = update.effective_user.id
    
    if not db.is_admin(user_id):
        await update.message.reply_text(
            "❌ شما دسترسی به این بخش ندارید!",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "➕ افزودن ادمین جدید:\n\n"
        "لطفاً User ID کاربر را ارسال کنید:\n"
        "(مثال: 123456789)\n\n"
        "💡 کاربر می‌تواند User ID خود را از ربات @userinfobot دریافت کند.\n\n"
        "برای لغو روی دکمه لغو بزنید.",
        reply_markup=cancel_keyboard()
    )
    return WAITING_ADMIN_ID

async def receive_admin_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت User ID ادمین"""
    admin_id = update.message.text.strip()
    
    if not admin_id.isdigit():
        await update.message.reply_text(
            "❌ فرمت User ID اشتباه است!\n"
            "User ID باید عدد باشد (مثال: 123456789)",
            reply_markup=cancel_keyboard()
        )
        return WAITING_ADMIN_ID
    
    # دریافت اطلاعات کاربر
    try:
        user = await context.bot.get_chat(admin_id)
        username = user.username if hasattr(user, 'username') and user.username else "بدون یوزرنیم"
        first_name = user.first_name if user.first_name else "بدون نام"
        
        if db.add_admin(admin_id, username, first_name):
            await update.message.reply_text(
                f"✅ ادمین با موفقیت اضافه شد:\n\n"
                f"👤 نام: {first_name}\n"
                f"🆔 یوزرنیم: @{username}\n"
                f"🔢 User ID: `{admin_id}`",
                parse_mode='Markdown',
                reply_markup=admin_panel_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ این کاربر قبلاً ادمین است!",
                reply_markup=admin_panel_keyboard()
            )
    except Exception as e:
        await update.message.reply_text(
            f"⚠️ هشدار: ادمین اضافه شد اما اطلاعات کاربر قابل دسترسی نیست.\n\n"
            f"User ID: `{admin_id}`\n\n"
            f"کاربر باید حداقل یکبار ربات را /start کرده باشد.",
            parse_mode='Markdown',
            reply_markup=admin_panel_keyboard()
        )
        db.add_admin(admin_id, None, None)
    
    return ConversationHandler.END

async def list_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست ادمین‌ها"""
    user_id = update.effective_user.id
    
    if not db.is_admin(user_id):
        await update.message.reply_text(
            "❌ شما دسترسی به این بخش ندارید!",
            reply_markup=main_menu_keyboard()
        )
        return
    
    admins = db.get_admins()
    
    if not admins:
        await update.message.reply_text(
            "❌ هیچ ادمینی تعریف نشده است!\n\n"
            "برای افزودن ادمین، روی دکمه «➕ افزودن ادمین» بزنید.",
            reply_markup=admin_panel_keyboard()
        )
        return
    
    text = "📜 لیست ادمین‌ها:\n\n"
    
    for idx, (user_id_db, username, first_name, added_date) in enumerate(admins, 1):
        name = first_name if first_name else "بدون نام"
        user_tag = f"@{username}" if username else "بدون یوزرنیم"
        
        text += f"{idx}. **{name}** ({user_tag})\n"
        text += f"   🔢 User ID: `{user_id_db}`\n"
        text += f"   📅 تاریخ: {added_date[:10]}\n\n"
    
    await update.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=admin_panel_keyboard()
    )

async def remove_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع حذف ادمین"""
    user_id = update.effective_user.id
    
    if not db.is_admin(user_id):
        await update.message.reply_text(
            "❌ شما دسترسی به این بخش ندارید!",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    admins = db.get_admins()
    
    if not admins:
        await update.message.reply_text(
            "❌ هیچ ادمینی برای حذف وجود ندارد!",
            reply_markup=admin_panel_keyboard()
        )
        return ConversationHandler.END
    
    if len(admins) == 1:
        await update.message.reply_text(
            "❌ نمی‌توانید آخرین ادمین را حذف کنید!\n"
            "حداقل یک ادمین باید وجود داشته باشد.",
            reply_markup=admin_panel_keyboard()
        )
        return ConversationHandler.END
    
    text = "➖ حذف ادمین:\n\n"
    text += "📋 لیست ادمین‌ها:\n\n"
    
    for idx, (user_id_db, username, first_name, added_date) in enumerate(admins, 1):
        name = first_name if first_name else "بدون نام"
        user_tag = f"@{username}" if username else "بدون یوزرنیم"
        text += f"{idx}. {name} ({user_tag})\n"
        text += f"   🔢 `{user_id_db}`\n\n"
    
    text += "💬 User ID ادمینی که می‌خواهید حذف کنید را ارسال کنید:"
    
    await update.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=cancel_keyboard()
    )
    return WAITING_ADMIN_REMOVE

async def receive_admin_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت User ID ادمین برای حذف"""
    admin_id = update.message.text.strip()
    user_id = update.effective_user.id
    
    # جلوگیری از حذف خودش
    if admin_id == str(user_id):
        await update.message.reply_text(
            "❌ شما نمی‌توانید خودتان را از لیست ادمین‌ها حذف کنید!",
            reply_markup=admin_panel_keyboard()
        )
        return ConversationHandler.END
    
    if db.remove_admin(admin_id):
        await update.message.reply_text(
            f"✅ ادمین با User ID زیر حذف شد:\n`{admin_id}`",
            parse_mode='Markdown',
            reply_markup=admin_panel_keyboard()
        )
    else:
        await update.message.reply_text(
            f"❌ این User ID در لیست ادمین‌ها یافت نشد!\n\n"
            f"User ID وارد شده: `{admin_id}`",
            parse_mode='Markdown',
            reply_markup=admin_panel_keyboard()
        )
    
    return ConversationHandler.END

async def bot_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار ربات"""
    user_id = update.effective_user.id
    
    if not db.is_admin(user_id):
        await update.message.reply_text(
            "❌ شما دسترسی به این بخش ندارید!",
            reply_markup=main_menu_keyboard()
        )
        return
    
    # آمارگیری
    sources = db.get_sources()
    destinations = db.get_destinations()
    active_posts = db.get_active_posts()
    inactive_posts = db.get_inactive_posts()
    admin_count = db.get_admin_count()
    interval, interval_type = db.get_forward_interval()
    
    type_fa = {"second": "ثانیه", "minute": "دقیقه", "hour": "ساعت"}
    
    from app.handlers.forwarding import is_forwarding
    forward_status = "✅ فعال" if is_forwarding else "❌ غیرفعال"
    
    text = "📊 آمار ربات:\n\n"
    text += f"👥 تعداد ادمین‌ها: {admin_count}\n"
    text += f"📤 تعداد مبداها: {len(sources)}\n"
    text += f"📥 تعداد مقاصد: {len(destinations)}\n"
    text += f"📗 پست‌های فعال: {len(active_posts)}\n"
    text += f"📕 پست‌های غیرفعال: {len(inactive_posts)}\n"
    text += f"⏰ زمان فوروارد: هر {interval} {type_fa[interval_type]}\n"
    text += f"🔄 وضعیت فوروارد: {forward_status}\n"
    
    await update.message.reply_text(
        text,
        reply_markup=admin_panel_keyboard()
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو عملیات"""
    await update.message.reply_text(
        "❌ عملیات لغو شد.",
        reply_markup=main_menu_keyboard()
    )
    return ConversationHandler.END

def admin_handlers():
    """بازگشت لیست handler های پنل مدیریت"""
    # Handler برای منوی پنل
    admin_panel_handler = MessageHandler(filters.Regex("^👑 پنل مدیریت$"), admin_panel)
    list_admins_handler = MessageHandler(filters.Regex("^📜 لیست ادمین‌ها$"), list_admins)
    bot_stats_handler = MessageHandler(filters.Regex("^📊 آمار ربات$"), bot_stats)
    
    # ConversationHandler برای افزودن ادمین
    add_admin_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ افزودن ادمین$"), add_admin_start)],
        states={
            WAITING_ADMIN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^❌ لغو$"), receive_admin_id)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Regex("^❌ لغو$"), cancel)
        ],
        per_message=False,
        per_chat=True,
        per_user=True
    )
    
    # ConversationHandler برای حذف ادمین
    remove_admin_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➖ حذف ادمین$"), remove_admin_start)],
        states={
            WAITING_ADMIN_REMOVE: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^❌ لغو$"), receive_admin_remove)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Regex("^❌ لغو$"), cancel)
        ],
        per_message=False,
        per_chat=True,
        per_user=True
    )
    
    return [admin_panel_handler, list_admins_handler, bot_stats_handler, add_admin_conv, remove_admin_conv]
