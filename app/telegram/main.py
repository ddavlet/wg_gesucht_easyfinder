import json
import os
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters  # Note: 'filters' is lowercase in v20+
)
from dotenv import load_dotenv
from database.user_manager import UserManager
from pymongo import MongoClient

load_dotenv()

# Connect to MongoDB
# MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
# client = MongoClient(MONGODB_URI)
# db = client[os.getenv('MONGO_DB_NAME', 'app_db')]

# Load environment variables
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
LANGUAGE_FILES = {
    'en': os.getenv('LANGUAGE_FILE_EN'),
    'de': os.getenv('LANGUAGE_FILE_DE'),
    'ru': os.getenv('LANGUAGE_FILE_RU')
}

# Load language files
with open(LANGUAGE_FILES['en'], 'r') as f:
    en_texts = json.load(f)
with open(LANGUAGE_FILES['de'], 'r') as f:
    de_texts = json.load(f)
with open(LANGUAGE_FILES['ru'], 'r') as f:
    ru_texts = json.load(f)

# Initialize bot
updater = Updater(TOKEN)
dispatcher = updater.dispatcher

# In-memory user settings
user_manager = UserManager()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    existing_user = user_manager.get_user(chat_id)

    if existing_user and existing_user.get('is_active', False):
        context.bot.send_message(
            chat_id=chat_id,
            text=eval(f"{existing_user['language']}_texts")['registration']['already_registered']
        )
        return

    user_data = {
        'chat_id': chat_id,
        'language': 'en',
        'city': None,
        'distance': None,
        'is_active': True,
        'settings': {
            'notifications': True,
            'language': 'en'
        }
    }
    user_manager.save_user(chat_id, user_data)
    context.bot.send_message(chat_id=chat_id, text=en_texts['start'])

def set_language(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    keyboard = [
        [InlineKeyboardButton("English", callback_data='lang_en')],
        [InlineKeyboardButton("Deutsch", callback_data='lang_de')],
        [InlineKeyboardButton("Русский", callback_data='lang_ru')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=chat_id, text="Choose your language:", reply_markup=reply_markup)

def button(update: Update, context: CallbackContext):
    query = update.callback_query
    chat_id = query.message.chat_id
    query.answer()

    if query.data.startswith('lang_'):
        lang = query.data.split('_')[1]
        user_data = user_manager.get_user(chat_id)
        if user_data:
            user_data['language'] = lang
            user_data['settings']['language'] = lang
            user_manager.save_user(chat_id, user_data)
            context.bot.send_message(
                chat_id=chat_id,
                text=eval(f"{lang}_texts")['settings']['language_changed']
            )

def register(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user_data = user_manager.get_user(chat_id)
    if user_data:
        city = update.message.text.split(' ', 1)[1]
        user_data['city'] = city
        user_manager.save_user(chat_id, user_data)
        context.bot.send_message(
            chat_id=chat_id,
            text=eval(f"{user_data['language']}_texts")['settings']['city_set'].format(city=city)
        )

def set_settings(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    settings = json.loads(update.message.text.split(' ', 1)[1])
    user_data = user_manager.get_user(chat_id)
    if user_data:
        user_data.update(settings)
        user_manager.save_user(chat_id, user_data)
        context.bot.send_message(
            chat_id=chat_id,
            text=eval(f"{user_data['language']}_texts")['settings']['updated']
        )

def stop(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user_data = user_manager.get_user(chat_id)
    if user_data:
        user_manager.deactivate_user(chat_id)
        context.bot.send_message(
            chat_id=chat_id,
            text=eval(f"{user_data['language']}_texts")['account']['stopped']
        )

def delete_account(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user_data = user_manager.get_user(chat_id)
    if user_data:
        user_manager.delete_user(chat_id)
        context.bot.send_message(
            chat_id=chat_id,
            text=eval(f"{user_data['language']}_texts")['account']['deleted']
        )

def check_user_registered(func):
    def wrapper(update: Update, context: CallbackContext):
        chat_id = update.message.chat_id
        user_data = user_manager.get_user(chat_id)

        if not user_data or not user_data.get('is_active', False):
            context.bot.send_message(
                chat_id=chat_id,
                text="Please send /start to register and use the bot."
            )
            return
        return func(update, context)
    return wrapper

# Apply decorator to all command handlers that require registration
@check_user_registered
def set_language(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    keyboard = [
        [InlineKeyboardButton("English", callback_data='lang_en')],
        [InlineKeyboardButton("Deutsch", callback_data='lang_de')],
        [InlineKeyboardButton("Русский", callback_data='lang_ru')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=chat_id, text="Choose your language:", reply_markup=reply_markup)

@check_user_registered
def register(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user_data = user_manager.get_user(chat_id)
    if user_data:
        city = update.message.text.split(' ', 1)[1]
        user_data['city'] = city
        user_manager.save_user(chat_id, user_data)
        context.bot.send_message(
            chat_id=chat_id,
            text=eval(f"{user_data['language']}_texts")['settings']['city_set'].format(city=city)
        )

@check_user_registered
def set_settings(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    settings = json.loads(update.message.text.split(' ', 1)[1])
    user_data = user_manager.get_user(chat_id)
    if user_data:
        user_data.update(settings)
        user_manager.save_user(chat_id, user_data)
        context.bot.send_message(
            chat_id=chat_id,
            text=eval(f"{user_data['language']}_texts")['settings']['updated']
        )

def send_proposals(context: CallbackContext):
    job = context.job
    chat_id = job.context
    user_data = user_manager.get_user(chat_id)
    if user_data:
        proposals = fetch_proposals(user_data)
        for proposal in proposals:
            context.bot.send_message(chat_id=chat_id, text=proposal)

def fetch_proposals(settings):
    # Placeholder function to fetch proposals based on user settings
    return ["Proposal 1", "Proposal 2"]

def error(update: Update, context: CallbackContext):
    print(f"Update {update} caused error {context.error}")

# Update handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("stop", stop))
dispatcher.add_handler(CommandHandler("delete_account", delete_account))
dispatcher.add_handler(CommandHandler("set_language", set_language))
dispatcher.add_handler(CallbackQueryHandler(button))
dispatcher.add_handler(CommandHandler("register", register))
dispatcher.add_handler(CommandHandler("set_settings", set_settings))
dispatcher.add_error_handler(error)

# Add handler for all text messages
def handle_message(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user_data = user_manager.get_user(chat_id)

    if not user_data or not user_data.get('is_active', False):
        context.bot.send_message(
            chat_id=chat_id,
            text=eval(f"en_texts")['errors']['unknown_command']
        )
        return

dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

# Add this function at the end of the file
async def start_telegram_bot():
    # Initialize bot with application builder
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("delete_account", delete_account))
    application.add_handler(CommandHandler("set_language", set_language))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    await application.run_polling()
