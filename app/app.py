import os
import asyncio
# from database.tg_bot.main import application
from parser.main import start_parser
from database.database import create_database
from dotenv import load_dotenv
import threading

def run_parser():
    start_parser()

# def load_environment():
#     load_dotenv()
#     print("Initializing application...")

async def main():
    # Load environment variables
    # load_environment()

    # Initialize database (if needed)
    # Uncomment and configure the following lines if you wish to initialize your database
    try:
        print("Setting up database...")
        create_database()
        print("Database setup complete")
    except Exception as e:
        print(f"Database initialization error: {e}")
        return
    # Create and start parser thread
    # parser_thread = threading.Thread(target=run_parser)
    # parser_thread.daemon = True
    # parser_thread.start()
    run_parser()
    # Start the Telegram bot directly in the main thread
    # try:
    #     await application.run_polling()  # Await the coroutine
    # except Exception as e:
    #     print(f"Telegram bot error: {e}")
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down application...")
