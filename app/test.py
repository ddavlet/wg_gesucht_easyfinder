from tg_bot.main import start_telegram_bot


try:
    start_telegram_bot()
except Exception as e:
    print(f"Telegram bot error: {e}")
