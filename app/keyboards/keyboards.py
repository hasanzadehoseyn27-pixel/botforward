# app/keyboards/keyboards.py
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from config import SUPER_ADMIN_ID


def main_menu_keyboard(is_forwarding=False, user_id=None):
    """منوی اصلی با دکمه‌های پایین صفحه"""
    keyboard = [
        [
            KeyboardButton("📤 تعیین مبدا"),
            KeyboardButton("📥 تعیین مقصد")
        ],
        [
            KeyboardButton("📋 لیست پست‌ها"),
            KeyboardButton("⏰ حالت ارسال")
        ]
    ]
    
    # 🔥 دکمه پنل مدیریت فقط برای SUPER_ADMIN
    if user_id and str(user_id) == str(SUPER_ADMIN_ID):
        keyboard.append([KeyboardButton("👑 پنل مدیریت")])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def admin_panel_keyboard():
    """منوی پنل مدیریت"""
    keyboard = [
        [
            KeyboardButton("➕ افزودن ادمین"),
            KeyboardButton("📜 لیست ادمین‌ها")
        ],
        [
            KeyboardButton("➖ حذف ادمین"),
            KeyboardButton("📊 آمار ربات")
        ],
        [
            KeyboardButton("🔙 بازگشت")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def source_menu_keyboard():
    """منوی مدیریت مبداها"""
    keyboard = [
        [
            KeyboardButton("➕ افزودن مبدا"),
            KeyboardButton("📜 لیست مبدا")
        ],
        [
            KeyboardButton("➖ حذف مبدا"),
            KeyboardButton("🔙 بازگشت")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def destination_menu_keyboard():
    """منوی مدیریت مقاصد"""
    keyboard = [
        [
            KeyboardButton("➕ افزودن مقصد"),
            KeyboardButton("📜 لیست مقصد")
        ],
        [
            KeyboardButton("➖ حذف مقصد"),
            KeyboardButton("🔙 بازگشت")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def send_mode_menu_keyboard(is_forwarding=False):
    """منوی حالت ارسال"""
    keyboard = [
        [
            KeyboardButton("⏱ ثانیه‌ای"),
            KeyboardButton("⏲ دقیقه‌ای")
        ],
        [
            KeyboardButton("⏰ ساعتی"),
            KeyboardButton("📊 زمان کنونی")
        ]
    ]
    
    # ردیف آخر: شروع/توقف و بازگشت
    if is_forwarding:
        keyboard.append([
            KeyboardButton("🛑 توقف فوروارد"),
            KeyboardButton("🔙 بازگشت")
        ])
    else:
        keyboard.append([
            KeyboardButton("▶️ شروع فوروارد"),
            KeyboardButton("🔙 بازگشت")
        ])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def posts_menu_keyboard():
    """منوی لیست پست‌ها"""
    keyboard = [
        [
            KeyboardButton("📗 پست‌های فعال"),
            KeyboardButton("📕 پست‌های غیرفعال")
        ],
        [
            KeyboardButton("🔙 بازگشت")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def cancel_keyboard():
    """دکمه لغو"""
    keyboard = [
        [KeyboardButton("❌ لغو")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def post_toggle_button(ad_number, is_active):
    """دکمه روشن/خاموش برای هر پست (Inline)"""
    if is_active:
        text = "✅ روشن"
        callback = f"toggle_off_{ad_number}"
    else:
        text = "❌ خاموش"
        callback = f"toggle_on_{ad_number}"
    
    keyboard = [
        [InlineKeyboardButton(text, callback_data=callback)]
    ]
    return InlineKeyboardMarkup(keyboard)
