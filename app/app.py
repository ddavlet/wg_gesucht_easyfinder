import os
import threading
from tg_bot.main import start_telegram_bot
from parser.main import start_parser
from database.database import create_database
from dotenv import load_dotenv
# import schedule
import time

def run_parser():
    """Run the parser function and schedule it to run periodically"""
    print("Starting parser thread")
    while True:
        try:
            start_parser()
        except Exception as e:
            print(f"Parser error: {e}")

        # Wait for 5 minutes before next run
        time.sleep(300)

def run_telegram():
    """Run the Telegram bot"""
    print("Starting Telegram bot thread")
    try:
        start_telegram_bot()
    except Exception as e:
        print(f"Telegram bot error: {e}")

def main():
    # Load environment variables
    load_dotenv()

    print("Initializing application...")

    # Initialize database
    try:
        print("Setting up database...")
        create_database()
        print("Database setup complete")
    except Exception as e:
        print(f"Database initialization error: {e}")
        return

    # Create and start parser thread
    parser_thread = threading.Thread(target=run_parser)
    parser_thread.daemon = True
    parser_thread.start()

    # Create and start telegram thread
    # telegram_thread = threading.Thread(target=run_telegram)
    # telegram_thread.daemon = True
    # telegram_thread.start()

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down application...")

if __name__ == "__main__":
    main()
