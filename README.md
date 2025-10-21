# 🤖 HeshmatBot - ربات تلگرام

یک ربات تلگرام ساده و کاربردی با Python و MySQL

## ✨ ویژگی‌ها

- 🎯 **پنل ادمین تعاملی** با منوی زیبا
- 🔐 **Session Management** با مدت زمان قابل تنظیم
- 💬 **چت هوشمند** با پاسخ‌های خودکار
- 📊 **آمار کامل کاربران** و پیام‌ها
- 🗄️ **پایگاه داده MySQL** برای ذخیره اطلاعات
- 📝 **سیستم لاگ‌گیری** کامل
- 🛡️ **امنیت پیشرفته** با دکوریتور محافظ

## 🚀 نصب و راه‌اندازی

### پیش‌نیازها

- Python 3.7+
- MySQL Server
- یک ربات تلگرام (از @BotFather)

### نصب خودکار روی لینوکس (Ubuntu/Debian)

```bash
sudo bash scripts/setup.sh
```

اسکریپت:
- وابستگی‌ها (Python، pip، venv، MySQL Server) را نصب می‌کند
- venv می‌سازد و `requirements.txt` را نصب می‌کند
- دیتابیس و یوزر را می‌سازد و `mysql_setup.sql` را اعمال می‌کند
- فایل `.env` می‌سازد (BOT_TOKEN و ... را می‌پرسد)
- سرویس systemd به نام `heshmatbot` می‌سازد و اجرا می‌کند

متغیرهای قابل تنظیم (اختیاری) قبل از اجرا:

```bash
export PROJECT_DIR=/opt/heshmatbot
export SERVICE_NAME=heshmatbot
export DB_NAME=heshmatbot
export DB_USER=heshmat
export DB_PASSWORD=secret
export MYSQL_ROOT_PWD=your_root_pwd
export BOT_TOKEN=123:ABC
export ADMIN_PASSWORD=admin123
sudo -E bash scripts/setup.sh
```

پس از نصب:

```bash
systemctl status heshmatbot --no-pager
journalctl -u heshmatbot -n 100 --no-pager
```

### مراحل نصب دستی

1. **کلون کردن پروژه:**
   ```bash
   git clone <repository-url>
   cd HeshmatBot
   ```

2. **فعال کردن virtual environment:**
   ```bash
   .\venv\Scripts\Activate.ps1  # Windows
   source venv/bin/activate      # Linux/Mac
   ```

3. **نصب وابستگی‌ها:**
   ```bash
   pip install -r requirements.txt
   ```

4. **تنظیم دیتابیس MySQL:**
   - MySQL Server را نصب کنید
   - دیتابیس `heshmatbot` ایجاد کنید
   - فایل `.env` را ویرایش کنید

5. **تنظیم متغیرهای محیطی:**
   - فایل `.env` را ویرایش کنید
   - توکن ربات و تنظیمات MySQL را وارد کنید

6. **اجرای ربات:**
   ```bash
   python bot.py
   ```

## 📋 دستورات موجود

### دستورات عمومی
- `/start` - شروع کار با ربات
- `/help` - نمایش راهنما

### پنل ادمین تعاملی
- `/admin` - ورود به پنل ادمین (با منوی زیبا)

#### منوی ادمین شامل:
- 📊 **آمار** - آمار کامل کاربران و پیام‌ها
- 👥 **کاربران** - لیست کاربران با جزئیات
- 📢 **ارسال پیام** - ارسال پیام به همه کاربران
- 🔐 **Session** - اطلاعات session ادمین
- 🔄 **تازه‌سازی** - تازه‌سازی منو
- 🚪 **خروج** - خروج از پنل ادمین

## ⚙️ تنظیمات

### فایل .env

```env
# تنظیمات ربات تلگرام
BOT_TOKEN=your_bot_token_here

# رمز عبور پنل ادمین
ADMIN_PASSWORD=admin123

# تنظیمات دیتابیس MySQL
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=heshmatbot

# تنظیمات لاگ
LOG_LEVEL=INFO
LOG_FILE=bot.log
```

## 🗄️ ساختار دیتابیس

### جدول users
- `user_id` - شناسه کاربر تلگرام
- `username` - نام کاربری
- `first_name` - نام
- `last_name` - نام خانوادگی
- `join_date` - تاریخ عضویت
- `last_activity` - آخرین فعالیت
- `message_count` - تعداد پیام‌ها

### جدول messages
- `id` - شناسه پیام
- `user_id` - شناسه کاربر
- `message_text` - متن پیام
- `message_type` - نوع پیام
- `message_date` - تاریخ پیام

### جدول logs
- `id` - شناسه لاگ
- `user_id` - شناسه کاربر
- `action` - عمل انجام شده
- `details` - جزئیات
- `log_date` - تاریخ لاگ

## 📁 ساختار پروژه

```
HeshmatBot/
├── bot.py              # فایل اصلی ربات
├── database.py         # مدیریت دیتابیس MySQL
├── requirements.txt    # وابستگی‌ها
├── setup.py           # فایل نصب
├── .env               # متغیرهای محیطی
├── env_example.txt    # نمونه تنظیمات
├── README.md          # راهنما
└── venv/              # virtual environment
```

## 🔧 توسعه

### اضافه کردن دستور جدید

```python
@bot.message_handler(commands=['new_command'])
def new_command(message):
    bot.reply_to(message, "پیام پاسخ")
```

### اضافه کردن قابلیت جدید

```python
# در فایل database.py
def new_function(self):
    # کد جدید
    pass
```

## 🐛 عیب‌یابی

### مشکلات رایج

1. **خطای اتصال به MySQL:**
   - مطمئن شوید MySQL Server در حال اجرا است
   - تنظیمات دیتابیس را بررسی کنید

2. **خطای توکن:**
   - توکن ربات را از @BotFather دریافت کنید
   - فایل .env را بررسی کنید

3. **خطای نصب:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## 📄 مجوز

این پروژه تحت مجوز MIT منتشر شده است.

## 🤝 مشارکت

برای مشارکت در پروژه:

1. Fork کنید
2. شاخه جدید ایجاد کنید
3. تغییرات را commit کنید
4. Pull Request ارسال کنید

---

**نکته:** این ربات برای اهداف آموزشی ساخته شده است. برای استفاده تجاری، امنیت و قابلیت‌های بیشتری اضافه کنید.
