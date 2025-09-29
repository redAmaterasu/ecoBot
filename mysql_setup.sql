-- دستورات MySQL برای ایجاد دیتابیس و جداول HeshmatBot

-- ایجاد دیتابیس
CREATE DATABASE IF NOT EXISTS heshmatbot 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- استفاده از دیتابیس
USE heshmatbot;

-- ایجاد جدول کاربران
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    join_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
    message_count INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ایجاد جدول پیام‌ها
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT,
    message_text TEXT,
    message_type VARCHAR(50) DEFAULT 'text',
    message_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ایجاد جدول لاگ‌ها
CREATE TABLE IF NOT EXISTS logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT,
    action VARCHAR(255),
    details TEXT,
    log_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ایجاد ایندکس‌ها برای بهبود عملکرد
-- (اگر ایندکس قبلاً وجود دارد، خطا نادیده گرفته می‌شود)
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_join_date ON users(join_date);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_messages_user_id ON messages(user_id);
CREATE INDEX idx_messages_date ON messages(message_date);
CREATE INDEX idx_logs_date ON logs(log_date);
CREATE INDEX idx_logs_action ON logs(action);

-- نمایش جداول ایجاد شده
SHOW TABLES;

-- نمایش ساختار جدول کاربران
DESCRIBE users;

-- نمایش ساختار جدول پیام‌ها
DESCRIBE messages;

-- نمایش ساختار جدول لاگ‌ها
DESCRIBE logs;
