@echo off
echo ========================================
echo    راه اندازی دیتابیس HeshmatBot
echo ========================================
echo.

echo در حال اتصال به MySQL...
echo.

REM اجرای دستورات SQL
mysql -u root -pr8_passM < mysql_setup.sql

if %errorlevel% equ 0 (
    echo.
    echo ✅ دیتابیس با موفقیت ایجاد شد!
    echo.
    echo 📊 جداول ایجاد شده:
    echo    - users (کاربران)
    echo    - messages (پیام‌ها)
    echo    - logs (لاگ‌ها)
    echo.
    echo 🚀 حالا می‌توانید ربات را اجرا کنید:
    echo    python bot.py
) else (
    echo.
    echo ❌ خطا در ایجاد دیتابیس!
    echo.
    echo 🔧 بررسی کنید:
    echo    1. MySQL Server در حال اجرا است
    echo    2. رمز عبور root صحیح است
    echo    3. دسترسی‌های لازم وجود دارد
)

echo.
pause
