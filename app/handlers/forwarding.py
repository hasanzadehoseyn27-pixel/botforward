# app/handlers/forwarding.py
import re
import asyncio
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, ContextTypes, filters
from app.database import Database
from app.keyboards.keyboards import send_mode_menu_keyboard

db = Database()

# متغیرهای کنترل فوروارد
forwarding_task = None
is_forwarding = False

def extract_ad_number(text):
    """استخراج شماره آگهی از متن پست"""
    match = re.search(r'🔖 آگهی شماره #(\d+)', text)
    if match:
        return match.group(1)
    return None

async def forward_loop(application):
    """حلقه فوروارد خودکار"""
    global is_forwarding
    
    while is_forwarding:
        try:
            interval, interval_type = db.get_forward_interval()
            
            # تبدیل به ثانیه
            if interval_type == "minute":
                sleep_time = interval * 60
            elif interval_type == "hour":
                sleep_time = interval * 3600
            else:  # second
                sleep_time = interval
            
            active_posts = db.get_active_posts()
            destinations = db.get_destinations()
            
            if active_posts and destinations:
                for ad_num, link, source_chat_id, message_id in active_posts:
                    for dest_chat_id in destinations:
                        try:
                            await application.bot.forward_message(
                                chat_id=dest_chat_id,
                                from_chat_id=source_chat_id,
                                message_id=message_id
                            )
                            await asyncio.sleep(1)
                        except Exception as e:
                            print(f"خطا در فوروارد به {dest_chat_id}: {e}")
            
            await asyncio.sleep(sleep_time)
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"خطا در حلقه فوروارد: {e}")
            await asyncio.sleep(10)

async def start_forwarding_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع فوروارد خودکار با دستور /forward"""
    global forwarding_task, is_forwarding
    
    if is_forwarding:
        await update.message.reply_text(
            "✅ فوروارد خودکار در حال اجرا است!",
            reply_markup=send_mode_menu_keyboard(is_forwarding=True)
        )
        return
    
    is_forwarding = True
    forwarding_task = asyncio.create_task(forward_loop(context.application))
    
    await update.message.reply_text(
        "✅ فوروارد خودکار شروع شد!",
        reply_markup=send_mode_menu_keyboard(is_forwarding=True)
    )

async def start_forwarding_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع فوروارد خودکار با دکمه"""
    global forwarding_task, is_forwarding
    
    if is_forwarding:
        await update.message.reply_text(
            "✅ فوروارد خودکار در حال اجرا است!",
            reply_markup=send_mode_menu_keyboard(is_forwarding=True)
        )
        return
    
    is_forwarding = True
    forwarding_task = asyncio.create_task(forward_loop(context.application))
    
    await update.message.reply_text(
        "✅ فوروارد خودکار شروع شد!",
        reply_markup=send_mode_menu_keyboard(is_forwarding=True)
    )

async def stop_forwarding_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """توقف فوروارد خودکار با دستور /stop"""
    global forwarding_task, is_forwarding
    
    if not is_forwarding:
        await update.message.reply_text(
            "❌ فوروارد خودکار فعال نیست!",
            reply_markup=send_mode_menu_keyboard(is_forwarding=False)
        )
        return
    
    is_forwarding = False
    if forwarding_task:
        forwarding_task.cancel()
    
    await update.message.reply_text(
        "⏹ فوروارد خودکار متوقف شد!",
        reply_markup=send_mode_menu_keyboard(is_forwarding=False)
    )

async def stop_forwarding_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """توقف فوروارد خودکار با دکمه"""
    global forwarding_task, is_forwarding
    
    if not is_forwarding:
        await update.message.reply_text(
            "❌ فوروارد خودکار فعال نیست!",
            reply_markup=send_mode_menu_keyboard(is_forwarding=False)
        )
        return
    
    is_forwarding = False
    if forwarding_task:
        forwarding_task.cancel()
    
    await update.message.reply_text(
        "⏹ فوروارد خودکار متوقف شد!",
        reply_markup=send_mode_menu_keyboard(is_forwarding=False)
    )

async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت پست‌های جدید کانال‌های مبدا"""
    if not update.channel_post:
        return
    
    message = update.channel_post
    chat_id = str(message.chat_id)
    
    # بررسی اینکه کانال جزو مبداها هست یا نه
    sources = db.get_sources()
    if chat_id not in sources:
        return
    
    # اگه پیام متنی داره
    if message.text:
        ad_number = extract_ad_number(message.text)
        
        if ad_number:
            # پیام با شماره آگهی
            message_link = f"https://t.me/c/{chat_id.replace('-100', '')}/{message.message_id}"
            
            if db.add_post(ad_number, chat_id, message.message_id, message_link):
                print(f"✅ پست با شماره آگهی ذخیره شد: آگهی #{ad_number}")
            else:
                print(f"⚠️ پست تکراری: آگهی #{ad_number}")
        else:
            # پیام بدون شماره آگهی - از message_id به عنوان شماره یکتا استفاده کن
            ad_number = f"msg_{message.message_id}"
            message_link = f"https://t.me/c/{chat_id.replace('-100', '')}/{message.message_id}"
            
            if db.add_post(ad_number, chat_id, message.message_id, message_link):
                print(f"✅ پست بدون شماره آگهی ذخیره شد: {ad_number}")
            else:
                print(f"⚠️ پست تکراری: {ad_number}")
    
    # اگه پیام عکس/ویدیو/فایل و... داره (بدون متن یا با کپشن)
    elif message.caption:
        ad_number = extract_ad_number(message.caption)
        
        if ad_number:
            message_link = f"https://t.me/c/{chat_id.replace('-100', '')}/{message.message_id}"
            if db.add_post(ad_number, chat_id, message.message_id, message_link):
                print(f"✅ پست با کپشن ذخیره شد: آگهی #{ad_number}")
            else:
                print(f"⚠️ پست تکراری: آگهی #{ad_number}")
        else:
            ad_number = f"msg_{message.message_id}"
            message_link = f"https://t.me/c/{chat_id.replace('-100', '')}/{message.message_id}"
            if db.add_post(ad_number, chat_id, message.message_id, message_link):
                print(f"✅ پست با کپشن (بدون شماره) ذخیره شد: {ad_number}")
    
    else:
        # پیام بدون متن و کپشن (مثلاً فقط عکس)
        ad_number = f"msg_{message.message_id}"
        message_link = f"https://t.me/c/{chat_id.replace('-100', '')}/{message.message_id}"
        
        if db.add_post(ad_number, chat_id, message.message_id, message_link):
            print(f"✅ پیام بدون متن ذخیره شد: {ad_number}")

# Handler برای channel posts
channel_post_handler = MessageHandler(filters.UpdateType.CHANNEL_POST, handle_channel_post)

def forwarding_handlers():
    """بازگشت لیست handler های فوروارد"""
    return [
        CommandHandler("forward", start_forwarding_command),
        CommandHandler("stop", stop_forwarding_command),
        MessageHandler(filters.Regex("^▶️ شروع فوروارد$"), start_forwarding_button),
        MessageHandler(filters.Regex("^🛑 توقف فوروارد$"), stop_forwarding_button)
    ]
