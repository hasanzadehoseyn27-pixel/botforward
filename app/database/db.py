# app/database.py
import sqlite3

class Database:
    def __init__(self, db_name="bot_data.db"):
        self.db_name = db_name
        self.init_db()
    
    def init_db(self):
        """ایجاد جداول دیتابیس"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # جدول مبداها
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sources (
                chat_id TEXT PRIMARY KEY
            )
        ''')
        
        # جدول مقاصد
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS destinations (
                chat_id TEXT PRIMARY KEY
            )
        ''')
        
        # جدول پست‌ها
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                ad_number TEXT PRIMARY KEY,
                source_chat_id TEXT,
                message_id INTEGER,
                message_link TEXT,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        # جدول تنظیمات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # جدول ادمین‌ها (جدید)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                added_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # تنظیم مقدار پیش‌فرض برای زمان فوروارد
        cursor.execute('''
            INSERT OR IGNORE INTO settings (key, value) VALUES ('forward_interval', '10')
        ''')
        cursor.execute('''
            INSERT OR IGNORE INTO settings (key, value) VALUES ('interval_type', 'second')
        ''')
        
        conn.commit()
        conn.close()
    
    # ==================== توابع مبدا ====================
    
    def add_source(self, chat_id):
        """افزودن مبدا"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO sources (chat_id) VALUES (?)', (chat_id,))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def remove_source(self, chat_id):
        """حذف مبدا"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sources WHERE chat_id = ?', (chat_id,))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0
    
    def get_sources(self):
        """دریافت لیست مبداها"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT chat_id FROM sources')
        sources = [row[0] for row in cursor.fetchall()]
        conn.close()
        return sources
    
    # ==================== توابع مقصد ====================
    
    def add_destination(self, chat_id):
        """افزودن مقصد"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO destinations (chat_id) VALUES (?)', (chat_id,))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def remove_destination(self, chat_id):
        """حذف مقصد"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM destinations WHERE chat_id = ?', (chat_id,))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0
    
    def get_destinations(self):
        """دریافت لیست مقاصد"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT chat_id FROM destinations')
        destinations = [row[0] for row in cursor.fetchall()]
        conn.close()
        return destinations
    
    # ==================== توابع پست ====================
    
    def add_post(self, ad_number, source_chat_id, message_id, message_link):
        """افزودن پست"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO posts (ad_number, source_chat_id, message_id, message_link, is_active)
                VALUES (?, ?, ?, ?, 1)
            ''', (ad_number, source_chat_id, message_id, message_link))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_active_posts(self):
        """دریافت پست‌های فعال"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ad_number, message_link, source_chat_id, message_id 
            FROM posts WHERE is_active = 1
        ''')
        posts = cursor.fetchall()
        conn.close()
        return posts
    
    def get_inactive_posts(self):
        """دریافت پست‌های غیرفعال"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT ad_number, message_link FROM posts WHERE is_active = 0')
        posts = cursor.fetchall()
        conn.close()
        return posts
    
    def toggle_post(self, ad_number):
        """تغییر وضعیت پست"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT is_active FROM posts WHERE ad_number = ?', (ad_number,))
        result = cursor.fetchone()
        
        if result:
            new_status = 0 if result[0] == 1 else 1
            cursor.execute('UPDATE posts SET is_active = ? WHERE ad_number = ?', (new_status, ad_number))
            conn.commit()
            conn.close()
            return new_status
        
        conn.close()
        return None
    
    # ==================== توابع تنظیمات ====================
    
    def set_forward_interval(self, interval, interval_type):
        """تنظیم زمان فوروارد"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('UPDATE settings SET value = ? WHERE key = "forward_interval"', (str(interval),))
        cursor.execute('UPDATE settings SET value = ? WHERE key = "interval_type"', (interval_type,))
        conn.commit()
        conn.close()
    
    def get_forward_interval(self):
        """دریافت زمان فوروارد"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = "forward_interval"')
        interval = int(cursor.fetchone()[0])
        cursor.execute('SELECT value FROM settings WHERE key = "interval_type"')
        interval_type = cursor.fetchone()[0]
        conn.close()
        return interval, interval_type
    
    # ==================== توابع ادمین (جدید) ====================
    
    def add_admin(self, user_id, username=None, first_name=None):
        """افزودن ادمین"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO admins (user_id, username, first_name)
                VALUES (?, ?, ?)
            ''', (str(user_id), username, first_name))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def remove_admin(self, user_id):
        """حذف ادمین"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM admins WHERE user_id = ?', (str(user_id),))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0
    
    def get_admins(self):
        """دریافت لیست ادمین‌ها"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, username, first_name, added_date FROM admins')
        admins = cursor.fetchall()
        conn.close()
        return admins
    
    def is_admin(self, user_id):
        """بررسی ادمین بودن کاربر"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM admins WHERE user_id = ?', (str(user_id),))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def get_admin_count(self):
        """تعداد ادمین‌ها"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM admins')
        count = cursor.fetchone()[0]
        conn.close()
        return count
