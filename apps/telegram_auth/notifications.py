# apps/telegram_auth/notifications.py
import asyncio
import logging
from telegram import Bot
from django.conf import settings
from asgiref.sync import sync_to_async
import traceback

logger = logging.getLogger(__name__)


class TelegramNotificationService:
    """Telegram orqali xabar yuborish servisi"""

    def __init__(self):
        self.bot_token = getattr(settings, 'BOT_TOKEN', None)
        self.bot = None

        if self.bot_token:
            self.bot = Bot(token=self.bot_token)
        else:
            logger.error("BOT_TOKEN not found in settings")

    async def send_message_async(self, chat_id, message, parse_mode='HTML'):
        """Async xabar yuborish"""
        if not self.bot:
            logger.error("Bot not initialized")
            return False

        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=parse_mode
            )
            logger.info(f"Message sent to {chat_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send message to {chat_id}: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    def send_message_sync(self, chat_id, message, parse_mode='HTML'):
        """Sync wrapper for async message sending"""
        try:
            # Django context da async function ishlatish
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.send_message_async(chat_id, message, parse_mode)
            )
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Sync send message error: {str(e)}")
            return False

    def send_order_status_notification(self, order, old_status, new_status, admin_user=None):
        """Buyurtma status o'zgarishi haqida xabar"""
        if not order.user.telegram_chat_id:
            logger.warning(f"User {order.user.phone} has no telegram_chat_id")
            return False

        # Status display names
        status_names = {
            'pending': 'Kutilmoqda',
            'payment_pending': 'To\'lov kutilmoqda',
            'confirmed': 'Tasdiqlandi',
            'preparing': 'Tayyorlanmoqda',
            'shipped': 'Jo\'natildi',
            'delivered': 'Yetkazildi',
            'cancelled': 'Bekor qilindi',
            'payment_rejected': 'To\'lov rad etildi'
        }

        # Status emoji
        status_emojis = {
            'pending': '⏳',
            'payment_pending': '💳',
            'confirmed': '✅',
            'preparing': '📦',
            'shipped': '🚚',
            'delivered': '🎉',
            'cancelled': '❌',
            'payment_rejected': '❌'
        }

        old_status_name = status_names.get(old_status, old_status)
        new_status_name = status_names.get(new_status, new_status)
        new_status_emoji = status_emojis.get(new_status, '📝')

        # Admin info
        admin_info = ""
        if admin_user:
            admin_name = admin_user.get_full_name() or admin_user.username
            admin_info = f"\n👤 <i>O'zgartirdi: {admin_name}</i>"

        # Message yaratish
        message = f"""
{new_status_emoji} <b>Buyurtma holati o'zgarti!</b>

📋 <b>Buyurtma:</b> #{order.order_number}
💰 <b>Summa:</b> {order.formatted_total_som}

📊 <b>Holat o'zgarishi:</b>
• <i>Eski:</i> {old_status_name}
• <i>Yangi:</i> <b>{new_status_name}</b>

📅 <i>Vaqt:</i> {order.updated_at.strftime('%d.%m.%Y %H:%M')}{admin_info}
        """.strip()

        # Special messages for specific statuses
        if new_status == 'confirmed':
            message += "\n\n🎉 <b>Ajoyib!</b> Buyurtmangiz tasdiqlandi va tez orada tayyorlanadi."

        elif new_status == 'shipped':
            message += "\n\n🚚 <b>Buyurtmangiz yo'lda!</b> Tez orada sizga yetkaziladi."

        elif new_status == 'delivered':
            message += "\n\n🎉 <b>Tabriklaymiz!</b> Buyurtmangiz muvaffaqiyatli yetkazildi.\n💬 Agar xohlasangiz, mahsulotga sharh qoldiring!"

        elif new_status == 'cancelled':
            message += "\n\n😔 Afsuski buyurtmangiz bekor qilindi.\n📞 Savollar bo'lsa +998 (XX) XXX-XX-XX ga qo'ng'iroq qiling."

        elif new_status == 'payment_rejected':
            message += "\n\n❌ To'lov rad etildi. Iltimos to'lovni qayta amalga oshiring yoki biz bilan bog'laning."

        # Footer
        message += f"\n\n🌐 <a href='https://avtokontinent.uz/orders/{order.order_number}/'>Buyurtmani ko'rish</a>"

        # Send message
        return self.send_message_sync(
            chat_id=order.user.telegram_chat_id,
            message=message,
            parse_mode='HTML'
        )

    def send_payment_confirmation_notification(self, order):
        """To'lov tasdiqlanganda xabar"""
        if not order.user.telegram_chat_id:
            return False

        message = f"""
✅ <b>To'lov tasdiqlandi!</b>

📋 <b>Buyurtma:</b> #{order.order_number}
💰 <b>Summa:</b> {order.formatted_total_som}

🎉 To'lovingiz muvaffaqiyatli qabul qilindi!
📦 Buyurtmangiz tez orada tayyorlanadi.

📅 <i>Vaqt:</i> {order.updated_at.strftime('%d.%m.%Y %H:%M')}

🌐 <a href='https://avtokontinent.uz/orders/{order.order_number}/'>Buyurtmani ko'rish</a>
        """.strip()

        return self.send_message_sync(
            chat_id=order.user.telegram_chat_id,
            message=message,
            parse_mode='HTML'
        )


# Global instance
notification_service = TelegramNotificationService()