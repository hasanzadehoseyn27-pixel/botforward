# app/handlers/posts.py
from telegram import Update
from telegram.ext import CallbackQueryHandler, MessageHandler, ContextTypes, filters
from app.keyboards.keyboards import posts_menu_keyboard, post_toggle_button, main_menu_keyboard
from app.database import Database

db = Database()

async def list_posts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منوی لیست پست‌ها"""
    await update.message.reply_text(
        "📋 مدیریت پست‌ها:\n"
        "یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=posts_menu_keyboard()
    )

async def active_posts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش پست‌های فعال"""
    posts = db.get_active_posts()
    if posts:
        await update.message.reply_text(
            "📗 پست‌های فعال:\n"
            "روی هر پست کلیک کنید تا لینکش باز شود:",
            reply_markup=posts_menu_keyboard()
        )
        
        for ad_num, link, _, _ in posts:
            text = f"🔖 شماره آگهی #{ad_num}"
            if link:
                text = f"[{text}]({link})"
            
            await update.message.reply_text(
                text,
                parse_mode='Markdown',
                reply_markup=post_toggle_button(ad_num, True)
            )
    else:
        await update.message.reply_text(
            "❌ هیچ پست فعالی وجود ندارد!",
            reply_markup=posts_menu_keyboard()
        )

async def inactive_posts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش پست‌های غیرفعال"""
    posts = db.get_inactive_posts()
    if posts:
        await update.message.reply_text(
            "📕 پست‌های غیرفعال:\n"
            "روی هر پست کلیک کنید تا لینکش باز شود:",
            reply_markup=posts_menu_keyboard()
        )
        
        for ad_num, link in posts:
            text = f"🔖 شماره آگهی #{ad_num}"
            if link:
                text = f"[{text}]({link})"
            
            await update.message.reply_text(
                text,
                parse_mode='Markdown',
                reply_markup=post_toggle_button(ad_num, False)
            )
    else:
        await update.message.reply_text(
            "❌ هیچ پست غیرفعالی وجود ندارد!",
            reply_markup=posts_menu_keyboard()
        )

async def toggle_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تغییر وضعیت پست"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    parts = data.split("_")
    ad_number = parts[2]
    
    new_status = db.toggle_post(ad_number)
    
    if new_status is not None:
        status_text = "✅ روشن" if new_status == 1 else "❌ خاموش"
        await query.answer(f"وضعیت پست به {status_text} تغییر کرد!", show_alert=True)
        await query.edit_message_reply_markup(
            reply_markup=post_toggle_button(ad_number, new_status)
        )
    else:
        await query.answer("❌ خطا در تغییر وضعیت!")

def posts_handlers():
    """بازگشت لیست handler های پست‌ها"""
    return [
        MessageHandler(filters.Regex("^📋 لیست پست‌ها$"), list_posts_menu),
        MessageHandler(filters.Regex("^📗 پست‌های فعال$"), active_posts),
        MessageHandler(filters.Regex("^📕 پست‌های غیرفعال$"), inactive_posts),
        CallbackQueryHandler(toggle_post, pattern="^toggle_")
    ]
