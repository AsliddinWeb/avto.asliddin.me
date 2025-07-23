from django.core.management.base import BaseCommand
from apps.telegram_auth.bot import get_bot
import asyncio


class Command(BaseCommand):
    help = 'Start Telegram Auth Bot'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-only',
            action='store_true',
            help='Only test connection',
        )

    def handle(self, *args, **options):
        """Run bot"""
        self.stdout.write("🤖 Starting Telegram Auth Bot...")

        try:
            bot = get_bot()

            if options['test_only']:
                # Test only
                async def test():
                    success = await bot.test_connection()
                    if success:
                        self.stdout.write(self.style.SUCCESS("✅ Connection test passed"))
                    else:
                        self.stdout.write(self.style.ERROR("❌ Connection test failed"))

                asyncio.run(test())
            else:
                # Run bot - SYNC USUL
                self.stdout.write("🚀 Starting bot polling...")
                bot.run_polling()  # Bu sync method

        except KeyboardInterrupt:
            self.stdout.write("\n🛑 Bot stopped")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))