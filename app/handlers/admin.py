# app/handlers/admin.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters
)
from app.keyboards.keyboards import admin_panel_keyboard, cancel_keyboard, main_menu_keyboard
from app.database import Database
from config import SUPER_ADMIN_ID  # ✅ اضافه شد


db = Database()


# States
WAITING_ADMIN_ID = 0
WAITING_ADMIN_REMOVE = 1


def is_super_admin(user_id: int) -> bool:
    """بررسی SUPER_ADMIN بودن کاربر"""
    return str(user_id) == str(SUPER_ADMIN_ID)


async def is_admin(user_id: int) -> bool:
    """بررسی ادمین بودن کاربر"""
    # 🔥 اول چک کن که SUPER_ADMIN هست یا نه
    if is_super_admin(user_id):
        # اگر تو دیتابیس نیست، اضافه‌اش کن
        if not db.is_admin(str(user_id)):
            db.add_admin(str(user_id), username="SUPER_ADMIN", first_name="Super Admin")
            print(f"✅ SUPER_ADMIN {user_id} به دیتابیس اضافه شد!")
        return True
    
    # بقیه چک کن
    return db.is_admin(str(user_id))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /start"""
    user = update.effective_user
    user_id = user.id
    
    # بررسی ادمین بودن
    if not await is_admin(user_id):
        await update.message.reply_text(
            f"❌ دسترسی غیرمجاز!\n\n"
            f"👋 سلام {user.first_name}!\n"
            f"شما به این ربات دسترسی ندارید.\n\n"
            f"🆔 User ID شما: <code>{user_id}</code>\n\n"
            f"برای دریافت دسترسی، این User ID را به ادمین ربات بدهید.",
            parse_mode='HTML'
        )
        return
    
    # منوی اصلی ادمین
    keyboard = [
        [
            InlineKeyboardButton("📥 مبدا", callback_data="source_menu"),
            InlineKeyboardButton("📤 مقصد", callback_data="destination_menu")
        ],
        [
            InlineKeyboardButton("📋 پست‌ها", callback_data="posts_menu"),
            InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings_menu")
        ],
        [
            InlineKeyboardButton("👥 ادمین‌ها", callback_data="admin_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 سلام {user.first_name}!\n"
        f"به پنل مدیریت ربات خوش آمدید.\n\n"
        f"🆔 User ID شما: <code>{user_id}</code>",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پنل مدیریت - فقط برای SUPER_ADMIN"""
    user_id = update.effective_user.id
    
    # 🔥 فقط SUPER_ADMIN می‌تونه وارد پنل مدیریت بشه
    if not is_super_admin(user_id):
        await update.message.reply_text(
            "❌ شما دسترسی به پنل مدیریت ندارید!\n"
            "فقط SUPER ADMIN می‌تواند وارد این بخش شود.",
            reply_markup=main_menu_keyboard()
        )
        return
    
    await update.message.reply_text(
        "👑 پنل مدیریت:\n"
        "یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=admin_panel_keyboard()
    )


async def add_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع افزودن ادمین - فقط برای SUPER_ADMIN"""
    user_id = update.effective_user.id
    
    # 🔥 فقط SUPER_ADMIN می‌تونه ادمین اضافه کنه
    if not is_super_admin(user_id):
        await update.message.reply_text(
            "❌ شما دسترسی به این بخش ندارید!\n"
            "فقط SUPER ADMIN می‌تواند ادمین اضافه کند.",
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
        username = user.username if hasattr(user, 'username') and user.username else None
        first_name = user.first_name if user.first_name else None
        
        if db.add_admin(admin_id, username, first_name):
            user_tag = f"@{username}" if username else "بدون یوزرنیم"
            name = first_name if first_name else "بدون نام"
            
            await update.message.reply_text(
                f"✅ ادمین با موفقیت اضافه شد:\n\n"
                f"👤 نام: {name}\n"
                f"🆔 یوزرنیم: {user_tag}\n"
                f"🔢 User ID: <code>{admin_id}</code>",
                parse_mode='HTML',
                reply_markup=admin_panel_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ این کاربر قبلاً ادمین است!",
                reply_markup=admin_panel_keyboard()
            )
    except Exception as e:
        # اگه اطلاعات کاربر قابل دسترسی نیست، بازم اضافه کن
        if db.add_admin(admin_id, None, None):
            await update.message.reply_text(
                f"✅ ادمین اضافه شد:\n\n"
                f"🔢 User ID: <code>{admin_id}</code>\n\n"
                f"⚠️ اطلاعات کاربر قابل دسترسی نیست.\n"
                f"کاربر باید حداقل یکبار ربات را /start کند.",
                parse_mode='HTML',
                reply_markup=admin_panel_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ این کاربر قبلاً ادمین است!",
                reply_markup=admin_panel_keyboard()
            )
    
    return ConversationHandler.END


async def list_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست ادمین‌ها - فقط برای SUPER_ADMIN"""
    user_id = update.effective_user.id
    
    # 🔥 فقط SUPER_ADMIN می‌تونه لیست ادمین‌ها رو ببینه
    if not is_super_admin(user_id):
        await update.message.reply_text(
            "❌ شما دسترسی به این بخش ندارید!\n"
            "فقط SUPER ADMIN می‌تواند لیست ادمین‌ها را مشاهده کند.",
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
    
    for idx, admin_data in enumerate(admins, 1):
        # 🔥 چک کردن تعداد عناصر tuple
        if len(admin_data) == 4:
            user_id_db, username, first_name, added_date = admin_data
        else:
            # اگه فرمت متفاوت بود
            user_id_db = admin_data[0]
            username = admin_data[1] if len(admin_data) > 1 else None
            first_name = admin_data[2] if len(admin_data) > 2 else None
            added_date = admin_data[3] if len(admin_data) > 3 else "نامشخص"
        
        name = first_name if first_name else "بدون نام"
        user_tag = f"@{username}" if username else "بدون یوزرنیم"
        date_str = added_date[:10] if added_date and len(added_date) >= 10 else "نامشخص"
        
        # 🔥 استفاده از HTML به جای Markdown برای جلوگیری از خطا
        text += f"{idx}. <b>{name}</b> ({user_tag})\n"
        text += f"   🔢 User ID: <code>{user_id_db}</code>\n"
        text += f"   📅 تاریخ: {date_str}\n\n"
    
    await update.message.reply_text(
        text,
        parse_mode='HTML',  # 🔥 تغییر از Markdown به HTML
        reply_markup=admin_panel_keyboard()
    )


async def remove_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع حذف ادمین - فقط برای SUPER_ADMIN"""
    user_id = update.effective_user.id
    
    # 🔥 فقط SUPER_ADMIN می‌تونه ادمین حذف کنه
    if not is_super_admin(user_id):
        await update.message.reply_text(
            "❌ شما دسترسی به این بخش ندارید!\n"
            "فقط SUPER ADMIN می‌تواند ادمین حذف کند.",
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
    
    for idx, admin_data in enumerate(admins, 1):
        # 🔥 چک کردن تعداد عناصر tuple
        if len(admin_data) == 4:
            user_id_db, username, first_name, added_date = admin_data
        else:
            user_id_db = admin_data[0]
            username = admin_data[1] if len(admin_data) > 1 else None
            first_name = admin_data[2] if len(admin_data) > 2 else None
        
        name = first_name if first_name else "بدون نام"
        user_tag = f"@{username}" if username else "بدون یوزرنیم"
        
        # 🔥 استفاده از HTML به جای Markdown
        text += f"{idx}. {name} ({user_tag})\n"
        text += f"   🔢 <code>{user_id_db}</code>\n\n"
    
    text += "💬 User ID ادمینی که می‌خواهید حذف کنید را ارسال کنید:"
    
    await update.message.reply_text(
        text,
        parse_mode='HTML',  # 🔥 تغییر از Markdown به HTML
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
            f"✅ ادمین با User ID زیر حذف شد:\n<code>{admin_id}</code>",
            parse_mode='HTML',
            reply_markup=admin_panel_keyboard()
        )
    else:
        await update.message.reply_text(
            f"❌ این User ID در لیست ادمین‌ها یافت نشد!\n\n"
            f"User ID وارد شده: <code>{admin_id}</code>",
            parse_mode='HTML',
            reply_markup=admin_panel_keyboard()
        )
    
    return ConversationHandler.END


async def bot_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار ربات"""
    user_id = update.effective_user.id
    
    if not await is_admin(user_id):
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
    # Handler برای دستور /start
    start_handler = CommandHandler("start", start)
    
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
    
    return [start_handler, admin_panel_handler, list_admins_handler, bot_stats_handler, add_admin_conv, remove_admin_conv]
