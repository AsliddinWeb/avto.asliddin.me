import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from django.conf import settings

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TelegramAuthBot:
    """Telegram Authentication Bot"""

    def __init__(self):
        """Bot initialization"""
        self.token = settings.BOT_TOKEN
        if not self.token:
            raise ValueError("BOT_TOKEN not found in settings")

        # Create application
        self.application = Application.builder().token(self.token).build()

        # Setup handlers
        self.setup_handlers()

    def setup_handlers(self):
        """Setup bot command and message handlers"""
        # Import handlers
        from .handlers import (
            start_handler,
            help_handler,
            contact_handler,
            unknown_handler
        )

        # Add command handlers
        self.application.add_handler(CommandHandler("start", start_handler))
        self.application.add_handler(CommandHandler("help", help_handler))

        # Add contact handler
        self.application.add_handler(
            MessageHandler(filters.CONTACT, contact_handler)
        )

        # Add unknown handler (LAST - catches everything else)
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_handler)
        )

        logger.info("Bot handlers setup completed")

    async def test_connection(self):
        """Test bot connection"""
        try:
            bot = self.application.bot
            me = await bot.get_me()
            logger.info(f"✅ Bot connected successfully: @{me.username}")
            return True
        except Exception as e:
            logger.error(f"❌ Bot connection failed: {e}")
            return False

    def run_polling(self):
        """Run bot polling - SODDA USUL"""
        try:
            logger.info("🚀 Starting bot polling...")

            # ENG SODDA USUL
            self.application.run_polling(
                drop_pending_updates=True
            )

        except Exception as e:
            logger.error(f"❌ Bot polling error: {e}")
            raise


# Global bot instance
bot_instance = None


def get_bot():
    """Get bot instance"""
    global bot_instance
    if bot_instance is None:
        bot_instance = TelegramAuthBot()
    return bot_instance