"""
ربات تلگرام HeshmatBot
"""
'''
خب نه این منو رو نگه دار ولی اول باید کاربر داخل ربات ثبت نام کنه
میخوام ورک فلو اینطوری باشه که کاربر وقتی /start رو زد اون پیام اولیه نشون داده بشه 
بعد زیرش یه دکمه بیاد که ثبت نام کنه
اول شماره تلفن ازش بگیره بعد ازش نام و نام خانوادگی 
'''
import telebot
import logging
import os
from datetime import datetime, timedelta
from database import DatabaseManager
from dotenv import load_dotenv
from functools import wraps
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# بارگذاری متغیرهای محیطی
load_dotenv()

# تنظیمات لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# تنظیمات ربات
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
ADMIN_SESSION_DURATION = int(os.getenv('ADMIN_SESSION_DURATION', 3600))  # 1 ساعت

# ایجاد نمونه ربات
bot = telebot.TeleBot(BOT_TOKEN)

# ایجاد نمونه دیتابیس
db = DatabaseManager()

# ذخیره وضعیت کاربران و session های ادمین
user_states = {}
admin_sessions = {}  # {user_id: {'expires': datetime, 'login_time': datetime}}
admin_last_messages = {}  # {user_id: {'chat_id': int, 'message_id': int}}


def is_admin_session_valid(user_id: int) -> bool:
    """بررسی اعتبار session ادمین"""
    if user_id not in admin_sessions:
        return False
    
    session = admin_sessions[user_id]
    if datetime.now() > session['expires']:
        # session منقضی شده
        del admin_sessions[user_id]
        return False
    
    return True


def create_admin_session(user_id: int) -> None:
    """ایجاد session ادمین"""
    expires = datetime.now() + timedelta(seconds=ADMIN_SESSION_DURATION)
    admin_sessions[user_id] = {
        'expires': expires,
        'login_time': datetime.now()
    }
    logger.info(f"Admin session created for user {user_id}")


def admin_required(func):
    """دکوریتور برای دستورات ادمین"""
    @wraps(func)
    def wrapper(message):
        user_id = message.from_user.id
        
        if not is_admin_session_valid(user_id):
            bot.reply_to(message, 
                "🔐 **دسترسی ادمین مورد نیاز**\n\n"
                "برای استفاده از این دستور، ابتدا وارد پنل ادمین شوید:\n"
                "`/admin`", 
                parse_mode='Markdown')
            return
        
        return func(message)
    return wrapper


def cleanup_expired_sessions():
    """پاک کردن session های منقضی شده"""
    current_time = datetime.now()
    expired_users = [
        user_id for user_id, session in admin_sessions.items()
        if current_time > session['expires']
    ]
    
    for user_id in expired_users:
        del admin_sessions[user_id]
        logger.info(f"Admin session expired for user {user_id}")


def remember_admin_message(user_id: int, chat_id: int, message_id: int) -> None:
    """ذخیره آخرین پیام پنل ادمین برای کاربر جهت ویرایش‌های بعدی"""
    admin_last_messages[user_id] = { 'chat_id': chat_id, 'message_id': message_id }


def get_admin_message_ref(user_id: int):
    """دریافت مرجع آخرین پیام ادمین کاربر"""
    return admin_last_messages.get(user_id)


def create_admin_menu():
    """ایجاد منوی ادمین"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # ردیف اول
    keyboard.add(
        InlineKeyboardButton("📊 آمار", callback_data="admin_stats"),
        InlineKeyboardButton("👥 کاربران", callback_data="admin_users")
    )
    
    # ردیف دوم
    keyboard.add(
        InlineKeyboardButton("🛍️ محصولات", callback_data="admin_products"),
        InlineKeyboardButton("🧾 سفارش‌ها", callback_data="admin_orders")
    )
    
    # ردیف سوم
    keyboard.add(
        InlineKeyboardButton("🔐 Session", callback_data="admin_session"),
        InlineKeyboardButton("🔄 تازه‌سازی", callback_data="admin_refresh")
    )
    
    # ردیف چهارم
    keyboard.add(InlineKeyboardButton("🚪 خروج", callback_data="admin_logout"))
    
    return keyboard


def create_back_menu():
    """ایجاد دکمه بازگشت"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 بازگشت به منو", callback_data="admin_menu"))
    return keyboard


def create_main_menu():
    """ایجاد منوی اصلی کاربر زیر پیام خوش‌آمدگویی"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("👤 پروفایل", callback_data="menu_profile"),
        InlineKeyboardButton("🛍️ محصولات", callback_data="menu_products")
    )
    keyboard.add(
        InlineKeyboardButton("👛 کیف پول", callback_data="menu_wallet"),
        InlineKeyboardButton("🧾 سفارشات", callback_data="menu_orders")
    )
    return keyboard


def create_user_back_menu():
    """ایجاد دکمه بازگشت به منوی اصلی کاربر"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_main"))
    return keyboard


def create_beautiful_product_button(product_name, product_id, is_admin=False):
    """ایجاد دکمه زیبا برای محصول"""
    if is_admin:
        icon = "✏️"
        max_length = 60
    else:
        icon = "🛍️"
        max_length = 60
    
    button_text = f"{icon} {product_name}"
    if len(button_text) > max_length:
        button_text = f"{icon} {product_name[:max_length-3]}..."
    
    return InlineKeyboardButton(button_text, callback_data=f"{'manage' if is_admin else 'view'}_product_{product_id}")


def create_product_info_text(product, index, is_admin=False):
    """ایجاد متن زیبا برای اطلاعات محصول"""
    product_name = escape_markdown(product['name'])
    
    if is_admin:
        text = f"**{index}.** 🛍️ **{product_name}**\n"
        text += f"💰 قیمت: {product['price']:,} تومان\n"
        text += f"📅 تاریخ: {product['created_at'].strftime('%Y/%m/%d')}\n\n"
    else:
        text = f"**{index}.** 🛍️ **{product_name}**\n"
        text += f"💰 قیمت: {product['price']:,} تومان\n"
        if product['description']:
            desc = escape_markdown(product['description'][:50])
            text += f"📄 {desc}...\n"
        text += "\n"
    
    return text


def display_products_page(chat_id, message_id, products_data):
    """نمایش صفحه محصولات با pagination"""
    if not products_data['products']:
        text = "🛍️ **محصولات**\n\n❌ هیچ محصولی موجود نیست."
        safe_edit_message(chat_id, message_id, text, reply_markup=create_user_back_menu())
        return
    
    text = f"🛍️ **محصولات موجود**\n\n📄 صفحه {products_data['current_page']} از {products_data['total_pages']}\n\n"
    keyboard = InlineKeyboardMarkup()
    product_buttons = []
    for i, product in enumerate(products_data['products'], 1):
        # اضافه کردن اطلاعات محصول به متن
        text += create_product_info_text(product, i, is_admin=False)
        
        # ساخت دکمه برای محصول
        btn = create_beautiful_product_button(product['name'], product['id'], is_admin=False)
        product_buttons.append(btn)
    
    # اضافه کردن دکمه‌های محصولات به صورت دوتایی
    for i in range(0, len(product_buttons), 2):
        row = product_buttons[i:i+2]  # هر بار 2 تا
        keyboard.add(*row)
    
    # دکمه‌های pagination - همیشه نمایش داده می‌شوند
    pagination_row = []
    
    # دکمه قبلی - اگر صفحه اول نیست، فعال است
    if products_data['current_page'] > 1:
        prev_page = products_data['current_page'] - 1
        pagination_row.append(InlineKeyboardButton("⬅️ صفحه قبلی", callback_data=f"products_page_{prev_page}"))
    else:
        pagination_row.append(InlineKeyboardButton("⬅️ صفحه قبلی", callback_data="noop"))
    
    # دکمه بعدی - اگر صفحه آخر نیست، فعال است
    if products_data['current_page'] < products_data['total_pages']:
        next_page = products_data['current_page'] + 1
        pagination_row.append(InlineKeyboardButton("صفحه بعدی ➡️", callback_data=f"products_page_{next_page}"))
    else:
        pagination_row.append(InlineKeyboardButton("صفحه بعدی ➡️", callback_data="noop"))
    
    keyboard.add(*pagination_row)
    keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="menu_main"))
    safe_edit_message(chat_id, message_id, text, reply_markup=keyboard)


def display_admin_products_page(chat_id, message_id, products_data):
    """نمایش صفحه محصولات ادمین با pagination"""
    if not products_data['products']:
        text = "📋 **لیست محصولات**\n\n❌ هیچ محصولی ثبت نشده است."
        safe_edit_message(chat_id, message_id, text, reply_markup=create_products_menu())
        return
    
    text = f"📋 **لیست محصولات**\n\n📄 صفحه {products_data['current_page']} از {products_data['total_pages']}\n\n"
    keyboard = InlineKeyboardMarkup()
    
    for i, product in enumerate(products_data['products'], 1):
        # اضافه کردن اطلاعات محصول به متن
        text += create_product_info_text(product, i, is_admin=True)
        
        # ایجاد دکمه زیبا برای محصول
        keyboard.add(create_beautiful_product_button(product['name'], product['id'], is_admin=True))
    
    # دکمه‌های pagination - همیشه نمایش داده می‌شوند
    pagination_row = []
    
    # دکمه قبلی - اگر صفحه اول نیست، فعال است
    if products_data['current_page'] > 1:
        prev_page = products_data['current_page'] - 1
        pagination_row.append(InlineKeyboardButton("⬅️ صفحه قبلی", callback_data=f"admin_products_page_{prev_page}"))
    else:
        pagination_row.append(InlineKeyboardButton("⬅️ صفحه قبلی", callback_data="noop"))
    
    # دکمه بعدی - اگر صفحه آخر نیست، فعال است
    if products_data['current_page'] < products_data['total_pages']:
        next_page = products_data['current_page'] + 1
        pagination_row.append(InlineKeyboardButton("صفحه بعدی ➡️", callback_data=f"admin_products_page_{next_page}"))
    else:
        pagination_row.append(InlineKeyboardButton("صفحه بعدی ➡️", callback_data="noop"))
    
    keyboard.add(*pagination_row)
    keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="admin_products"))
    safe_edit_message(chat_id, message_id, text, reply_markup=keyboard)


def create_registration_menu():
    """ایجاد منوی ثبت نام"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📝 ثبت نام", callback_data="start_registration"))
    return keyboard




def create_profile_edit_menu():
    """ایجاد منوی ویرایش پروفایل"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📱 شماره تلفن", callback_data="edit_phone"),
        InlineKeyboardButton("👤 نام", callback_data="edit_first_name")
    )
    keyboard.add(
        InlineKeyboardButton("👥 نام خانوادگی", callback_data="edit_last_name"),
        InlineKeyboardButton("🏙️ شهر", callback_data="edit_city")
    )
    keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="menu_main"))
    return keyboard


def create_products_menu():
    """ایجاد منوی مدیریت محصولات"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ افزودن محصول", callback_data="add_product"),
        InlineKeyboardButton("📋 لیست محصولات", callback_data="list_products")
    )
    keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="admin_menu"))
    return keyboard


def create_product_edit_menu(product_id):
    """ایجاد منوی ویرایش محصول"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✏️ ویرایش نام", callback_data=f"edit_product_name_{product_id}"),
        InlineKeyboardButton("💰 ویرایش قیمت", callback_data=f"edit_product_price_{product_id}")
    )
    keyboard.add(
        InlineKeyboardButton("🖼️ افزودن عکس", callback_data=f"add_product_image_{product_id}"),
        InlineKeyboardButton("📝 ویرایش توضیحات", callback_data=f"edit_product_desc_{product_id}")
    )
    keyboard.add(
        InlineKeyboardButton("🖼️ مدیریت عکس‌ها", callback_data=f"manage_images_{product_id}"),
        InlineKeyboardButton("🗑️ حذف محصول", callback_data=f"delete_product_{product_id}")
    )
    keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="list_products"))
    return keyboard


def escape_markdown(text):
    """Escape کردن کاراکترهای خاص Markdown"""
    if not text:
        return text
    return text.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`').replace(']', '\\]')


def safe_edit_message(chat_id, message_id, text, reply_markup=None, parse_mode='Markdown'):
    """ویرایش امن پیام با مدیریت خطا. در صورت ارسال پیام جدید، همان Message را برمی‌گرداند."""
    try:
        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            parse_mode=parse_mode,
            reply_markup=reply_markup
        )
        return None
    except Exception as e:
        if "message is not modified" in str(e):
            # اگر پیام تغییر نکرده، فقط keyboard را به‌روزرسانی کن
            if reply_markup:
                try:
                    bot.edit_message_reply_markup(
                        chat_id,
                        message_id,
                        reply_markup=reply_markup
                    )
                    return None
                except Exception:
                    # اگر keyboard هم تغییر نکرده، پیام جدید ارسال کن
                    try:
                        return bot.send_message(
                            chat_id,
                            text,
                            parse_mode=parse_mode,
                            reply_markup=reply_markup
                        )
                    except Exception:
                        return None
            return None
        else:
            # اگر خطای دیگری است، پیام جدید ارسال کن
            try:
                return bot.send_message(
                    chat_id,
                    text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup
                )
            except Exception:
                return None


def safe_edit_last_admin_message(user_id: int, text: str, reply_markup=None, parse_mode: str = 'Markdown') -> bool:
    """ویرایش امن آخرین پیام ادمین کاربر. در صورت نبود مرجع، پیام جدید ارسال می‌کند."""
    ref = get_admin_message_ref(user_id)
    if ref:
        new_msg = safe_edit_message(ref['chat_id'], ref['message_id'], text, reply_markup=reply_markup, parse_mode=parse_mode)
        if new_msg:
            try:
                remember_admin_message(user_id, new_msg.chat.id, new_msg.message_id)
            except Exception:
                pass
        return True
    else:
        try:
            sent = bot.send_message(user_id, text, parse_mode=parse_mode, reply_markup=reply_markup)
            remember_admin_message(user_id, sent.chat.id, sent.message_id)
            return True
        except Exception:
            return False


def safe_edit_admin(call, text: str, reply_markup=None, parse_mode: str = 'Markdown'):
    """ویرایش امن پیام ادمین بر اساس callback و به‌روزرسانی مرجع آخرین پیام"""
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    new_msg = safe_edit_message(chat_id, message_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
    if new_msg:
        try:
            remember_admin_message(user_id, new_msg.chat.id, new_msg.message_id)
        except Exception:
            pass
    else:
        try:
            remember_admin_message(user_id, chat_id, message_id)
        except Exception:
            pass

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """پیام خوش‌آمدگویی و بررسی وضعیت ثبت نام"""
    user_id = message.from_user.id
    username = message.from_user.username or "کاربر عزیز"
    first_name = message.from_user.first_name or ""
    
    # ذخیره کاربر در دیتابیس (بدون ثبت نام کامل)
    db.add_user(user_id, username, first_name, message.from_user.last_name or "")
    
    # بررسی اینکه آیا کاربر قبلاً ثبت نام کرده است
    if db.is_user_registered(user_id):
        # کاربر قبلاً ثبت نام کرده - نمایش منو
        welcome_text = f"""
🎉 **سلام {first_name}!** 🎉

✨ به **دهکده مامایی ایران** خوش آمدید! ✨

🚀 از منو زیر گزینه مورد نظرتون رو انتخاب بکنید.
        """
        bot.reply_to(message, welcome_text, parse_mode='Markdown', reply_markup=create_main_menu())
    else:
        # کاربر جدید - نمایش پیام ثبت نام
        welcome_text = f"""
🎉 **سلام {first_name}!** 🎉

✨ به تلگرام **دهکده مامایی ایران** خوش آمدید! ✨

🤖 من یک ربات هوشمند هستم که می‌تونم:
• 💬 با شما چت کنم
• 🧮 محاسبات مالی انجام بدم  
• 📊 آمار و اطلاعات محصولات را به شما ارائه بدم
• 🎯 به سوالات شما پاسخ بدم و تجربه خرید راحت تری برای شما فراهم بکنم

📝 **برای استفاده از تمام امکانات، ابتدا ثبت نام کنید:**
        """
        bot.reply_to(message, welcome_text, parse_mode='Markdown', reply_markup=create_registration_menu())
    
    logger.info(f"User: {username} (ID: {user_id}) - Registered: {db.is_user_registered(user_id)}")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    """پنل ادمین با رمز عبور"""
    user_id = message.from_user.id
    
    # بررسی اینکه آیا کاربر در حال وارد کردن رمز است
    if user_id in user_states and user_states[user_id] == 'waiting_password':
        password = message.text.strip()
        
        if password == ADMIN_PASSWORD:
            # حذف وضعیت انتظار رمز
            del user_states[user_id]
            
            # ایجاد session ادمین
            create_admin_session(user_id)
            
            # ثبت لاگ
            db.add_log(user_id, 'admin_login', 'Successful admin panel login')
            
            admin_text = f"""
🔐 **پنل ادمین** 🔐

✅ **ورود موفق!** خوش آمدید!

⏰ **مدت زمان session:** {ADMIN_SESSION_DURATION // 60} دقیقه

🎯 **منوی ادمین را انتخاب کنید:**
            """
            sent = bot.reply_to(message, admin_text, parse_mode='Markdown', reply_markup=create_admin_menu())
            try:
                remember_admin_message(user_id, sent.chat.id, sent.message_id)
            except Exception:
                pass
        else:
            # ثبت تلاش ناموفق
            db.add_log(user_id, 'admin_login_failed', f'Failed login attempt with password: {password[:3]}***')
            bot.reply_to(message, "❌ رمز عبور اشتباه است! دوباره تلاش کنید.")
            del user_states[user_id]
    else:
        # درخواست رمز عبور
        user_states[user_id] = 'waiting_password'
        bot.reply_to(message, 
            "🔐 **ورود به پنل ادمین**\n\n"
            "لطفاً رمز عبور ادمین را وارد کنید:",
            parse_mode='Markdown')

# دستورات قدیمی ادمین حذف شدند - حالا از منوی تعاملی استفاده می‌شود


@bot.callback_query_handler(func=lambda call: call.data == 'noop')
def handle_noop_callback(call):
    """مدیریت کلیک روی دکمه‌های غیرفعال"""
    bot.answer_callback_query(call.id, "⚠️ این دکمه در حال حاضر غیرفعال است", show_alert=False)
    return

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def handle_admin_callback(call):
    """مدیریت callback های منوی ادمین"""
    user_id = call.from_user.id
    
    # بررسی اعتبار session
    if not is_admin_session_valid(user_id):
        bot.answer_callback_query(call.id, "❌ Session منقضی شده! دوباره وارد شوید.")
        return
    
    if call.data == "admin_menu":
        # نمایش منوی اصلی
        admin_text = f"""
🔐 **پنل ادمین** 🔐

⏰ **مدت زمان session:** {ADMIN_SESSION_DURATION // 60} دقیقه

🎯 **منوی ادمین را انتخاب کنید:**
        """
        safe_edit_admin(call, admin_text, reply_markup=create_admin_menu())
    
    elif call.data == "admin_stats":
        # نمایش آمار
        try:
            total_users = db.get_users_count()
            daily_stats = db.get_daily_stats()
            
            stats_text = f"""
📊 **آمار ربات**

👥 **کاربران:**
• کل کاربران: {total_users}
• کاربران جدید امروز: {daily_stats.get('new_users_today', 0)}
• کاربران فعال امروز: {daily_stats.get('active_users_today', 0)}

💬 **پیام‌ها:**
• پیام‌های امروز: {daily_stats.get('messages_today', 0)}

📅 **زمان:**
• تاریخ: {datetime.now().strftime('%Y/%m/%d')}
• ساعت: {datetime.now().strftime('%H:%M:%S')}

🔧 **وضعیت:** آنلاین ✅
            """
            safe_edit_admin(call, stats_text, reply_markup=create_back_menu())
        except Exception as e:
            bot.answer_callback_query(call.id, f"❌ خطا در دریافت آمار: {str(e)}")
    
    elif call.data == "admin_users":
        # نمایش لیست کاربران
        try:
            users = db.get_all_users()
            if not users:
                users_text = "📝 هیچ کاربری ثبت نشده است."
            else:
                users_text = "👥 **لیست کاربران:**\n\n"
                for i, user in enumerate(users[:10], 1):
                    username = user['username'] or 'بدون نام کاربری'
                    first_name = user['first_name'] or 'نامشخص'
                    join_date = user['join_date'].strftime('%Y/%m/%d') if user['join_date'] else 'نامشخص'
                    # Escape special characters for Markdown
                    username = escape_markdown(username)
                    first_name = escape_markdown(first_name)
                    users_text += f"{i}. {first_name} (@{username})\n📅 {join_date}\n\n"
                
                if len(users) > 10:
                    users_text += f"... و {len(users) - 10} کاربر دیگر"
            
            safe_edit_admin(call, users_text, reply_markup=create_back_menu())
        except Exception as e:
            bot.answer_callback_query(call.id, f"❌ خطا در دریافت لیست کاربران: {str(e)}")
    
    elif call.data == "admin_orders":
        # لیست سفارش‌های در انتظار تایید - صفحه اول
        page = 1
        orders_data = db.get_pending_orders(page, per_page=10)
        text = "🧾 سفارش‌های در انتظار تایید\n\n"
        if not orders_data['orders']:
            text += "هیچ سفارشی در انتظار نیست."
            safe_edit_admin(call, text, reply_markup=create_admin_menu())
            return
        keyboard = InlineKeyboardMarkup()
        for order in orders_data['orders']:
            otext = (
                f"#{order['id']} - {escape_markdown(order['product_name'])} - {order['price']} تومان\n"
                f"کاربر: {escape_markdown(order.get('first_name') or '')} @{escape_markdown(order.get('username') or '-') }\n"
                f"تاریخ: {order['created_at'].strftime('%Y/%m/%d %H:%M')}\n\n"
            )
            text += otext
            keyboard.add(InlineKeyboardButton(f"بررسی سفارش #{order['id']}", callback_data=f"admin_view_order_{order['id']}"))
        # pagination
        pag = []
        if orders_data['current_page'] > 1:
            pag.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"admin_orders_page_{orders_data['current_page']-1}"))
        else:
            pag.append(InlineKeyboardButton("⬅️ قبلی", callback_data="noop"))
        if orders_data['current_page'] < orders_data['total_pages']:
            pag.append(InlineKeyboardButton("بعدی ➡️", callback_data=f"admin_orders_page_{orders_data['current_page']+1}"))
        else:
            pag.append(InlineKeyboardButton("بعدی ➡️", callback_data="noop"))
        keyboard.add(*pag)
        keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="admin_menu"))
        safe_edit_admin(call, text, reply_markup=keyboard)

    elif call.data.startswith("admin_orders_page_"):
        page = int(call.data.replace("admin_orders_page_", ""))
        orders_data = db.get_pending_orders(page, per_page=10)
        text = "🧾 سفارش‌های در انتظار تایید\n\n"
        keyboard = InlineKeyboardMarkup()
        if not orders_data['orders']:
            text += "در این صفحه سفارشی نیست."
        else:
            for order in orders_data['orders']:
                otext = (
                    f"#{order['id']} - {escape_markdown(order['product_name'])} - {order['price']} تومان\n"
                    f"کاربر: {escape_markdown(order.get('first_name') or '')} @{escape_markdown(order.get('username') or '-') }\n"
                    f"تاریخ: {order['created_at'].strftime('%Y/%m/%d %H:%M')}\n\n"
                )
                text += otext
                keyboard.add(InlineKeyboardButton(f"بررسی سفارش #{order['id']}", callback_data=f"admin_view_order_{order['id']}"))
        pag = []
        if orders_data['current_page'] > 1:
            pag.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"admin_orders_page_{orders_data['current_page']-1}"))
        else:
            pag.append(InlineKeyboardButton("⬅️ قبلی", callback_data="noop"))
        if orders_data['current_page'] < orders_data['total_pages']:
            pag.append(InlineKeyboardButton("بعدی ➡️", callback_data=f"admin_orders_page_{orders_data['current_page']+1}"))
        else:
            pag.append(InlineKeyboardButton("بعدی ➡️", callback_data="noop"))
        keyboard.add(*pag)
        keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="admin_menu"))
        safe_edit_admin(call, text, reply_markup=keyboard)

    elif call.data.startswith("admin_view_order_"):
        try:
            order_id = int(call.data.replace("admin_view_order_", ""))
            order = db.get_order(order_id)
            if not order:
                bot.answer_callback_query(call.id, "❌ سفارش یافت نشد")
                return
            text = (
                f"🧾 سفارش #{order['id']}\n\n"
                f"محصول: {escape_markdown(order['product_name'])}\n"
                f"مبلغ: {order['price']} تومان\n"
                f"وضعیت: {order['status']}\n"
                f"تاریخ: {order['created_at'].strftime('%Y/%m/%d %H:%M')}\n"
            )
            keyboard = InlineKeyboardMarkup()
            if order.get('screenshot_file_id'):
                keyboard.add(InlineKeyboardButton("مشاهده اسکرین‌شات", callback_data=f"admin_view_orders_ss_{order['id']}"))
            keyboard.add(
                InlineKeyboardButton("✅ تایید", callback_data=f"admin_approve_order_{order['id']}"),
                InlineKeyboardButton("❌ رد", callback_data=f"admin_reject_order_{order['id']}"),
            )
            keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="admin_orders"))
            safe_edit_admin(call, text, reply_markup=keyboard)
        except ValueError:
            bot.answer_callback_query(call.id, "❌ داده نامعتبر")
            logger.error(f"Invalid callback data for admin_view_order: {call.data}")
            return

    elif call.data.startswith("admin_view_orders_ss_"):
        try:
            order_id = int(call.data.replace("admin_view_orders_ss_", ""))
            order = db.get_order(order_id)
            if order and order.get('screenshot_file_id'):
                keyboard = InlineKeyboardMarkup()
                keyboard.add(
                    InlineKeyboardButton("✅ تایید", callback_data=f"admin_approve_order_{order_id}"),
                    InlineKeyboardButton("❌ رد", callback_data=f"admin_reject_order_{order_id}")
                )
                keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data=f"admin_view_order_{order_id}"))
                caption = (
                    f"🧾 سفارش #{order_id}\n"
                    f"اسکرین‌شات پرداخت"
                )
                bot.send_photo(
                    call.message.chat.id,
                    order['screenshot_file_id'],
                    caption=caption,
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
            else:
                bot.answer_callback_query(call.id, "❌ اسکرین‌شات موجود نیست")
        except ValueError:
            bot.answer_callback_query(call.id, "❌ داده نامعتبر")
            logger.error(f"Invalid callback data for admin_view_order_ss: {call.data}")
            return

    elif call.data.startswith("admin_approve_order_"):
        order_id = int(call.data.replace("admin_approve_order_", ""))
        if db.update_order_status(order_id, 'approved', admin_id=user_id):
            try:
                order = db.get_order(order_id)
                if order:
                    bot.send_message(order['user_id'], f"✅ سفارش #{order_id} شما تایید شد و در صف ارسال است.")
            except:
                pass
            bot.answer_callback_query(call.id, "✅ سفارش تایید شد")
            # refresh view
            order = db.get_order(order_id)
            if order:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🔙 بازگشت", callback_data="admin_orders")
                ))
        else:
            bot.answer_callback_query(call.id, "❌ خطا در تایید سفارش")

    elif call.data.startswith("admin_reject_order_"):
        order_id = int(call.data.replace("admin_reject_order_", ""))
        # رد بدون دلیل متنی در این نسخه ساده
        if db.update_order_status(order_id, 'rejected', admin_id=user_id, rejection_reason='rejected by admin'):
            try:
                order = db.get_order(order_id)
                if order:
                    bot.send_message(order['user_id'], f"❌ سفارش #{order_id} شما رد شد. در صورت مشکل با پشتیبانی تماس بگیرید.")
            except:
                pass
            bot.answer_callback_query(call.id, "✅ سفارش رد شد")
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 بازگشت", callback_data="admin_orders")
            ))
        else:
            bot.answer_callback_query(call.id, "❌ خطا در رد سفارش")

    elif call.data == "admin_broadcast":
        # درخواست پیام برای ارسال
        user_states[user_id] = 'waiting_broadcast'
        broadcast_text = """
📢 **ارسال پیام به همه کاربران**

لطفاً پیام خود را ارسال کنید:
        """
        safe_edit_admin(call, broadcast_text, reply_markup=create_back_menu())
    
    elif call.data == "admin_session":
        # نمایش اطلاعات session
        session = admin_sessions[user_id]
        login_time = session['login_time'].strftime('%H:%M:%S')
        expires_time = session['expires'].strftime('%H:%M:%S')
        remaining_time = session['expires'] - datetime.now()
        remaining_minutes = int(remaining_time.total_seconds() // 60)
        
        session_text = f"""
🔐 **اطلاعات Session ادمین**

⏰ **زمان ورود:** {login_time}
⏳ **انقضا:** {expires_time}
⏱️ **زمان باقی‌مانده:** {remaining_minutes} دقیقه

💡 برای تمدید session، دوباره `/admin` را اجرا کنید.
        """
        safe_edit_admin(call, session_text, reply_markup=create_back_menu())
    
    elif call.data == "admin_refresh":
        # تازه‌سازی منو
        admin_text = f"""
🔐 **پنل ادمین** 🔐

⏰ **مدت زمان session:** {ADMIN_SESSION_DURATION // 60} دقیقه

🎯 **منوی ادمین را انتخاب کنید:**
        """
        safe_edit_admin(call, admin_text, reply_markup=create_admin_menu())
        bot.answer_callback_query(call.id, "🔄 منو تازه‌سازی شد!")
    
    elif call.data == "admin_products":
        # مدیریت محصولات
        products_count = db.get_products_count()
        products_text = f"""
🛍️ **مدیریت محصولات**

📊 **آمار:**
• تعداد محصولات فعال: {products_count}

🎯 **عملیات:**
        """
        safe_edit_admin(call, products_text, reply_markup=create_products_menu())
    
    elif call.data == "admin_logout":
        # خروج از پنل ادمین
        db.add_log(user_id, 'admin_logout', 'خروج از پنل ادمین')
        del admin_sessions[user_id]
        
        logout_text = "👋 **خروج موفق!** از پنل ادمین خارج شدید."
        safe_edit_admin(call, logout_text)
        bot.answer_callback_query(call.id, "👋 خروج موفق!")


@bot.callback_query_handler(func=lambda call: call.data.startswith('products_page_'))
def handle_products_pagination_callback(call):
    """مدیریت pagination محصولات کاربران"""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    try:
        # تغییر صفحه محصولات
        page = int(call.data.replace("products_page_", ""))
        logger.info(f"Products page callback: {call.data}, page: {page}")
        print(f"DEBUG: Products page callback: {call.data}, page: {page}")
        products_data = db.get_products_paginated(page, per_page=5)
        logger.info(f"Products data: {products_data}")
        print(f"DEBUG: Products data: {products_data}")
        
        # بررسی اینکه آیا محصولات وجود دارند
        if not products_data['products']:
            bot.answer_callback_query(call.id, "❌ هیچ محصولی در این صفحه وجود ندارد")
            return
            
        display_products_page(chat_id, message_id, products_data)
        bot.answer_callback_query(call.id, f"صفحه {page} از {products_data['total_pages']}")
    except Exception as e:
        logger.error(f"خطا در pagination محصولات: {e}")
        print(f"DEBUG ERROR: {e}")
        bot.answer_callback_query(call.id, f"❌ خطا در تغییر صفحه: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('menu_'))
def handle_user_menu_callback(call):
    """مدیریت منوی اصلی کاربر (پروفایل، محصولات، کیف پول، سفارشات)"""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    user_id = call.from_user.id

    if call.data == 'menu_main':
        # بازگشت به منوی اصلی
        main_text = (
            "🎯 **منوی اصلی**\n\n"
            "از گزینه‌های زیر یکی را انتخاب کنید:"
        )
        safe_edit_message(chat_id, message_id, main_text, reply_markup=create_main_menu())
        return

    if call.data == 'menu_profile':
        # نمایش اطلاعات پروفایل
        user_info = db.get_user(user_id)
        if user_info and user_info.get('is_registered'):
            profile_text = f"""
👤 **پروفایل شما**

📱 **شماره تلفن:** {user_info.get('phone', 'ثبت نشده')}
👤 **نام:** {user_info.get('first_name', 'ثبت نشده')}
👥 **نام خانوادگی:** {user_info.get('last_name', 'ثبت نشده')}
🏙️ **شهر:** {user_info.get('city', 'ثبت نشده')}

📅 **تاریخ عضویت:** {user_info.get('join_date', '').strftime('%Y/%m/%d') if user_info.get('join_date') else 'نامشخص'}
            """
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("✏️ ویرایش پروفایل", callback_data="edit_profile"))
            keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="menu_main"))
            safe_edit_message(chat_id, message_id, profile_text, reply_markup=keyboard)
        else:
            text = "❌ شما هنوز ثبت نام نکرده‌اید. ابتدا ثبت نام کنید."
            safe_edit_message(chat_id, message_id, text, reply_markup=create_user_back_menu())
        return

    if call.data == 'menu_products':
        # نمایش محصولات - صفحه اول
        page = 1
        products_data = db.get_products_paginated(page, per_page=5)
        display_products_page(chat_id, message_id, products_data)
        return

    if call.data == 'menu_wallet':
        text = (
            "👛 **کیف پول**\n\n"
            "موجودی و تراکنش‌ها به‌زودی نمایش داده می‌شود."
        )
        safe_edit_message(chat_id, message_id, text, reply_markup=create_user_back_menu())
        return

    if call.data == 'menu_orders':
        orders = db.get_user_orders(user_id)
        if not orders:
            text = (
                "🧾 **سفارشات**\n\n"
                "هنوز سفارشی ثبت نکرده‌اید."
            )
            safe_edit_message(chat_id, message_id, text, reply_markup=create_user_back_menu())
            return
        text = "🧾 **سفارشات شما**\n\n"
        status_map = { 'pending': '⏳ در انتظار', 'approved': '✅ تایید شده', 'rejected': '❌ رد شده' }
        for o in orders:
            text += (
                f"#{o['id']} - {escape_markdown(o['product_name'])}\n"
                f"وضعیت: {status_map.get(o['status'], o['status'])}\n"
                f"مبلغ: {o['price']} تومان\n"
                f"تاریخ: {o['created_at'].strftime('%Y/%m/%d %H:%M')}\n\n"
            )
        safe_edit_message(chat_id, message_id, text, reply_markup=create_user_back_menu())
        return


@bot.callback_query_handler(func=lambda call: call.data.startswith('images_page_'))
def handle_images_pagination_callback(call):
    """مدیریت pagination عکس‌های محصولات"""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    try:
        # تغییر صفحه عکس‌ها
        parts = call.data.replace("images_page_", "").split("_")
        product_id = int(parts[0])
        page = int(parts[1])
        logger.info(f"Images page callback: {call.data}, product_id: {product_id}, page: {page}")
        print(f"DEBUG: Images page callback: {call.data}, product_id: {product_id}, page: {page}")
        
        # دریافت اطلاعات محصول
        product = db.get_product(product_id)
        if not product:
            bot.send_message(chat_id, "❌ محصول یافت نشد!", reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 بازگشت به محصولات", callback_data="menu_products")
            ))
            bot.answer_callback_query(call.id)
            return
        
        # دریافت عکس‌ها با pagination
        images_data = db.get_product_images_paginated(product_id, page, per_page=1)
        logger.info(f"Images data: {images_data}")
        print(f"DEBUG: Images data: {images_data}")
        
        if not images_data['images']:
            bot.send_message(chat_id, "❌ هیچ عکسی یافت نشد!", reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 بازگشت به محصول", callback_data=f"view_product_{product_id}")
            ))
            bot.answer_callback_query(call.id)
            return
        
        # حذف پیام قبلی
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        
        # ارسال فقط اولین عکس با pagination
        if images_data['images']:
            first_image = images_data['images'][0]
            keyboard = InlineKeyboardMarkup()
            
            # دکمه‌های pagination - همیشه نمایش داده می‌شوند
            pagination_row = []
            
            # دکمه قبلی - اگر صفحه اول نیست، فعال است
            if page > 1:
                prev_page = page - 1
                pagination_row.append(InlineKeyboardButton("⬅️ عکس قبلی", callback_data=f"images_page_{product_id}_{prev_page}"))
            else:
                pagination_row.append(InlineKeyboardButton("⬅️ عکس قبلی", callback_data="noop"))
            
            # دکمه بعدی - اگر صفحه آخر نیست، فعال است
            if page < images_data['total_pages']:
                next_page = page + 1
                pagination_row.append(InlineKeyboardButton("عکس بعدی ➡️", callback_data=f"images_page_{product_id}_{next_page}"))
            else:
                pagination_row.append(InlineKeyboardButton("عکس بعدی ➡️", callback_data="noop"))
            
            keyboard.add(*pagination_row)
            keyboard.add(InlineKeyboardButton("🛒 خرید", callback_data=f"buy_product_{product_id}"))
            keyboard.add(InlineKeyboardButton("🔙 بازگشت به محصول", callback_data=f"view_product_{product_id}"))
            
            bot.send_photo(
                chat_id, 
                first_image['file_id'], 
                caption=f"📸 **{escape_markdown(product['name'])}**\n\nعکس 1 از {len(images_data['images'])} (صفحه {page} از {images_data['total_pages']})",
                parse_mode='Markdown',
                reply_markup=keyboard
            )
            
        bot.answer_callback_query(call.id, f"صفحه {page} از {images_data['total_pages']}")
                
    except Exception as e:
        logger.error(f"خطا در pagination عکس‌ها: {e}")
        print(f"DEBUG ERROR: {e}")
        bot.answer_callback_query(call.id, f"❌ خطا در تغییر صفحه عکس‌ها: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('view_all_images_'))
def handle_view_all_images_callback(call):
    """مشاهده عکس‌های محصول با pagination"""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    try:
        # شروع مشاهده عکس‌ها
        product_id = int(call.data.replace("view_all_images_", ""))
        page = 1
        logger.info(f"View all images callback: {call.data}, product_id: {product_id}, page: {page}")
        
        # دریافت اطلاعات محصول
        product = db.get_product(product_id)
        if not product:
            bot.send_message(chat_id, "❌ محصول یافت نشد!", reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 بازگشت به محصولات", callback_data="menu_products")
            ))
            bot.answer_callback_query(call.id)
            return
        
        # دریافت عکس‌ها با pagination
        images_data = db.get_product_images_paginated(product_id, page, per_page=1)
        logger.info(f"Images data: {images_data}")
        
        if not images_data['images']:
            bot.send_message(chat_id, "❌ هیچ عکسی یافت نشد!", reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 بازگشت به محصول", callback_data=f"view_product_{product_id}")
            ))
            bot.answer_callback_query(call.id)
            return
        
        # حذف پیام قبلی
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        
        # ارسال فقط اولین عکس با pagination
        if images_data['images']:
            first_image = images_data['images'][0]
            keyboard = InlineKeyboardMarkup()
            
            # دکمه‌های pagination - همیشه نمایش داده می‌شوند
            pagination_row = []
            
            # دکمه قبلی - اگر صفحه اول نیست، فعال است
            if page > 1:
                prev_page = page - 1
                pagination_row.append(InlineKeyboardButton("⬅️ عکس قبلی", callback_data=f"images_page_{product_id}_{prev_page}"))
            else:
                pagination_row.append(InlineKeyboardButton("⬅️ عکس قبلی", callback_data="noop"))
            
            # دکمه بعدی - اگر صفحه آخر نیست، فعال است
            if page < images_data['total_pages']:
                next_page = page + 1
                pagination_row.append(InlineKeyboardButton("عکس بعدی ➡️", callback_data=f"images_page_{product_id}_{next_page}"))
            else:
                pagination_row.append(InlineKeyboardButton("عکس بعدی ➡️", callback_data="noop"))
            
            keyboard.add(*pagination_row)
            keyboard.add(InlineKeyboardButton("🔙 بازگشت به محصول", callback_data=f"view_product_{product_id}"))
            
            bot.send_photo(
                chat_id, 
                first_image['file_id'], 
                caption=f"📸 **{escape_markdown(product['name'])}**\n\nعکس 1 از {len(images_data['images'])} (صفحه {page} از {images_data['total_pages']})",
                parse_mode='Markdown',
                reply_markup=keyboard
            )
            
        bot.answer_callback_query(call.id, f"صفحه {page} از {images_data['total_pages']}")
                    
    except Exception as e:
        logger.error(f"خطا در نمایش عکس‌ها: {e}")
        bot.answer_callback_query(call.id, f"❌ خطا در نمایش عکس‌ها: {str(e)}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('view_product_'))
def handle_view_product_callback(call):
    """نمایش جزئیات محصول"""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    product_id = int(call.data.replace("view_product_", ""))
    
    product = db.get_product_with_images(product_id)
    if product:
        # ایجاد متن محصول
        text = f"""
🛍️ **{escape_markdown(product['name'])}**

💰 **قیمت:** {product['price']:,} تومان

{f"📄 **توضیحات:**\n{escape_markdown(product['description'])}" if product['description'] else "📄 **توضیحات:** ندارد"}

📅 **تاریخ اضافه شدن:** {product['created_at'].strftime('%Y/%m/%d')}
        """
        
        # ارسال عکس‌ها اگر وجود دارند
        if product.get('images'):
            try:
                # حذف پیام قبلی
                try:
                    bot.delete_message(chat_id, message_id)
                except:
                    pass
                
                # اضافه کردن اطلاعات عکس‌ها به متن
                image_count = len(product['images'])
                text_with_images = text + f"\n\n🖼️ **عکس‌ها:** {image_count} عکس"
                
                # ارسال اولین عکس با کپشن کامل
                first_image = product['images'][0]
                keyboard = InlineKeyboardMarkup()
                keyboard.add(InlineKeyboardButton("🛒 خرید این محصول", callback_data=f"buy_product_{product_id}"))
                keyboard.add(InlineKeyboardButton("🔙 بازگشت به محصولات", callback_data="menu_products"))
                
                # اگر بیش از یک عکس داریم، دکمه مشاهده همه عکس‌ها اضافه کن
                if image_count > 1:
                    keyboard.add(InlineKeyboardButton(f"📸 مشاهده همه عکس‌ها ({image_count})", callback_data=f"view_all_images_{product_id}"))
                
                bot.send_photo(
                    chat_id,
                    first_image['file_id'],
                    caption=text_with_images,
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
                    
            except Exception as e:
                logger.error(f"خطا در ارسال عکس محصول: {e}")
                # اگر ارسال عکس ناموفق بود، متن را ارسال کن
                safe_edit_message(chat_id, message_id, text + "\n\n❌ خطا در نمایش عکس‌ها", reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🔙 بازگشت به محصولات", callback_data="menu_products")
                ))
        else:
            # اگر عکسی وجود ندارد، فقط متن را نمایش بده
            safe_edit_message(chat_id, message_id, text, reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🛒 خرید این محصول", callback_data=f"buy_product_{product_id}"),
                InlineKeyboardButton("🔙 بازگشت به محصولات", callback_data="menu_products")
            ))
    else:
        safe_edit_message(chat_id, message_id, "❌ محصول یافت نشد!", reply_markup=create_user_back_menu())


@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_product_'))
def handle_buy_product_callback(call):
    """شروع فرآیند خرید: درخواست ارسال اسکرین‌شات و ثبت وضعیت کاربر"""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    user_id = call.from_user.id
    try:
        product_id = int(call.data.replace("buy_product_", ""))
    except Exception:
        bot.answer_callback_query(call.id, "❌ داده نامعتبر")
        return

    product = db.get_product(product_id)
    if not product:
        safe_edit_message(chat_id, message_id, "❌ محصول یافت نشد!", reply_markup=create_user_back_menu())
        return

    # ذخیره وضعیت برای انتظار عکس پرداخت
    user_states[user_id] = {
        'action': 'buying_product',
        'product_id': product_id,
        'price': float(product['price'])
    }

    text = (
        f"🛒 خرید محصول: {escape_markdown(product['name'])}\n\n"
        f"💰 مبلغ: {product['price']:,} تومان\n\n"
        "لطفاً پس از واریز مبلغ، اسکرین‌شات پرداخت را به همین چت ارسال کنید.\n\n"
        "پس از ارسال، سفارش شما در وضعیت در انتظار تایید قرار می‌گیرد و پس از تایید ادمین، پیام تایید دریافت خواهید کرد."
    )
    safe_edit_message(chat_id, message_id, text, reply_markup=InlineKeyboardMarkup().add(
        InlineKeyboardButton("❌ لغو", callback_data=f"view_product_{product_id}")
    ))
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith(('start_registration', 'cancel_registration', 'skip_phone', 'skip_city', 'skip_image', 'skip_description')) or call.data in ['edit_phone', 'edit_first_name', 'edit_last_name', 'edit_city', 'edit_profile'])
def handle_registration_and_edit_callback(call):
    """مدیریت ثبت نام و ویرایش پروفایل"""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    user_id = call.from_user.id

    if call.data == 'start_registration':
        # شروع فرآیند ثبت نام ساده
        user_states[user_id] = 'waiting_name'
        text = (
            "📝 **ثبت نام سریع**\n\n"
            "👤 لطفاً نام و نام خانوادگی خود را در یک پیام ارسال کنید:\n\n"
            "مثال: علی احمدی"
        )
        safe_edit_message(chat_id, message_id, text, reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("❌ لغو", callback_data="cancel_registration")
        ))
        return

    elif call.data == 'cancel_registration':
        # لغو ثبت نام
        if user_id in user_states:
            del user_states[user_id]
        text = "❌ ثبت نام لغو شد."
        safe_edit_message(chat_id, message_id, text, reply_markup=create_registration_menu())
        return

    elif call.data == 'skip_phone':
        # رد کردن شماره تلفن و رفتن به شهر
        if user_id in user_states and isinstance(user_states[user_id], dict):
            user_states[user_id]['phone'] = None
            user_states[user_id]['step'] = 'waiting_city'
            
            text = (
                "✅ شماره تلفن رد شد\n\n"
                "🏙️ **شهر (اختیاری):**\n"
                "شهر خود را ارسال کنید یا Enter بزنید تا رد شود:"
            )
            safe_edit_message(chat_id, message_id, text, reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("⏭️ رد کردن", callback_data="skip_city"),
                InlineKeyboardButton("❌ لغو", callback_data="cancel_registration")
            ))
        return

    elif call.data == 'skip_city':
        # رد کردن شهر و تکمیل ثبت نام
        if user_id in user_states and isinstance(user_states[user_id], dict):
            user_data = user_states[user_id].copy()
            
            # ثبت نام در دیتابیس
            if db.register_user(
                user_id, 
                user_data['first_name'],
                user_data['last_name'],
                user_data.get('phone'),
                None
            ):
                # حذف وضعیت ثبت نام
                del user_states[user_id]
                
                success_text = f"""
✅ **ثبت نام با موفقیت تکمیل شد!**

👤 **اطلاعات شما:**
👤 نام: {user_data['first_name']} {user_data['last_name']}
{f"📱 شماره تلفن: {user_data.get('phone')}" if user_data.get('phone') else "📱 شماره تلفن: ثبت نشده"}
🏙️ شهر: ثبت نشده

🎉 حالا می‌توانید از تمام امکانات ربات استفاده کنید!
                """
                safe_edit_message(chat_id, message_id, success_text, reply_markup=create_main_menu())
            else:
                safe_edit_message(chat_id, message_id, "❌ خطا در ثبت نام. لطفاً دوباره تلاش کنید.")
        return

    elif call.data == 'skip_image':
        # رد کردن عکس محصول
        if user_id in user_states and isinstance(user_states[user_id], dict) and user_states[user_id].get('action') == 'adding_product':
            user_states[user_id]['image_url'] = None
            user_states[user_id]['step'] = 'waiting_description'
            
            text = (
                "✅ عکس محصول رد شد\n\n"
                "📝 **مرحله 4/4: توضیحات محصول (اختیاری)**\n"
                "توضیحات محصول را ارسال کنید یا Enter بزنید تا رد شود:"
            )
            safe_edit_message(chat_id, message_id, text, reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("⏭️ رد کردن", callback_data="skip_description"),
                InlineKeyboardButton("❌ لغو", callback_data="admin_products")
            ))
        return

    elif call.data == 'skip_description':
        # رد کردن توضیحات و تکمیل افزودن محصول
        if user_id in user_states and isinstance(user_states[user_id], dict) and user_states[user_id].get('action') == 'adding_product':
            user_data = user_states[user_id].copy()
            user_data['description'] = None
            
            # ذخیره محصول در دیتابیس
            if db.add_product(
                user_data['name'],
                user_data['price'],
                user_data.get('image_url'),
                user_data.get('description')
            ):
                # ثبت لاگ افزودن موفق (skip توضیحات)
                try:
                    db.add_log(user_id, 'product_add_success', f'افزودن محصول جدید (skip توضیحات): {user_data["name"]} - {user_data["price"]:,} تومان')
                except:
                    pass
                del user_states[user_id]
                success_text = f"""
✅ **محصول با موفقیت اضافه شد!**

🛍️ **اطلاعات محصول:**
📝 نام: {user_data['name']}
💰 قیمت: {user_data['price']:,} تومان
🖼️ عکس: {'✅' if user_data.get('image_url') else '❌'}
📄 توضیحات: ❌
                """
                safe_edit_message(chat_id, message_id, success_text, reply_markup=create_products_menu())
            else:
                # ثبت لاگ خطا در افزودن
                try:
                    db.add_log(user_id, 'product_add_failed', f'خطا در افزودن محصول (skip توضیحات): {user_data["name"]}')
                except:
                    pass
                safe_edit_message(chat_id, message_id, "❌ خطا در افزودن محصول. لطفاً دوباره تلاش کنید.")
        return

    elif call.data == 'edit_profile':
        # نمایش منوی ویرایش پروفایل
        text = "✏️ **ویرایش پروفایل**\n\nکدام فیلد را می‌خواهید ویرایش کنید؟"
        safe_edit_message(chat_id, message_id, text, reply_markup=create_profile_edit_menu())
        return

    elif call.data.startswith('edit_'):
        # شروع ویرایش فیلد خاص
        field = call.data.replace('edit_', '')
        field_names = {
            'phone': 'شماره تلفن',
            'first_name': 'نام',
            'last_name': 'نام خانوادگی',
            'city': 'شهر'
        }
        
        if field in field_names:
            user_states[user_id] = f'editing_{field}'
            text = f"✏️ **ویرایش {field_names[field]}**\n\nلطفاً {field_names[field]} جدید را ارسال کنید:"
            safe_edit_message(chat_id, message_id, text, reply_markup=create_user_back_menu())
        return


@bot.callback_query_handler(func=lambda call: call.data.startswith(('add_product_image_', 'manage_images_', 'delete_image_')))
def handle_image_management_callback(call):
    """مدیریت عکس‌های محصولات"""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    user_id = call.from_user.id
    
    # Debug log
    logger.info(f"Image management callback: {call.data} from user {user_id}")
    
    # بررسی اعتبار session
    if not is_admin_session_valid(user_id):
        logger.warning(f"Admin session invalid for user {user_id} in image management")
        bot.answer_callback_query(call.id, "❌ Session منقضی شده! دوباره وارد شوید.")
        return
    
    bot.answer_callback_query(call.id)
    
    if call.data.startswith("add_product_image_"):
        # افزودن عکس جدید به محصول
        product_id = int(call.data.replace("add_product_image_", ""))
        user_states[user_id] = {'action': 'adding_image', 'product_id': product_id}
        
        text = f"🖼️ **افزودن عکس جدید به محصول**\n\nعکس جدید را ارسال کنید:"
        safe_edit_message(chat_id, message_id, text, reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("❌ لغو", callback_data=f"manage_product_{product_id}")
        ))
        return

    elif call.data.startswith("manage_images_"):
        # مدیریت عکس‌های محصول
        product_id = int(call.data.replace("manage_images_", ""))
        images = db.get_product_images(product_id)
        
        if not images:
            text = "🖼️ **مدیریت عکس‌های محصول**\n\n❌ هیچ عکسی برای این محصول وجود ندارد."
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("➕ افزودن عکس", callback_data=f"add_product_image_{product_id}"))
            keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data=f"manage_product_{product_id}"))
        else:
            text = f"🖼️ **مدیریت عکس‌های محصول**\n\n📊 تعداد عکس‌ها: {len(images)}\n\n"
            keyboard = InlineKeyboardMarkup()
            
            for i, img in enumerate(images[:5], 1):  # حداکثر 5 عکس
                keyboard.add(InlineKeyboardButton(
                    f"🗑️ حذف عکس {i}", 
                    callback_data=f"delete_image_{img['id']}"
                ))
            
            keyboard.add(InlineKeyboardButton("➕ افزودن عکس", callback_data=f"add_product_image_{product_id}"))
            keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data=f"manage_product_{product_id}"))
        
        safe_edit_message(chat_id, message_id, text, reply_markup=keyboard)
        return

    elif call.data.startswith("delete_image_"):
        # حذف عکس محصول
        image_id = int(call.data.replace("delete_image_", ""))
        
        if db.delete_product_image(image_id):
            text = "✅ عکس با موفقیت حذف شد!"
            safe_edit_message(chat_id, message_id, text, reply_markup=create_products_menu())
        else:
            text = "❌ خطا در حذف عکس!"
            safe_edit_message(chat_id, message_id, text, reply_markup=create_products_menu())
        return



@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_products_page_'))
def handle_admin_products_pagination_callback(call):
    """مدیریت pagination محصولات ادمین"""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    try:
        # تغییر صفحه محصولات ادمین
        page = int(call.data.replace("admin_products_page_", ""))
        logger.info(f"Admin products page callback: {call.data}, page: {page}")
        print(f"DEBUG: Admin products page callback: {call.data}, page: {page}")
        products_data = db.get_products_paginated(page, per_page=10)
        logger.info(f"Admin products data: {products_data}")
        print(f"DEBUG: Admin products data: {products_data}")
        
        # بررسی اینکه آیا محصولات وجود دارند
        if not products_data['products']:
            bot.answer_callback_query(call.id, "❌ هیچ محصولی در این صفحه وجود ندارد")
            return
            
        display_admin_products_page(chat_id, message_id, products_data)
        bot.answer_callback_query(call.id, f"صفحه {page} از {products_data['total_pages']}")
    except Exception as e:
        logger.error(f"خطا در pagination محصولات ادمین: {e}")
        print(f"DEBUG ERROR: {e}")
        bot.answer_callback_query(call.id, f"❌ خطا در تغییر صفحه محصولات: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith(('add_product', 'list_products', 'manage_product_', 'edit_product_', 'delete_product_')))
def handle_products_callback(call):
    """مدیریت محصولات"""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    user_id = call.from_user.id
    
    # Debug log
    logger.info(f"Products callback: {call.data} from user {user_id}")
    
    # بررسی اعتبار session
    if not is_admin_session_valid(user_id):
        logger.warning(f"Admin session invalid for user {user_id}")
        bot.answer_callback_query(call.id, "❌ Session منقضی شده! دوباره وارد شوید.")
        return
    
    # پاسخ به callback query
    bot.answer_callback_query(call.id)

    if call.data == "add_product":
        # شروع افزودن محصول
        user_states[user_id] = {'action': 'adding_product', 'step': 'waiting_name'}
        text = (
            "➕ **افزودن محصول جدید**\n\n"
            "📝 **مرحله 1/4: نام محصول**\n"
            "لطفاً نام محصول را ارسال کنید:"
        )
        safe_edit_message(chat_id, message_id, text, reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("❌ لغو", callback_data="admin_products")
        ))
        return

    elif call.data == "list_products":
        # نمایش لیست محصولات - صفحه اول
        page = 1
        products_data = db.get_products_paginated(page, per_page=10)
        display_admin_products_page(chat_id, message_id, products_data)
        return
    

    elif call.data.startswith("manage_product_"):
        # مدیریت یک محصول خاص
        product_id = int(call.data.replace("manage_product_", ""))
        product = db.get_product(product_id)
        
        if product:
            # دریافت عکس‌های محصول
            images = db.get_product_images(product_id)
            image_count = len(images)
            
            text = f"""
🛍️ **مدیریت محصول**

📝 **نام:** {escape_markdown(product['name'])}
💰 **قیمت:** {product['price']:,} تومان
🖼️ **عکس‌ها:** {image_count} عکس {'✅' if image_count > 0 else '❌'}
📄 **توضیحات:** {'✅' if product['description'] else '❌'}
📅 **تاریخ ایجاد:** {product['created_at'].strftime('%Y/%m/%d %H:%M')}
            """
            safe_edit_message(chat_id, message_id, text, reply_markup=create_product_edit_menu(product_id))
        else:
            safe_edit_message(chat_id, message_id, "❌ محصول یافت نشد!", reply_markup=create_products_menu())
        
        return

    elif call.data.startswith("edit_product_name_"):
        # ویرایش نام محصول
        product_id = int(call.data.replace("edit_product_name_", ""))
        user_states[user_id] = {'action': 'editing_product', 'product_id': product_id, 'field': 'name'}
        
        text = f"✏️ **ویرایش نام محصول**\n\nنام جدید را ارسال کنید:"
        safe_edit_message(chat_id, message_id, text, reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("❌ لغو", callback_data=f"manage_product_{product_id}")
        ))
        return

    elif call.data.startswith("edit_product_price_"):
        # ویرایش قیمت محصول
        product_id = int(call.data.replace("edit_product_price_", ""))
        user_states[user_id] = {'action': 'editing_product', 'product_id': product_id, 'field': 'price'}
        
        text = f"💰 **ویرایش قیمت محصول**\n\nقیمت جدید را به تومان ارسال کنید:"
        safe_edit_message(chat_id, message_id, text, reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("❌ لغو", callback_data=f"manage_product_{product_id}")
        ))
        return

    elif call.data.startswith("edit_product_image_"):
        # ویرایش عکس محصول
        product_id = int(call.data.replace("edit_product_image_", ""))
        user_states[user_id] = {'action': 'editing_product', 'product_id': product_id, 'field': 'image_url'}
        
        text = f"🖼️ **ویرایش عکس محصول**\n\nعکس جدید را ارسال کنید یا لینک عکس را وارد کنید:"
        safe_edit_message(chat_id, message_id, text, reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("❌ لغو", callback_data=f"manage_product_{product_id}")
        ))
        return

    elif call.data.startswith("edit_product_desc_"):
        # ویرایش توضیحات محصول
        product_id = int(call.data.replace("edit_product_desc_", ""))
        user_states[user_id] = {'action': 'editing_product', 'product_id': product_id, 'field': 'description'}
        
        text = f"📝 **ویرایش توضیحات محصول**\n\nتوضیحات جدید را ارسال کنید:"
        safe_edit_message(chat_id, message_id, text, reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("❌ لغو", callback_data=f"manage_product_{product_id}")
        ))
        return

    elif call.data.startswith("delete_product_"):
        # حذف محصول
        product_id = int(call.data.replace("delete_product_", ""))
        product = db.get_product(product_id)
        
        if product and db.delete_product(product_id):
            # ثبت لاگ حذف موفق
            try:
                db.add_log(user_id, 'product_delete_success', f'حذف محصول {product_id} ({product["name"]}) توسط ادمین')
            except:
                pass
            text = f"✅ محصول '{product['name']}' با موفقیت حذف شد!"
            safe_edit_message(chat_id, message_id, text, reply_markup=create_products_menu())
        else:
            # ثبت لاگ خطا در حذف
            try:
                db.add_log(user_id, 'product_delete_failed', f'خطا در حذف محصول {product_id}')
            except:
                pass
            text = "❌ خطا در حذف محصول!"
            safe_edit_message(chat_id, message_id, text, reply_markup=create_products_menu())
        
        return


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    """مدیریت آپلود عکس برای محصولات و پرداخت سفارش"""
    user_id = message.from_user.id
    
    # Debug log
    logger.info(f"Photo received from user {user_id}, user_states: {user_states.get(user_id)}")
    
    # بررسی اینکه آیا کاربر در حال اضافه کردن عکس به محصول است
    if user_id in user_states and isinstance(user_states[user_id], dict):
        user_data = user_states[user_id]
        
        if user_data.get('action') == 'adding_product' and user_data.get('step') == 'waiting_image':
            # ذخیره اطلاعات عکس
            photo = message.photo[-1]  # بزرگترین سایز عکس
            user_states[user_id]['image_file_id'] = photo.file_id
            user_states[user_id]['image_file_unique_id'] = photo.file_unique_id
            user_states[user_id]['image_file_size'] = photo.file_size
            user_states[user_id]['image_width'] = photo.width
            user_states[user_id]['image_height'] = photo.height
            user_states[user_id]['step'] = 'waiting_description'
            
            text = (
                f"✅ عکس محصول دریافت شد!\n\n"
                f"📏 سایز: {photo.width}x{photo.height}\n"
                f"📁 حجم: {photo.file_size} بایت\n\n"
                f"📝 **مرحله 4/4: توضیحات محصول (اختیاری)**\n"
                f"توضیحات محصول را ارسال کنید یا Enter بزنید تا رد شود:"
            )
            safe_edit_last_admin_message(
                user_id,
                text,
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("⏭️ رد کردن", callback_data="skip_description"),
                    InlineKeyboardButton("❌ لغو", callback_data="admin_products")
                )
            )
            return
        
        elif user_data.get('action') == 'editing_product' and user_data.get('field') == 'image_url':
            # افزودن عکس جدید به محصول (از منوی ویرایش)
            product_id = user_data['product_id']
            photo = message.photo[-1]
            
            # اضافه کردن عکس جدید (بدون حذف عکس‌های قبلی)
            if db.add_product_image(
                product_id, 
                photo.file_id, 
                photo.file_unique_id, 
                photo.file_size, 
                photo.width, 
                photo.height
            ):
                del user_states[user_id]
                product = db.get_product_with_images(product_id)
                if product:
                    success_text = f"✅ عکس جدید با موفقیت اضافه شد!\n\n📏 سایز: {photo.width}x{photo.height}\n📊 تعداد کل عکس‌ها: {len(product.get('images', []))}"
                    safe_edit_last_admin_message(user_id, success_text, reply_markup=create_product_edit_menu(product_id))
                else:
                    safe_edit_last_admin_message(user_id, "✅ عکس اضافه شد!", reply_markup=create_products_menu())
            else:
                safe_edit_last_admin_message(user_id, "❌ خطا در اضافه کردن عکس. لطفاً دوباره تلاش کنید.")
            return
        
        elif user_data.get('action') == 'adding_image':
            # افزودن عکس جدید به محصول (از منوی مدیریت عکس‌ها)
            product_id = user_data['product_id']
            photo = message.photo[-1]
            
            # اضافه کردن عکس جدید
            if db.add_product_image(
                product_id, 
                photo.file_id, 
                photo.file_unique_id, 
                photo.file_size, 
                photo.width, 
                photo.height
            ):
                del user_states[user_id]
                product = db.get_product_with_images(product_id)
                if product:
                    success_text = f"✅ عکس جدید با موفقیت اضافه شد!\n\n📏 سایز: {photo.width}x{photo.height}\n📊 تعداد کل عکس‌ها: {len(product.get('images', []))}"
                    safe_edit_last_admin_message(user_id, success_text, reply_markup=create_product_edit_menu(product_id))
                else:
                    safe_edit_last_admin_message(user_id, "✅ عکس اضافه شد!", reply_markup=create_products_menu())
            else:
                safe_edit_last_admin_message(user_id, "❌ خطا در اضافه کردن عکس. لطفاً دوباره تلاش کنید.")
            return

        elif user_data.get('action') == 'buying_product':
            # دریافت اسکرین‌شات پرداخت و ایجاد سفارش در انتظار تایید
            product_id = user_data['product_id']
            price = user_data['price']
            photo = message.photo[-1]
            order_id = db.create_order(user_id, product_id, price, photo.file_id)
            if order_id:
                del user_states[user_id]
                confirm_text = (
                    f"✅ اسکرین‌شات پرداخت دریافت شد.\n\n"
                    f"🧾 شناسه سفارش: #{order_id}\n"
                    "⏳ سفارش شما در وضعیت در انتظار تایید است. پس از تایید ادمین، پیام تایید برای شما ارسال خواهد شد."
                )
                safe_edit_last_admin_message(user_id, confirm_text, reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🧾 مشاهده سفارشات", callback_data="menu_orders")
                ))
            else:
                safe_edit_last_admin_message(user_id, "❌ خطا در ثبت سفارش. لطفاً دوباره تلاش کنید.")
            return
    
    # اگر عکس برای محصول ارسال نشده، پیام پیش‌فرض
    try:
        bot.reply_to(message, "📸 عکس دریافت شد!")
    except Exception:
        pass


@bot.message_handler(commands=['help'])
def send_help(message):
    """راهنمای دستورات"""
    help_text = """
📋 **دستورات موجود:**

🔹 **دستورات عمومی:**
• /start - شروع کار با ربات
• /help - نمایش این راهنما

🔹 **دستورات ادمین:**
• /admin - ورود به پنل ادمین (با منوی تعاملی)

💡 **نکته:** برای استفاده از پنل ادمین، ابتدا /admin را اجرا کنید.
    """
    bot.reply_to(message, help_text, parse_mode='Markdown')



@bot.message_handler(func=lambda message: True)
def handle_text(message):
    """پردازش پیام‌های متنی"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    # بررسی وضعیت کاربر
    if user_id in user_states and user_states[user_id] == 'waiting_password':
        # کاربر در حال وارد کردن رمز است
        admin_panel(message)
        return
    
    elif user_id in user_states and user_states[user_id] == 'waiting_broadcast':
        # کاربر در حال ارسال پیام broadcast است
        if is_admin_session_valid(user_id):
            broadcast_text = message.text.strip()
            if not broadcast_text:
                bot.reply_to(message, "❌ لطفاً پیام خود را ارسال کنید.")
                return
            
            try:
                users = db.get_all_users()
                sent_count = 0
                failed_count = 0
                
                # ارسال پیام به صورت تدریجی
                for user in users:
                    try:
                        bot.send_message(user['user_id'], f"📢 **پیام ادمین:**\n\n{broadcast_text}", parse_mode='Markdown')
                        sent_count += 1
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"خطا در ارسال پیام به کاربر {user['user_id']}: {e}")
                
                # ثبت لاگ
                db.add_log(user_id, 'broadcast_sent', f'ارسال پیام به {sent_count} کاربر')
                
                result_text = f"""
✅ **ارسال پیام تکمیل شد**

📊 **نتایج:**
• ارسال موفق: {sent_count}
• ارسال ناموفق: {failed_count}
• کل کاربران: {len(users)}
                """
                safe_edit_last_admin_message(user_id, result_text, reply_markup=create_back_menu())
                
            except Exception as e:
                logger.error(f"خطا در ارسال پیام عمومی: {e}")
                safe_edit_last_admin_message(user_id, f"❌ خطا در ارسال پیام: {str(e)}")
            
            # حذف وضعیت انتظار
            del user_states[user_id]
        else:
            safe_edit_last_admin_message(user_id, "❌ Session ادمین منقضی شده! دوباره وارد شوید.")
            del user_states[user_id]
        return
    
    elif user_id in user_states and user_states[user_id] == 'waiting_name':
        # دریافت نام و نام خانوادگی
        name_parts = text.strip().split()
        if len(name_parts) < 2:
            bot.reply_to(message, 
                "❌ لطفاً نام و نام خانوادگی را با فاصله جدا کنید:\n\nمثال: علی احمدی",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("❌ لغو", callback_data="cancel_registration")
                )
            )
            return
        
        first_name = name_parts[0]
        last_name = ' '.join(name_parts[1:])
        
        # ذخیره نام و درخواست شماره تلفن
        user_states[user_id] = {
            'first_name': first_name,
            'last_name': last_name,
            'step': 'waiting_phone'
        }
        
        bot.reply_to(message, 
            f"✅ نام دریافت شد: {first_name} {last_name}\n\n"
            "📱 **شماره تلفن (اختیاری):**\n"
            "شماره تلفن خود را ارسال کنید یا Enter بزنید تا رد شود:",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("⏭️ رد کردن", callback_data="skip_phone"),
                InlineKeyboardButton("❌ لغو", callback_data="cancel_registration")
            )
        )
        return
    
    elif user_id in user_states and isinstance(user_states[user_id], dict) and user_states[user_id].get('step') == 'waiting_phone':
        # دریافت شماره تلفن
        user_data = user_states[user_id].copy()
        phone = text.strip() if text.strip() else None
        
        # ذخیره شماره تلفن و درخواست شهر
        user_states[user_id]['phone'] = phone
        user_states[user_id]['step'] = 'waiting_city'
        
        bot.reply_to(message, 
            f"✅ شماره تلفن دریافت شد: {phone if phone else 'رد شد'}\n\n"
            "🏙️ **شهر (اختیاری):**\n"
            "شهر خود را ارسال کنید یا Enter بزنید تا رد شود:",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("⏭️ رد کردن", callback_data="skip_city"),
                InlineKeyboardButton("❌ لغو", callback_data="cancel_registration")
            )
        )
        return
    
    elif user_id in user_states and isinstance(user_states[user_id], dict) and user_states[user_id].get('step') == 'waiting_city':
        # دریافت شهر و تکمیل ثبت نام
        user_data = user_states[user_id].copy()
        city = text.strip() if text.strip() else None
        
        # ثبت نام در دیتابیس
        if db.register_user(
            user_id, 
            user_data['first_name'],
            user_data['last_name'],
            user_data.get('phone'),
            city
        ):
            # حذف وضعیت ثبت نام
            del user_states[user_id]
            
            success_text = f"""
✅ **ثبت نام با موفقیت تکمیل شد!**

👤 **اطلاعات شما:**
👤 نام: {user_data['first_name']} {user_data['last_name']}
{f"📱 شماره تلفن: {user_data.get('phone')}" if user_data.get('phone') else "📱 شماره تلفن: ثبت نشده"}
{f"🏙️ شهر: {city}" if city else "🏙️ شهر: ثبت نشده"}

🎉 حالا می‌توانید از تمام امکانات ربات استفاده کنید!
            """
            bot.reply_to(message, success_text, parse_mode='Markdown', reply_markup=create_main_menu())
        else:
            bot.reply_to(message, "❌ خطا در ثبت نام. لطفاً دوباره تلاش کنید.")
        return
    
    elif user_id in user_states and isinstance(user_states[user_id], str) and user_states[user_id].startswith('editing_'):
        # ویرایش پروفایل
        field = user_states[user_id].replace('editing_', '')
        
        if db.update_user_profile(user_id, **{field: text}):
            del user_states[user_id]
            bot.reply_to(message, f"✅ {field} با موفقیت به‌روزرسانی شد!", reply_markup=create_main_menu())
        else:
            bot.reply_to(message, f"❌ خطا در به‌روزرسانی {field}. لطفاً دوباره تلاش کنید.")
        return
    
    elif user_id in user_states and isinstance(user_states[user_id], dict) and user_states[user_id].get('action') == 'adding_product':
        # افزودن محصول
        step = user_states[user_id].get('step')
        
        if step == 'waiting_name':
            # دریافت نام محصول
            user_states[user_id]['name'] = text
            user_states[user_id]['step'] = 'waiting_price'
            bot.reply_to(message, 
                f"✅ نام محصول دریافت شد: {text}\n\n"
                "💰 **مرحله 2/4: قیمت محصول**\n"
                "قیمت محصول را به تومان ارسال کنید:",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("❌ لغو", callback_data="admin_products")
                )
            )
            return
        
        elif step == 'waiting_price':
            # دریافت قیمت محصول
            try:
                price = float(text.replace(',', ''))
                user_states[user_id]['price'] = price
                user_states[user_id]['step'] = 'waiting_image'
                bot.reply_to(message, 
                f"✅ قیمت محصول دریافت شد: {price:,} تومان\n\n"
                "🖼️ **مرحله 3/4: عکس محصول (اختیاری)**\n"
                "عکس محصول را ارسال کنید یا لینک عکس را وارد کنید:",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("⏭️ رد کردن", callback_data="skip_image"),
                    InlineKeyboardButton("❌ لغو", callback_data="admin_products")
                    )
                )
            except ValueError:
                bot.reply_to(message, "❌ لطفاً قیمت معتبر وارد کنید (مثال: 50000)")
            return
        
        elif step == 'waiting_image':
            # دریافت لینک عکس محصول (اختیاری)
            user_states[user_id]['image_url'] = text if text.strip() else None
            user_states[user_id]['step'] = 'waiting_description'
            bot.reply_to(message, 
                f"✅ لینک عکس محصول دریافت شد: {'✅' if user_states[user_id]['image_url'] else 'رد شد'}\n\n"
                "📝 **مرحله 4/4: توضیحات محصول (اختیاری)**\n"
                "توضیحات محصول را ارسال کنید یا Enter بزنید تا رد شود:",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("⏭️ رد کردن", callback_data="skip_description"),
                    InlineKeyboardButton("❌ لغو", callback_data="admin_products")
                )
            )
            return
        
        elif step == 'waiting_description':
            # تکمیل افزودن محصول
            user_states[user_id]['description'] = text if text.strip() else None
            
            # ذخیره محصول در دیتابیس
            product_data = user_states[user_id].copy()
            if db.add_product(
                product_data['name'],
                product_data['price'],
                product_data.get('image_url'),
                product_data.get('description')
            ):
                # دریافت ID محصول جدید
                products = db.get_all_products()
                new_product_id = products[0]['id'] if products else None
                
                # اضافه کردن عکس اگر وجود دارد
                if new_product_id and product_data.get('image_file_id'):
                    db.add_product_image(
                        new_product_id,
                        product_data['image_file_id'],
                        product_data['image_file_unique_id'],
                        product_data.get('image_file_size'),
                        product_data.get('image_width'),
                        product_data.get('image_height')
                    )
                
                # ثبت لاگ افزودن موفق
                try:
                    db.add_log(user_id, 'product_add_success', f'افزودن محصول جدید: {product_data["name"]} - {product_data["price"]:,} تومان')
                except:
                    pass  # اگر user_id وجود نداشت، لاگ را نادیده بگیر
                
                del user_states[user_id]
                success_text = f"""
✅ **محصول با موفقیت اضافه شد!**

🛍️ **اطلاعات محصول:**
📝 نام: {product_data['name']}
💰 قیمت: {product_data['price']:,} تومان
🖼️ عکس: {'✅' if product_data.get('image_file_id') or product_data.get('image_url') else '❌'}
📄 توضیحات: {'✅' if product_data.get('description') else '❌'}
                """
                bot.reply_to(message, success_text, reply_markup=create_products_menu())
            else:
                # ثبت لاگ خطا در افزودن
                try:
                    db.add_log(user_id, 'product_add_failed', f'خطا در افزودن محصول: {product_data["name"]}')
                except:
                    pass
                bot.reply_to(message, "❌ خطا در افزودن محصول. لطفاً دوباره تلاش کنید.")
        return
    
    elif user_id in user_states and isinstance(user_states[user_id], dict) and user_states[user_id].get('action') == 'editing_product':
        # ویرایش محصول
        product_id = user_states[user_id]['product_id']
        field = user_states[user_id]['field']
        
        # تبدیل قیمت اگر لازم باشد
        if field == 'price':
            try:
                text = float(text.replace(',', ''))
            except ValueError:
                bot.reply_to(message, "❌ لطفاً قیمت معتبر وارد کنید (مثال: 50000)")
                return
        
        if db.update_product(product_id, **{field: text}):
            # ثبت لاگ موفقیت‌آمیز
            field_names = {
                'name': 'نام',
                'price': 'قیمت',
                'image_url': 'عکس',
                'description': 'توضیحات'
            }
            field_name = field_names.get(field, field)
            try:
                db.add_log(user_id, 'product_edit_success', f'ویرایش {field_name} محصول {product_id} توسط ادمین')
            except:
                pass
            
            del user_states[user_id]
            product = db.get_product(product_id)
            if product:
                success_text = f"✅ {field_name} محصول با موفقیت به‌روزرسانی شد!"
                bot.reply_to(message, success_text, reply_markup=create_product_edit_menu(product_id))
            else:
                bot.reply_to(message, "✅ به‌روزرسانی موفق!", reply_markup=create_products_menu())
        else:
            # ثبت لاگ خطا
            try:
                db.add_log(user_id, 'product_edit_failed', f'خطا در ویرایش {field} محصول {product_id}')
            except:
                pass
            bot.reply_to(message, f"❌ خطا در به‌روزرسانی {field}. لطفاً دوباره تلاش کنید.")
        return
    
    # پاسخ‌های هوشمند
    if any(word in text for word in ['سلام', 'hello', 'hi']):
        bot.reply_to(message, "👋 سلام! چطور می‌تونم کمکتون کنم؟")
    
    elif any(word in text for word in ['خداحافظ', 'bye', 'goodbye']):
        bot.reply_to(message, "👋 خداحافظ! امیدوارم دوباره ببینمتون.")
    
    elif any(word in text for word in ['چطوری', 'حال', 'چطور']):
        bot.reply_to(message, "😊 من خوبم! ممنون که پرسیدید. شما چطورید؟")
    
    elif any(word in text for word in ['ممنون', 'تشکر', 'thanks']):
        bot.reply_to(message, "😊 خواهش می‌کنم! خوشحالم که تونستم کمکتون کنم.")
    
    else:
        # پاسخ پیش‌فرض
        responses = [
            "🤔 جالب! بیشتر توضیح بدید.",
            "😊 متوجه شدم. چیز دیگه‌ای هم هست؟",
            "👍 خوبه! سوال دیگه‌ای دارید؟",
            "💭 عالی! من اینجا هستم تا کمکتون کنم."
        ]
        import random
        bot.reply_to(message, random.choice(responses))


def main():
    """تابع اصلی برای اجرای ربات"""
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info("🚀 Start the robot...")
            print("🤖HeshmatBot Telegram bot launched!")
            print("🔐The admin system is enabled with session management.")
            print("⏰Admin session duration:", ADMIN_SESSION_DURATION // 60, "Min")
            print("To stop the bot, press Ctrl+C.")
            
            # پاک کردن session های منقضی شده
            cleanup_expired_sessions()
            
            # شروع polling با تنظیمات بهتر
            bot.infinity_polling(
                timeout=30,  # افزایش timeout
                long_polling_timeout=60,  # افزایش long polling timeout
                none_stop=True,  # عدم توقف در صورت خطا
                interval=1,  # کاهش interval
                skip_pending=True,  # رد کردن پیام‌های pending
                allowed_updates=['message', 'callback_query']
            )
            
        except KeyboardInterrupt:
            logger.info("⏹️ The robot stopped.")
            print("\n👋 The robot stopped.")
            break
        except Exception as e:
            retry_count += 1
            logger.error(f"❌ Error running the robot (attempt {retry_count}/{max_retries}): {str(e)}")
            print(f"❌ خطا (تلاش {retry_count}/{max_retries}): {str(e)}")
            
            if retry_count < max_retries:
                wait_time = min(30, retry_count * 10)  # افزایش تدریجی زمان انتظار
                logger.info(f"🔄 Restarting bot in {wait_time} seconds...")
                print(f"🔄 ربات در {wait_time} ثانیه دوباره راه‌اندازی می‌شود...")
                import time
                time.sleep(wait_time)
            else:
                logger.error("❌ Maximum retry attempts reached. Bot stopped.")
                print("❌ حداکثر تلاش‌ها انجام شد. ربات متوقف شد.")
                break
        finally:
            # بستن اتصال دیتابیس
            db.close_connection()

if __name__ == '__main__':
    main()
