import json
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from user_manager import UserManager

# Load environment variables
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
LANGUAGE_FILES = {
    'en': os.getenv('LANGUAGE_FILE_EN'),
    'de': os.getenv('LANGUAGE_FILE_DE'),
    'ru': os.getenv('LANGUAGE_FILE_RU')
}

# Check if any language file path is None
for lang, path in LANGUAGE_FILES.items():
    if path is None:
        print(f"Warning: LANGUAGE_FILE_{lang.upper()} is not set in the environment variables.")

# Load language files
with open(LANGUAGE_FILES['en'], 'r') as f:
    en_texts = json.load(f)
with open(LANGUAGE_FILES['de'], 'r') as f:
    de_texts = json.load(f)
with open(LANGUAGE_FILES['ru'], 'r') as f:
    ru_texts = json.load(f)

# In-memory user settings
user_manager = UserManager()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("start")
    chat_id = update.message.chat_id
    existing_user = user_manager.get_user(chat_id)

    if existing_user and existing_user.get('is_active', False):
        await context.bot.send_message(
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
    await context.bot.send_message(chat_id=chat_id, text=en_texts['start'])

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    # keyboard = [
    #     [InlineKeyboardButton("English", callback_data='lang_en')],
    #     [InlineKeyboardButton("Deutsch", callback_data='lang_de')],
    #     [InlineKeyboardButton("Русский", callback_data='lang_ru')]
    # ]
    # reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, text="Choose your language:")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    await query.answer()

    if query.data.startswith('lang_'):
        lang = query.data.split('_')[1]
        user_data = user_manager.get_user(chat_id)
        if user_data:
            user_data['language'] = lang
            user_data['settings']['language'] = lang
            user_manager.save_user(chat_id, user_data)
            await context.bot.send_message(
                chat_id=chat_id,
                text=eval(f"{lang}_texts")['settings']['language_changed']
            )

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_data = user_manager.get_user(chat_id)
    if user_data:
        city = update.message.text.split(' ', 1)[1]
        user_data['city'] = city
        user_manager.save_user(chat_id, user_data)
        await context.bot.send_message(
            chat_id=chat_id,
            text=eval(f"{user_data['language']}_texts")['settings']['city_set'].format(city=city)
        )

async def set_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    settings = json.loads(update.message.text.split(' ', 1)[1])
    user_data = user_manager.get_user(chat_id)
    if user_data:
        user_data.update(settings)
        user_manager.save_user(chat_id, user_data)
        await context.bot.send_message(
            chat_id=chat_id,
            text=eval(f"{user_data['language']}_texts")['settings']['updated']
        )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("stop")
    chat_id = update.message.chat_id
    user_data = user_manager.get_user(chat_id)
    if user_data:
        user_manager.deactivate_user(chat_id)
        await context.bot.send_message(
            chat_id=chat_id,
            text=eval(f"{user_data['language']}_texts")['account']['stopped']
        )

async def delete_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("delete_account")
    chat_id = update.message.chat_id
    user_data = user_manager.get_user(chat_id)
    if user_data:
        user_manager.delete_user(chat_id)
        await context.bot.send_message(
            chat_id=chat_id,
            text=eval(f"{user_data['language']}_texts")['account']['deleted']
        )

async def check_user_registered(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        user_data = user_manager.get_user(chat_id)

        if not user_data or not user_data.get('is_active', False):
            await context.bot.send_message(
                chat_id=chat_id,
                text="Please send /start to register and use the bot."
            )
            return
        return await func(update, context)
    return wrapper

@check_user_registered
async def set_language_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("set_language_handler")
    await set_language(update, context)

@check_user_registered
async def register_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("register_handler")
    await register(update, context)

@check_user_registered
async def set_settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("set_settings_handler")
    await set_settings(update, context)

async def send_proposals(context: ContextTypes.DEFAULT_TYPE):
    print("send_proposals")
    job = context.job
    chat_id = job.context
    user_data = user_manager.get_user(chat_id)
    if user_data:
        proposals = fetch_proposals(user_data)
        for proposal in proposals:
            await context.bot.send_message(chat_id=chat_id, text=proposal)

def fetch_proposals(settings):
    print("fetch_proposals")
    # Placeholder function to fetch proposals based on user settings
    return ["Proposal 1", "Proposal 2"]

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("handle_message")
    chat_id = update.message.chat_id
    user_data = user_manager.get_user(chat_id)

    if not user_data or not user_data.get('is_active', False):
        await context.bot.send_message(
            chat_id=chat_id,
            text=eval(f"en_texts")['errors']['unknown_command']
        )
        return

# New function to handle other messages
async def handle_other_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("handle_other_messages")
    chat_id = update.message.chat_id
    await context.bot.send_message(chat_id=chat_id, text="other message")

# Initialize bot with application builder
application = Application.builder().token(TOKEN).build()

# Add handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("stop", stop))
application.add_handler(CommandHandler("delete_account", delete_account))
application.add_handler(CommandHandler("set_language", set_language_handler))
application.add_handler(CallbackQueryHandler(button))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Add a handler for any other messages
application.add_handler(MessageHandler(filters.TEXT, handle_other_messages))

# Add error handler
application.add_error_handler(error_handler)

# Start the bot
application.run_polling()

