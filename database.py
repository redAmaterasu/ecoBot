"""
مدیریت دیتابیس MySQL برای ربات تلگرام
"""

import mysql.connector
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class DatabaseManager:
    """مدیریت پایگاه داده MySQL"""
    
    def __init__(self):
        self.connection = None
        self.connect()
        self.init_database()
    
    def connect(self):
        """اتصال به دیتابیس MySQL"""
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', 3306)),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', ''),
                database=os.getenv('DB_NAME', 'heshmatbot'),
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            logger.info("✅ MySQL database connection established")
        except mysql.connector.Error as e:
            logger.error(f"❌ Database connection error: {e}")
            raise
    
    def init_database(self):
        """ایجاد جداول مورد نیاز"""
        try:
            cursor = self.connection.cursor()
            
            # ایجاد جدول کاربران
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    phone VARCHAR(20),
                    city VARCHAR(100),
                    is_registered BOOLEAN DEFAULT FALSE,
                    join_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                    message_count INT DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # اضافه کردن ستون‌های جدید به جدول موجود (اگر وجود دارد)
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN phone VARCHAR(20)')
                logger.info("✅ Column phone added")
            except mysql.connector.Error:
                pass  # ستون قبلاً وجود دارد
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN city VARCHAR(100)')
                logger.info("✅ Column city added")
            except mysql.connector.Error:
                pass  # ستون قبلاً وجود دارد
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN is_registered BOOLEAN DEFAULT FALSE')
                logger.info("✅ Column is_registered added")
            except mysql.connector.Error:
                pass  # ستون قبلاً وجود دارد
            
            # ایجاد جدول پیام‌ها
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT,
                    message_text TEXT,
                    message_type VARCHAR(50) DEFAULT 'text',
                    message_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # ایجاد جدول لاگ‌ها
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT,
                    action VARCHAR(255),
                    details TEXT,
                    log_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # ایجاد جدول محصولات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    price DECIMAL(10,2) NOT NULL,
                    image_url VARCHAR(500),
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # ایجاد جدول عکس‌های محصولات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS product_images (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    product_id INT NOT NULL,
                    file_id VARCHAR(255) NOT NULL,
                    file_unique_id VARCHAR(255) NOT NULL,
                    file_size INT,
                    width INT,
                    height INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')

            # ایجاد جدول سفارش‌ها
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    product_id INT NOT NULL,
                    price DECIMAL(10,2) NOT NULL,
                    status ENUM('pending','approved','rejected') DEFAULT 'pending',
                    screenshot_file_id VARCHAR(255),
                    admin_id BIGINT NULL,
                    rejection_reason TEXT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    approved_at DATETIME NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # ایجاد ایندکس‌ها (با بررسی وجود)
            try:
                cursor.execute('CREATE INDEX idx_users_username ON users(username)')
            except mysql.connector.Error:
                pass  # ایندکس قبلاً وجود دارد
            
            try:
                cursor.execute('CREATE INDEX idx_users_join_date ON users(join_date)')
            except mysql.connector.Error:
                pass
            
            try:
                cursor.execute('CREATE INDEX idx_messages_user_id ON messages(user_id)')
            except mysql.connector.Error:
                pass
            
            try:
                cursor.execute('CREATE INDEX idx_messages_date ON messages(message_date)')
            except mysql.connector.Error:
                pass
            
            try:
                cursor.execute('CREATE INDEX idx_logs_date ON logs(log_date)')
            except mysql.connector.Error:
                pass

            # ایندکس‌های سفارش‌ها
            try:
                cursor.execute('CREATE INDEX idx_orders_user_id ON orders(user_id)')
            except mysql.connector.Error:
                pass
            try:
                cursor.execute('CREATE INDEX idx_orders_status ON orders(status)')
            except mysql.connector.Error:
                pass
            try:
                cursor.execute('CREATE INDEX idx_orders_created_at ON orders(created_at)')
            except mysql.connector.Error:
                pass
            
            self.connection.commit()
            cursor.close()
            logger.info("✅ Database tables created")
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error creating tables: {e}")
            raise
    
    def add_user(self, user_id: int, username: str, first_name: str, last_name: str) -> bool:
        """اضافه کردن کاربر جدید (بدون ثبت نام کامل)"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, last_name, join_date, last_activity)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                username = VALUES(username),
                first_name = VALUES(first_name),
                last_name = VALUES(last_name),
                last_activity = VALUES(last_activity),
                is_active = TRUE
            ''', (user_id, username, first_name, last_name, 
                  datetime.now(), datetime.now()))
            
            self.connection.commit()
            cursor.close()
            
            # ثبت لاگ
            self.add_log(user_id, 'user_added', f'User {username} added')
            
            return True
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error adding user: {e}")
            return False
    
    def register_user(self, user_id: int, first_name: str, last_name: str, phone: str = None, city: str = None) -> bool:
        """ثبت نام کامل کاربر"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET first_name = %s, last_name = %s, phone = %s, city = %s, 
                    is_registered = TRUE, updated_at = %s
                WHERE user_id = %s
            ''', (first_name, last_name, phone, city, datetime.now(), user_id))
            
            self.connection.commit()
            cursor.close()
            
            # ثبت لاگ
            self.add_log(user_id, 'user_registered', f'User {first_name} {last_name} registered')
            
            return True
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error registering user: {e}")
            return False
    
    def is_user_registered(self, user_id: int) -> bool:
        """بررسی اینکه آیا کاربر ثبت نام کرده است یا نه"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                SELECT is_registered FROM users WHERE user_id = %s
            ''', (user_id,))
            
            result = cursor.fetchone()
            cursor.close()
            
            return result[0] if result else False
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error checking registration status: {e}")
            return False
    
    def update_user_profile(self, user_id: int, **kwargs) -> bool:
        """به‌روزرسانی پروفایل کاربر"""
        try:
            cursor = self.connection.cursor()
            
            # ساخت query دینامیک
            fields = []
            values = []
            
            for field, value in kwargs.items():
                if field in ['phone', 'first_name', 'last_name', 'city']:
                    fields.append(f"{field} = %s")
                    values.append(value)
            
            if not fields:
                return False
            
            values.append(datetime.now())
            values.append(user_id)
            
            query = f'''
                UPDATE users 
                SET {', '.join(fields)}, updated_at = %s
                WHERE user_id = %s
            '''
            
            cursor.execute(query, values)
            self.connection.commit()
            cursor.close()
            
            # ثبت لاگ
            self.add_log(user_id, 'profile_updated', f'User profile updated: {list(kwargs.keys())}')
            
            return True
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error updating profile: {e}")
            return False
    
    def update_user_activity(self, user_id: int) -> bool:
        """به‌روزرسانی فعالیت کاربر"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET last_activity = %s, message_count = message_count + 1
                WHERE user_id = %s
            ''', (datetime.now(), user_id))
            
            self.connection.commit()
            cursor.close()
            return True
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error updating user activity: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """دریافت اطلاعات کاربر"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            cursor.execute('''
                SELECT * FROM users WHERE user_id = %s
            ''', (user_id,))
            
            result = cursor.fetchone()
            cursor.close()
            return result
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error getting user info: {e}")
            return None
    
    def get_all_users(self) -> List[Dict]:
        """دریافت لیست تمام کاربران"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            cursor.execute('''
                SELECT user_id, username, first_name, last_name, join_date, last_activity, message_count
                FROM users 
                WHERE is_active = TRUE
                ORDER BY join_date DESC
            ''')
            
            results = cursor.fetchall()
            cursor.close()
            return results
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error getting users list: {e}")
            return []
    
    def get_users_count(self) -> int:
        """تعداد کل کاربران فعال"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM users WHERE is_active = TRUE
            ''')
            
            count = cursor.fetchone()[0]
            cursor.close()
            return count
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error counting users: {e}")
            return 0
    
    def add_message(self, user_id: int, message_text: str, message_type: str = "text") -> bool:
        """اضافه کردن پیام به تاریخچه"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                INSERT INTO messages (user_id, message_text, message_type, message_date)
                VALUES (%s, %s, %s, %s)
            ''', (user_id, message_text, message_type, datetime.now()))
            
            self.connection.commit()
            cursor.close()
            return True
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error adding message: {e}")
            return False
    
    def add_log(self, user_id: int, action: str, details: str = "") -> bool:
        """اضافه کردن لاگ"""
        try:
            cursor = self.connection.cursor()
            
            # بررسی وجود کاربر در جدول users
            if user_id != 0:  # اگر user_id صفر نباشد
                cursor.execute('SELECT user_id FROM users WHERE user_id = %s', (user_id,))
                if not cursor.fetchone():
                    # اگر کاربر وجود ندارد، ابتدا آن را اضافه کن
                    cursor.execute('''
                        INSERT IGNORE INTO users (user_id, username, first_name, last_name, join_date, last_activity)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (user_id, 'Unknown', 'Unknown', 'User', datetime.now(), datetime.now()))
                    self.connection.commit()  # commit کردن قبل از اضافه کردن لاگ
            
            # اضافه کردن لاگ با user_id یا NULL
            log_user_id = user_id if user_id != 0 else None
            cursor.execute('''
                INSERT INTO logs (user_id, action, details, log_date)
                VALUES (%s, %s, %s, %s)
            ''', (log_user_id, action, details, datetime.now()))
            
            self.connection.commit()
            cursor.close()
            return True
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error adding log: {e}")
            return False
    
    def get_user_stats(self, user_id: int) -> Optional[Dict]:
        """دریافت آمار کاربر"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            cursor.execute('''
                SELECT 
                    u.*,
                    COUNT(m.id) as total_messages,
                    MAX(m.message_date) as last_message_date
                FROM users u
                LEFT JOIN messages m ON u.user_id = m.user_id
                WHERE u.user_id = %s
                GROUP BY u.user_id
            ''', (user_id,))
            
            result = cursor.fetchone()
            cursor.close()
            return result
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error getting user stats: {e}")
            return None
    
    def get_daily_stats(self) -> Dict:
        """دریافت آمار روزانه"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # آمار کاربران جدید امروز
            cursor.execute('''
                SELECT COUNT(*) as new_users_today
                FROM users 
                WHERE DATE(join_date) = CURDATE()
            ''')
            new_users = cursor.fetchone()
            
            # آمار پیام‌های امروز
            cursor.execute('''
                SELECT COUNT(*) as messages_today
                FROM messages 
                WHERE DATE(message_date) = CURDATE()
            ''')
            messages = cursor.fetchone()
            
            # آمار کاربران فعال امروز
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id) as active_users_today
                FROM messages 
                WHERE DATE(message_date) = CURDATE()
            ''')
            active_users = cursor.fetchone()
            
            cursor.close()
            
            return {
                'new_users_today': new_users['new_users_today'],
                'messages_today': messages['messages_today'],
                'active_users_today': active_users['active_users_today']
            }
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error getting daily stats: {e}")
            return {}
    
    def deactivate_user(self, user_id: int) -> bool:
        """غیرفعال کردن کاربر"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET is_active = FALSE, updated_at = %s
                WHERE user_id = %s
            ''', (datetime.now(), user_id))
            
            self.connection.commit()
            cursor.close()
            
            # ثبت لاگ
            self.add_log(user_id, 'user_deactivated', f'User {user_id} deactivated')
            
            return True
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error deactivating user: {e}")
            return False
    
    def close_connection(self):
        """بستن اتصال به دیتابیس"""
        if self.connection:
            self.connection.close()
            logger.info("✅ Database connection closed")
    
    def add_product(self, name: str, price: float, image_url: str = None, description: str = None) -> bool:
        """اضافه کردن محصول جدید"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                INSERT INTO products (name, price, image_url, description)
                VALUES (%s, %s, %s, %s)
            ''', (name, price, image_url, description))
            
            self.connection.commit()
            cursor.close()
            
            # ثبت لاگ (بدون user_id برای محصولات)
            try:
                self.add_log(0, 'product_added', f'Product {name} added')
            except:
                pass  # اگر user_id وجود نداشت، لاگ را نادیده بگیر
            
            return True
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error adding product: {e}")
            return False
    
    def get_all_products(self) -> List[Dict]:
        """دریافت لیست تمام محصولات فعال"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            cursor.execute('''
                SELECT * FROM products 
                WHERE is_active = TRUE
                ORDER BY created_at DESC
            ''')
            
            results = cursor.fetchall()
            cursor.close()
            return results
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error getting products list: {e}")
            return []
    
    def get_products_paginated(self, page: int = 1, per_page: int = 5) -> Dict:
        """دریافت محصولات با pagination"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # محاسبه offset
            offset = (page - 1) * per_page
            
            # دریافت محصولات صفحه جاری
            cursor.execute('''
                SELECT * FROM products 
                WHERE is_active = TRUE
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            ''', (per_page, offset))
            
            products = cursor.fetchall()
            
            # شمارش کل محصولات
            cursor.execute('''
                SELECT COUNT(*) as total FROM products 
                WHERE is_active = TRUE
            ''')
            
            total_count = cursor.fetchone()['total']
            total_pages = (total_count + per_page - 1) // per_page
            
            cursor.close()
            
            return {
                'products': products,
                'current_page': page,
                'total_pages': total_pages,
                'total_count': total_count,
                'per_page': per_page,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error getting paginated products: {e}")
            return {
                'products': [],
                'current_page': 1,
                'total_pages': 0,
                'total_count': 0,
                'per_page': per_page,
                'has_next': False,
                'has_prev': False
            }
    
    def get_product(self, product_id: int) -> Optional[Dict]:
        """دریافت اطلاعات یک محصول"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            cursor.execute('''
                SELECT * FROM products WHERE id = %s
            ''', (product_id,))
            
            result = cursor.fetchone()
            cursor.close()
            return result
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error getting product: {e}")
            return None
    
    def update_product(self, product_id: int, **kwargs) -> bool:
        """به‌روزرسانی محصول"""
        try:
            cursor = self.connection.cursor()
            
            # ساخت query دینامیک
            fields = []
            values = []
            
            for field, value in kwargs.items():
                if field in ['name', 'price', 'image_url', 'description', 'is_active']:
                    fields.append(f"{field} = %s")
                    values.append(value)
            
            if not fields:
                return False
            
            values.append(datetime.now())
            values.append(product_id)
            
            query = f'''
                UPDATE products 
                SET {', '.join(fields)}, updated_at = %s
                WHERE id = %s
            '''
            
            cursor.execute(query, values)
            self.connection.commit()
            cursor.close()
            
            # ثبت لاگ
            self.add_log(0, 'product_updated', f'Product {product_id} updated: {list(kwargs.keys())}')
            
            return True
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error updating product: {e}")
            return False
    
    def delete_product(self, product_id: int) -> bool:
        """حذف محصول (غیرفعال کردن)"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                UPDATE products 
                SET is_active = FALSE, updated_at = %s
                WHERE id = %s
            ''', (datetime.now(), product_id))
            
            self.connection.commit()
            cursor.close()
            
            # ثبت لاگ
            self.add_log(0, 'product_deleted', f'Product {product_id} deleted')
            
            return True
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error deleting product: {e}")
            return False
    
    def get_products_count(self) -> int:
        """تعداد کل محصولات فعال"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM products WHERE is_active = TRUE
            ''')
            
            count = cursor.fetchone()[0]
            cursor.close()
            return count
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error counting products: {e}")
            return 0
    
    def add_product_image(self, product_id: int, file_id: str, file_unique_id: str, file_size: int = None, width: int = None, height: int = None) -> bool:
        """اضافه کردن عکس به محصول"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                INSERT INTO product_images (product_id, file_id, file_unique_id, file_size, width, height)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (product_id, file_id, file_unique_id, file_size, width, height))
            
            self.connection.commit()
            cursor.close()
            return True
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error adding product image: {e}")
            return False
    
    def get_product_images(self, product_id: int) -> List[Dict]:
        """دریافت عکس‌های یک محصول"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            cursor.execute('''
                SELECT * FROM product_images 
                WHERE product_id = %s 
                ORDER BY created_at ASC
            ''', (product_id,))
            
            results = cursor.fetchall()
            cursor.close()
            return results
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error getting product images: {e}")
            return []
    
    def get_product_images_paginated(self, product_id: int, page: int = 1, per_page: int = 3) -> Dict:
        """دریافت عکس‌های یک محصول با pagination"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # محاسبه offset
            offset = (page - 1) * per_page
            
            # دریافت عکس‌های صفحه جاری
            cursor.execute('''
                SELECT * FROM product_images 
                WHERE product_id = %s 
                ORDER BY created_at ASC
                LIMIT %s OFFSET %s
            ''', (product_id, per_page, offset))
            
            images = cursor.fetchall()
            
            # شمارش کل عکس‌ها
            cursor.execute('''
                SELECT COUNT(*) as total FROM product_images 
                WHERE product_id = %s
            ''', (product_id,))
            
            total_count = cursor.fetchone()['total']
            total_pages = (total_count + per_page - 1) // per_page
            
            cursor.close()
            
            return {
                'images': images,
                'current_page': page,
                'total_pages': total_pages,
                'total_count': total_count,
                'per_page': per_page,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error getting paginated images: {e}")
            return {
                'images': [],
                'current_page': 1,
                'total_pages': 0,
                'total_count': 0,
                'per_page': per_page,
                'has_next': False,
                'has_prev': False
            }

    def create_order(self, user_id: int, product_id: int, price: float, screenshot_file_id: str) -> Optional[int]:
        """ایجاد سفارش جدید در حالت در انتظار تایید"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO orders (user_id, product_id, price, status, screenshot_file_id)
                VALUES (%s, %s, %s, 'pending', %s)
            ''', (user_id, product_id, price, screenshot_file_id))
            self.connection.commit()
            order_id = cursor.lastrowid
            cursor.close()
            # ثبت لاگ سفارش
            self.add_log(user_id, 'order_created', f'order #{order_id} for product {product_id} created pending approval')
            return order_id
        except mysql.connector.Error as e:
            logger.error(f"❌ Error creating order: {e}")
            return None

    def get_user_orders(self, user_id: int) -> List[Dict]:
        """دریافت سفارش‌های کاربر"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute('''
                SELECT o.*, p.name as product_name
                FROM orders o
                JOIN products p ON p.id = o.product_id
                WHERE o.user_id = %s
                ORDER BY o.created_at DESC
            ''', (user_id,))
            results = cursor.fetchall()
            cursor.close()
            return results
        except mysql.connector.Error as e:
            logger.error(f"❌ Error getting user orders: {e}")
            return []

    def get_pending_orders(self, page: int = 1, per_page: int = 10) -> Dict:
        """دریافت سفارش‌های در انتظار تایید با pagination برای ادمین"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            offset = (page - 1) * per_page
            cursor.execute('''
                SELECT o.*, p.name as product_name, u.username, u.first_name, u.last_name
                FROM orders o
                JOIN products p ON p.id = o.product_id
                JOIN users u ON u.user_id = o.user_id
                WHERE o.status = 'pending'
                ORDER BY o.created_at ASC
                LIMIT %s OFFSET %s
            ''', (per_page, offset))
            orders = cursor.fetchall()
            cursor.execute("SELECT COUNT(*) as total FROM orders WHERE status = 'pending'")
            total_count = cursor.fetchone()['total']
            total_pages = (total_count + per_page - 1) // per_page
            cursor.close()
            return {
                'orders': orders,
                'current_page': page,
                'total_pages': total_pages,
                'total_count': total_count,
                'per_page': per_page,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        except mysql.connector.Error as e:
            logger.error(f"❌ Error getting pending orders: {e}")
            return {
                'orders': [],
                'current_page': 1,
                'total_pages': 0,
                'total_count': 0,
                'per_page': per_page,
                'has_next': False,
                'has_prev': False
            }

    def get_order(self, order_id: int) -> Optional[Dict]:
        """دریافت جزئیات یک سفارش"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute('''
                SELECT o.*, p.name as product_name
                FROM orders o
                JOIN products p ON p.id = o.product_id
                WHERE o.id = %s
            ''', (order_id,))
            order = cursor.fetchone()
            cursor.close()
            return order
        except mysql.connector.Error as e:
            logger.error(f"❌ Error getting order: {e}")
            return None

    def update_order_status(self, order_id: int, status: str, admin_id: int = None, rejection_reason: str = None) -> bool:
        """به‌روزرسانی وضعیت سفارش و ثبت زمان تایید"""
        try:
            cursor = self.connection.cursor()
            if status == 'approved':
                cursor.execute('''
                    UPDATE orders
                    SET status = 'approved', admin_id = %s, approved_at = %s, updated_at = %s, rejection_reason = NULL
                    WHERE id = %s
                ''', (admin_id, datetime.now(), datetime.now(), order_id))
            elif status == 'rejected':
                cursor.execute('''
                    UPDATE orders
                    SET status = 'rejected', admin_id = %s, updated_at = %s, rejection_reason = %s
                    WHERE id = %s
                ''', (admin_id, datetime.now(), rejection_reason, order_id))
            else:
                cursor.execute('''
                    UPDATE orders
                    SET status = %s, updated_at = %s
                    WHERE id = %s
                ''', (status, datetime.now(), order_id))
            self.connection.commit()
            cursor.close()
            # ثبت لاگ
            self.add_log(admin_id or 0, 'order_status_updated', f'order #{order_id} -> {status}')
            return True
        except mysql.connector.Error as e:
            logger.error(f"❌ Error updating order status: {e}")
            return False
    
    def delete_product_image(self, image_id: int) -> bool:
        """حذف عکس محصول"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                DELETE FROM product_images WHERE id = %s
            ''', (image_id,))
            
            self.connection.commit()
            cursor.close()
            return True
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error deleting product image: {e}")
            return False
    
    def get_product_with_images(self, product_id: int) -> Optional[Dict]:
        """دریافت محصول همراه با عکس‌هایش"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # دریافت اطلاعات محصول
            cursor.execute('''
                SELECT * FROM products WHERE id = %s
            ''', (product_id,))
            
            product = cursor.fetchone()
            if not product:
                cursor.close()
                return None
            
            # دریافت عکس‌های محصول
            cursor.execute('''
                SELECT * FROM product_images 
                WHERE product_id = %s 
                ORDER BY created_at ASC
            ''', (product_id,))
            
            images = cursor.fetchall()
            product['images'] = images
            
            cursor.close()
            return product
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error getting product with images: {e}")
            return None

    def __del__(self):
        """بستن اتصال هنگام حذف شی"""
        self.close_connection()
