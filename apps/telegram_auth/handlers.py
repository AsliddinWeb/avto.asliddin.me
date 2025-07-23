from telegram import Update
from telegram.ext import ContextTypes
from channels.db import database_sync_to_async
import logging

logger = logging.getLogger(__name__)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - darhol kontakt so'raydi"""
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id

        logger.info(f"User {user.id} started bot")

        welcome_text = f"""🚗 <b>Avtokontinent.uz ga xush kelibsiz!</b>

Salom {user.first_name}! 

Saytga login qilish uchun kontaktingizni yuboring 👇"""

        # Import keyboard
        from .keyboards import get_contact_keyboard

        await update.message.reply_text(
            welcome_text,
            parse_mode='HTML',
            reply_markup=get_contact_keyboard()
        )

    except Exception as e:
        logger.error(f"Error in start_handler: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi. Qayta urinib ko'ring.")


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    try:
        logger.info(f"Help requested by user {update.effective_user.id}")

        help_text = """🤖 <b>Bot Yordam</b>

Bu bot Avtokontinent.uz saytiga login qilish uchun ishlatiladi.

<b>Jarayon:</b>
1. Saytda "Kod olish" tugmasini bosing
2. Ushbu botga o'ting
3. /start buyrug'ini bosing
4. Kontaktingizni yuboring
5. 5 xonali kod oling
6. Kodni saytga kiriting

<b>Buyruqlar:</b>
/start - Kontakt yuborish
/help - Yordam

❓ Savollar bo'lsa: @support"""

        await update.message.reply_text(
            help_text,
            parse_mode='HTML'
        )

    except Exception as e:
        logger.error(f"Error in help_handler: {e}")
        await update.message.reply_text("❌ Yordam ma'lumotini yuklashda xatolik.")


@database_sync_to_async
def create_user_code(phone_number, chat_id, telegram_username):
    """5 xonali kod yaratish"""
    from apps.telegram_auth.models import UserCode
    from phonenumber_field.phonenumber import PhoneNumber
    import random
    import string

    # Telefon raqamni PhoneNumber formatiga
    try:
        phone_number_obj = PhoneNumber.from_string(phone_number)
    except:
        phone_number_obj = phone_number

    # 5 xonali kod generate qilish
    code_5digit = ''.join(random.choices(string.digits, k=5))

    # Eski kodlarni bekor qilish (bir telefon uchun)
    UserCode.objects.filter(
        phone=phone_number_obj,
        is_used=False
    ).update(is_used=True)

    # Yangi kod yaratish
    user_code = UserCode.objects.create(
        phone=phone_number_obj,
        code=code_5digit,
        telegram_chat_id=chat_id,
        telegram_username=telegram_username,
        is_used=False
    )

    return user_code


async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle contact message - 5 xonali kod beradi"""
    try:
        if not update.message.contact:
            await update.message.reply_text(
                "❌ Iltimos, kontakt tugmasini bosing!"
            )
            return

        # Contact ma'lumotlari
        contact = update.message.contact
        phone = contact.phone_number
        user_id = contact.user_id
        first_name = contact.first_name or "Foydalanuvchi"
        telegram_username = update.effective_user.username
        chat_id = update.effective_chat.id

        logger.info(f"Contact received: {phone} from user {user_id}")

        # Telefon raqamni formatlash
        if not phone.startswith('+'):
            phone = '+' + phone

        # 5 xonali kod yaratish
        user_code = await create_user_code(phone, chat_id, telegram_username)

        logger.info(f"Generated code {user_code.code} for {phone}")

        # Success message with code
        success_text = f"""✅ <b>Muvaffaqiyat!</b>

📞 Telefon: <code>{phone}</code>
👤 Ism: {first_name}

🔢 <b>Sizning login kodingiz:</b>

<b><code>{user_code.code}</code></b>

📱 Bu kodni saytga kiriting va login qiling!
⏰ Kod 2 daqiqa davomida amal qiladi."""

        # Remove keyboard
        from .keyboards import remove_keyboard

        await update.message.reply_text(
            success_text,
            parse_mode='HTML',
            reply_markup=remove_keyboard()
        )

    except Exception as e:
        logger.error(f"Error in contact_handler: {e}")
        await update.message.reply_text(
            "❌ Kontakt qayta ishlashda xatolik. Qayta urinib ko'ring."
        )


async def unknown_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown commands and messages"""
    try:
        user = update.effective_user
        message_text = update.message.text if update.message.text else "multimedia"

        logger.info(f"Unknown message from {user.id}: {message_text}")

        unknown_text = """❓ <b>Noma'lum buyruq</b>

Login qilish uchun:
/start - Kontakt yuborish

Yoki yordam uchun:
/help - Batafsil ma'lumot"""

        await update.message.reply_text(
            unknown_text,
            parse_mode='HTML'
        )

    except Exception as e:
        logger.error(f"Error in unknown_handler: {e}")