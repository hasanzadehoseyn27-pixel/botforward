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
from config import SUPER_ADMIN_ID


db = Database()


# States برای ConversationHandler
WAITING_ADMIN_ID = 0
WAITING_ADMIN_ID_REMOVE = 1


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش پنل مدیریت (فقط برای SUPER ADMIN)"""
    user_id = update.effective_user.id
    
    if str(user_id) != str(SUPER_ADMIN_ID):
        await update.message.reply_text(
            "❌ شما به این بخش دسترسی ندارید!\n"
            "فقط SUPER ADMIN می‌تواند وارد پنل مدیریت شود."
        )
        return
    
    await update.message.reply_text(
        "👑 پنل مدیریت:\n"
        "یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=admin_panel_keyboard()
    )


async def add_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع افزودن ادمین جدید"""
    user_id = update.effective_user.id
    
    if str(user_id) != str(SUPER_ADMIN_ID):
        await update.message.reply_text("❌ فقط SUPER ADMIN می‌تواند ادمین اضافه کند!")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "➕ افزودن ادمین جدید:\n\n"
        "لطفاً User ID کاربر را ارسال کنید:\n"
        "(مثال: 123456789)\n\n"
        "💡 راهنما: کاربر باید ابتدا /start را به ربات بزند تا User ID خود را ببیند.\n\n"
        "برای لغو روی دکمه لغو بزنید.",
        reply_markup=cancel_keyboard()
    )
    return WAITING_ADMIN_ID


async def receive_admin_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت User ID ادمین جدید"""
    admin_id = update.message.text.strip()
    
    if not admin_id.isdigit():
        await update.message.reply_text(
            "❌ User ID باید عدد باشد!\n"
            "لطفاً مجدداً User ID را ارسال کنید:",
            reply_markup=cancel_keyboard()
        )
        return WAITING_ADMIN_ID
    
    # بررسی اینکه قبلاً ادمین نباشه
    if db.is_admin(admin_id):
        await update.message.reply_text(
            "⚠️ این کاربر قبلاً ادمین است!",
            reply_markup=admin_panel_keyboard()
        )
        return ConversationHandler.END
    
    # افزودن ادمین
    try:
        # سعی کن اطلاعات کاربر رو بگیری
        try:
            user = await context.bot.get_chat(admin_id)
            username = user.username if hasattr(user, 'username') and user.username else None
            first_name = user.first_name if hasattr(user, 'first_name') else None
        except:
            username = None
            first_name = None
        
        if db.add_admin(admin_id, username=username, first_name=first_name):
            # 🔥 ساده‌سازی پیام بدون Markdown پیچیده
            message = f"✅ ادمین جدید اضافه شد!\n\n"
            message += f"🆔 User ID: {admin_id}\n"
            message += f"👤 نام: {first_name or 'نامشخص'}\n"
            message += f"📧 Username: {'@' + username if username else 'ندارد'}"
            
            await update.message.reply_text(
                message,
                reply_markup=admin_panel_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ خطا در افزودن ادمین!",
                reply_markup=admin_panel_keyboard()
            )
    except Exception as e:
        await update.message.reply_text(
            f"❌ خطا: {str(e)}",
            reply_markup=admin_panel_keyboard()
        )
    
    return ConversationHandler.END


async def list_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست ادمین‌ها"""
    user_id = update.effective_user.id
    
    if str(user_id) != str(SUPER_ADMIN_ID):
        await update.message.reply_text("❌ فقط SUPER ADMIN می‌تواند لیست ادمین‌ها را ببیند!")
        return
    
    admins = db.get_admins()
    
    if not admins:
        await update.message.reply_text(
            "❌ هیچ ادمینی ثبت نشده است!",
            reply_markup=admin_panel_keyboard()
        )
        return
    
    # 🔥 ساده‌سازی متن بدون Markdown پیچیده
    text = "📜 لیست ادمین‌ها:\n\n"
    
    for idx, (admin_id, username, first_name, added_date) in enumerate(admins, 1):
        # مشخص کردن SUPER ADMIN
        if str(admin_id) == str(SUPER_ADMIN_ID):
            badge = "👑 SUPER ADMIN"
        else:
            badge = "👤 ادمین"
        
        text += f"{idx}. {badge}\n"
        text += f"   🆔 {admin_id}\n"
        text += f"   نام: {first_name or 'نامشخص'}\n"
        
        # 🔥 اصلاح username برای جلوگیری از خطای Markdown
        if username:
            text += f"   Username: @{username}\n"
        else:
            text += f"   Username: ندارد\n"
        
        # 🔥 فرمت تاریخ ساده
        if added_date:
            date_str = added_date[:10] if len(added_date) >= 10 else added_date
            text += f"   تاریخ: {date_str}\n"
        else:
            text += f"   تاریخ: نامشخص\n"
        
        text += "\n"
    
    # 🔥 ارسال بدون parse_mode برای جلوگیری از خطا
    await update.message.reply_text(
        text,
        reply_markup=admin_panel_keyboard()
    )


async def remove_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع حذف ادمین"""
    user_id = update.effective_user.id
    
    if str(user_id) != str(SUPER_ADMIN_ID):
        await update.message.reply_text("❌ فقط SUPER ADMIN می‌تواند ادمین حذف کند!")
        return ConversationHandler.END
    
    admins = db.get_admins()
    
    # فیلتر کردن SUPER ADMIN (نمی‌تونه خودش رو حذف کنه)
    admins = [a for a in admins if str(a[0]) != str(SUPER_ADMIN_ID)]
    
    if not admins:
        await update.message.reply_text(
            "❌ هیچ ادمینی برای حذف وجود ندارد!",
            reply_markup=admin_panel_keyboard()
        )
        return ConversationHandler.END
    
    text = "➖ حذف ادمین:\n\n"
    text += "📋 لیست ادمین‌ها:\n\n"
    
    for idx, (admin_id, username, first_name, added_date) in enumerate(admins, 1):
        text += f"{idx}. {first_name or 'نامشخص'}\n"
        text += f"   🆔 {admin_id}\n"
        
        if username:
            text += f"   Username: @{username}\n"
        else:
            text += f"   Username: ندارد\n"
        
        text += "\n"
    
    text += "💬 User ID ادمینی که می‌خواهید حذف کنید را ارسال کنید:"
    
    await update.message.reply_text(
        text,
        reply_markup=cancel_keyboard()
    )
    return WAITING_ADMIN_ID_REMOVE


async def receive_admin_id_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت User ID ادمین برای حذف"""
    admin_id = update.message.text.strip()
    
    # جلوگیری از حذف SUPER ADMIN
    if str(admin_id) == str(SUPER_ADMIN_ID):
        await update.message.reply_text(
            "❌ نمی‌توانید SUPER ADMIN را حذف کنید!",
            reply_markup=admin_panel_keyboard()
        )
        return ConversationHandler.END
    
    if db.remove_admin(admin_id):
        try:
            user = await context.bot.get_chat(admin_id)
            first_name = user.first_name if hasattr(user, 'first_name') else 'نامشخص'
            await update.message.reply_text(
                f"✅ ادمین حذف شد:\n\n"
                f"👤 نام: {first_name}\n"
                f"🆔 User ID: {admin_id}",
                reply_markup=admin_panel_keyboard()
            )
        except:
            await update.message.reply_text(
                f"✅ ادمین با User ID زیر حذف شد:\n{admin_id}",
                reply_markup=admin_panel_keyboard()
            )
    else:
        await update.message.reply_text(
            f"❌ این ادمین یافت نشد!\n\n"
            f"User ID وارد شده: {admin_id}",
            reply_markup=admin_panel_keyboard()
        )
    
    return ConversationHandler.END


async def bot_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار ربات"""
    user_id = update.effective_user.id
    
    if str(user_id) != str(SUPER_ADMIN_ID):
        await update.message.reply_text("❌ فقط SUPER ADMIN می‌تواند آمار ربات را ببیند!")
        return
    
    # جمع‌آوری آمار
    admin_count = db.get_admin_count()
    sources = db.get_sources()
    destinations = db.get_destinations()
    active_posts = db.get_active_posts()
    inactive_posts = db.get_inactive_posts()
    interval, interval_type = db.get_forward_interval()
    
    type_fa = {"second": "ثانیه", "minute": "دقیقه", "hour": "ساعت"}
    
    text = "📊 آمار ربات:\n\n"
    text += f"👥 تعداد ادمین‌ها: {admin_count}\n"
    text += f"📤 تعداد مبداها: {len(sources)}\n"
    text += f"📥 تعداد مقاصد: {len(destinations)}\n"
    text += f"📗 پست‌های فعال: {len(active_posts)}\n"
    text += f"📕 پست‌های غیرفعال: {len(inactive_posts)}\n"
    text += f"⏰ زمان فوروارد: هر {interval} {type_fa.get(interval_type, 'ثانیه')} یکبار\n"
    
    await update.message.reply_text(
        text,
        reply_markup=admin_panel_keyboard()
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو عملیات"""
    user_id = update.effective_user.id
    await update.message.reply_text(
        "❌ عملیات لغو شد.",
        reply_markup=main_menu_keyboard(user_id=user_id)
    )
    return ConversationHandler.END


def admin_handlers():
    """بازگشت لیست handler های پنل مدیریت"""
    # Handler برای منوی پنل مدیریت
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
            WAITING_ADMIN_ID_REMOVE: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^❌ لغو$"), receive_admin_id_remove)],
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
