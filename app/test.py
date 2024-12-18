from tg_bot.main import start_telegram_bot
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()

print("Loaded Telegram Bot Token:", os.getenv('TELEGRAM_BOT_TOKEN'))
print("Loaded MongoDB Name:", os.getenv('MONGO_DB_NAME'))
print("Loaded MongoDB Admin Username:", os.getenv('MONGO_DB_ADMIN_USERNAME'))
print("Loaded Language File EN Path:", os.getenv('LANGUAGE_FILE_EN'))
print("Loaded Language File DE Path:", os.getenv('LANGUAGE_FILE_DE'))
print("Loaded Language File RU Path:", os.getenv('LANGUAGE_FILE_RU'))
print("Parser Interval:", os.getenv('PARSER_INTERVAL'))

async def main():
    try:
        start_telegram_bot()
    except Exception as e:
        print(f"Telegram bot error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "This event loop is already running" in str(e):
            print("Event loop is already running. Please check your setup.")
        else:
            raise e
