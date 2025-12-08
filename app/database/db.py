# app/database/db.py
import sqlite3
import os

class Database:
    def __init__(self, db_name='bot.db'):
        """اتصال به دیتابیس"""
        # ایجاد مسیر کامل برای دیتابیس
        db_path = os.path.join(os.getcwd(), db_name)
        
        # مطمئن شویم که پوشه وجود دارد
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        print(f"📁 مسیر دیتابیس: {db_path}")
        
        try:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self._create_tables()
            print("✅ دیتابیس با موفقیت متصل شد!")
        except Exception as e:
            print(f"❌ خطا در اتصال به دیتابیس: {e}")
            # اگر مسیر مشکل دارد، از /tmp استفاده کن
            db_path = f"/tmp/{db_name}"
            print(f"📁 تلاش برای استفاده از: {db_path}")
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self._create_tables()
            print("✅ دیتابیس در /tmp ساخته شد!")
    
    def _create_tables(self):
        """ساخت جداول دیتابیس"""
        
        # جدول مبداها (Sources)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT UNIQUE NOT NULL
            )
        ''')
        
        # جدول مقاصد (Destinations)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS destinations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT UNIQUE NOT NULL
            )
        ''')
        
        # جدول پست‌ها (Posts)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad_number TEXT UNIQUE NOT NULL,
                source_chat_id TEXT NOT NULL,
                message_id INTEGER NOT NULL,
                message_link TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول تنظیمات (Settings)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # مقداردهی اولیه تنظیمات
        self.cursor.execute('''
            INSERT OR IGNORE INTO settings (key, value) VALUES ('forward_interval', '5')
        ''')
        self.cursor.execute('''
            INSERT OR IGNORE INTO settings (key, value) VALUES ('interval_type', 'second')
        ''')
        
        self.conn.commit()
    
    # ========== مدیریت مبداها ==========
    def add_source(self, chat_id):
        """افزودن مبدا"""
        try:
            self.cursor.execute('INSERT INTO sources (chat_id) VALUES (?)', (chat_id,))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def remove_source(self, chat_id):
        """حذف مبدا"""
        self.cursor.execute('DELETE FROM sources WHERE chat_id = ?', (chat_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def get_sources(self):
        """دریافت لیست مبداها"""
        self.cursor.execute('SELECT chat_id FROM sources')
        return [row[0] for row in self.cursor.fetchall()]
    
    # ========== مدیریت مقاصد ==========
    def add_destination(self, chat_id):
        """افزودن مقصد"""
        try:
            self.cursor.execute('INSERT INTO destinations (chat_id) VALUES (?)', (chat_id,))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def remove_destination(self, chat_id):
        """حذف مقصد"""
        self.cursor.execute('DELETE FROM destinations WHERE chat_id = ?', (chat_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def get_destinations(self):
        """دریافت لیست مقاصد"""
        self.cursor.execute('SELECT chat_id FROM destinations')
        return [row[0] for row in self.cursor.fetchall()]
    
    # ========== مدیریت پست‌ها ==========
    def add_post(self, ad_number, source_chat_id, message_id, message_link):
        """افزودن پست جدید"""
        try:
            self.cursor.execute('''
                INSERT INTO posts (ad_number, source_chat_id, message_id, message_link)
                VALUES (?, ?, ?, ?)
            ''', (ad_number, source_chat_id, message_id, message_link))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def toggle_post(self, ad_number):
        """تغییر وضعیت فعال/غیرفعال پست"""
        self.cursor.execute('SELECT is_active FROM posts WHERE ad_number = ?', (ad_number,))
        result = self.cursor.fetchone()
        if result:
            new_status = 0 if result[0] == 1 else 1
            self.cursor.execute('UPDATE posts SET is_active = ? WHERE ad_number = ?', (new_status, ad_number))
            self.conn.commit()
            return new_status
        return None
    
    def get_active_posts(self):
        """دریافت پست‌های فعال"""
        self.cursor.execute('''
            SELECT ad_number, message_link, source_chat_id, message_id 
            FROM posts WHERE is_active = 1
        ''')
        return self.cursor.fetchall()
    
    def get_inactive_posts(self):
        """دریافت پست‌های غیرفعال"""
        self.cursor.execute('''
            SELECT ad_number, message_link 
            FROM posts WHERE is_active = 0
        ''')
        return self.cursor.fetchall()
    
    # ========== مدیریت تنظیمات ==========
    def set_forward_interval(self, value, interval_type):
        """تنظیم زمان فوروارد"""
        self.cursor.execute('UPDATE settings SET value = ? WHERE key = ?', (str(value), 'forward_interval'))
        self.cursor.execute('UPDATE settings SET value = ? WHERE key = ?', (interval_type, 'interval_type'))
        self.conn.commit()
    
    def get_forward_interval(self):
        """دریافت زمان فوروارد"""
        self.cursor.execute('SELECT value FROM settings WHERE key = ?', ('forward_interval',))
        interval = self.cursor.fetchone()[0]
        self.cursor.execute('SELECT value FROM settings WHERE key = ?', ('interval_type',))
        interval_type = self.cursor.fetchone()[0]
        return int(interval), interval_type
    
    def close(self):
        """بستن اتصال دیتابیس"""
        self.conn.close()
