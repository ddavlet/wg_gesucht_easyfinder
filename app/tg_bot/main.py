import json
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from database.user_manager import UserManager
from database.database import get_user_fields
from mapsapi import MapsAPI
from validators import *
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
maps_api = MapsAPI()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("start")
    chat_id = update.effective_chat.id
    existing_user = user_manager.get_user(chat_id)

    if existing_user and existing_user.get('is_active', False):
        await context.bot.send_message(
            chat_id=chat_id,
            text=eval(f"{existing_user['language']}_texts")['registration']['already_registered']
        )
        return

    name = update.effective_chat.username
    user_data = get_user_fields()
    user_data['chat_id'] = chat_id
    user_data['language'] = 'en'
    user_data['preferences'] = {
        'address': None,
        'distance': None,
        'notifications': True
    }
    user_data['name'] = name
    user_data['status'] = 'main'
    user_manager.save_user(chat_id, user_data)
    await context.bot.send_message(chat_id=chat_id, text=en_texts['start'])

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("stop")
    chat_id = update.effective_chat.id
    user_data = user_manager.get_user(chat_id)
    if not user_data:
        await context.bot.send_message(
            chat_id=chat_id,
            text=eval(f"{user_data['language']}_texts")['errors']['not_registered']
        )
        return
    user_manager.deactivate_user(chat_id)
    await context.bot.send_message(
        chat_id=chat_id,
        text=eval(f"{user_data['language']}_texts")['account']['stopped']
    )

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data = user_manager.get_user(chat_id)
    if not user_data:
        await context.bot.send_message(
            chat_id=chat_id,
            text=eval(f"{user_data['language']}_texts")['errors']['not_registered']
        )
        return
    keyboard = [
        [InlineKeyboardButton("English", callback_data='lang_en')],
        [InlineKeyboardButton("Deutsch", callback_data='lang_de')],
        [InlineKeyboardButton("Русский", callback_data='lang_ru')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, text=eval(f"{user_data['language']}_texts")['settings']['choose_language'], reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    await query.answer()

    if query.data.startswith('lang_'):
        lang = query.data.split('_')[1]
        user_data = user_manager.get_user(chat_id)
        if not user_data:
            await context.bot.send_message(
                chat_id=chat_id,
                text=eval(f"{user_data['language']}_texts")['errors']['not_registered']
            )
            return
        user_data['language'] = lang
        user_manager.save_user(chat_id, user_data)
        await context.bot.send_message(
            chat_id=chat_id,
            text=eval(f"{lang}_texts")['settings']['language_changed']
        )

async def set_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    settings = json.loads(update.message.text.split(' ', 1)[1])
    user_data = user_manager.get_user(chat_id)
    if user_data:
        user_data.update(settings)
        user_manager.save_user(chat_id, user_data)
        await context.bot.send_message(
            chat_id=chat_id,
            text=eval(f"{user_data['language']}_texts")['settings']['updated']
        )

async def delete_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("delete_account")
    chat_id = update.effective_chat.id
    user_data = user_manager.get_user(chat_id)
    if user_data:
        user_manager.delete_user(chat_id)
        await context.bot.send_message(
            chat_id=chat_id,
            text=eval(f"{user_data['language']}_texts")['account']['deleted']
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")

async def handle_other_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("handle_other_messages")
    chat_id = update.effective_chat.id
    user_data = user_manager.get_user(chat_id)
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    if not user_data:
        await context.bot.send_message(
            chat_id=chat_id,
            text=eval(f"{user_data['language']}_texts")['errors']['not_registered']
        )
        return
    if user_data['state'] == 'main':
        await context.bot.send_message(chat_id=chat_id, text=eval(f"{user_data['language']}_texts")['errors']['unknown_command'])
    elif user_data['state'] == 'address':
        print("address")
        validators = Validators(user_data, eval(f"{user_data['language']}_texts"))
        user_data['status'] = 'main'
        user_manager.save_user(chat_id, user_data)
        try:
            answer = validators.validate_address(update.message.text)
        except Exception as e:
            print(f"Error validating address: {e}")
            answer = eval(f"{user_data['language']}_texts")['errors']['wrong_address']
        user_manager.save_user(chat_id, user_data)
        await context.bot.send_message(chat_id=chat_id, text=answer)
    elif user_data['state'] == 'settings':
        await context.bot.send_message(chat_id=chat_id, text=eval(f"{user_data['language']}_texts")['errors']['unknown_command'])
    else:
        await context.bot.send_message(chat_id=chat_id, text=eval(f"{user_data['language']}_texts")['errors']['unknown_command'])

# New command handler functions
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data = user_manager.get_user(chat_id)
    if not user_data:
        await context.bot.send_message(
            chat_id=chat_id,
            text=eval(f"{user_data['language']}_texts")['errors']['not_registered']
        )
        return
    await context.bot.send_message(chat_id=chat_id, text=eval(f"{user_data['language']}_texts")['help'])

async def set_settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data = user_manager.get_user(chat_id)
    if not user_data:
        await context.bot.send_message(
            chat_id=chat_id,
            text=eval(f"{user_data['language']}_texts")['errors']['not_registered']
        )
        return
    await context.bot.send_message(chat_id=chat_id, text="Please provide your settings in JSON format.")

async def set_distance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data = user_manager.get_user(chat_id)
    if not user_data:
        await context.bot.send_message(
            chat_id=chat_id,
            text=eval(f"{user_data['language']}_texts")['errors']['not_registered']
        )
        return
    await context.bot.send_message(chat_id=chat_id, text=eval(f"{user_data['language']}_texts")['settings']['distance_prompt'])

# New command handler for setting the address
async def set_address_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data = user_manager.get_user(chat_id)
    if not user_data:
        await context.bot.send_message(
            chat_id=chat_id,
            text=eval(f"{user_data['language']}_texts")['errors']['not_registered']
        )
        return

    # Prompt the user to enter their address
    user_data['state'] = 'address'
    user_manager.save_user(chat_id, user_data)
    await context.bot.send_message(
        chat_id=chat_id,
        text=eval(f"{user_data['language']}_texts")['registration']['address_prompt']
    )

# Initialize bot with application builder
application = ApplicationBuilder().token(TOKEN).build()

# Account handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("stop", stop))
application.add_handler(CommandHandler("delete_account", delete_account))

# Settings handlers
application.add_handler(CommandHandler("set_language", set_language))
application.add_handler(CommandHandler("set_address", set_address_command))
application.add_handler(CommandHandler("set_distance", set_distance_command))
application.add_handler(CommandHandler("set_settings", set_settings_command))
application.add_handler(CommandHandler("help", help_command))

application.add_handler(CallbackQueryHandler(button))

# Add a handler for any other messages
application.add_handler(MessageHandler(filters.TEXT, handle_other_messages))

# Add error handler
application.add_error_handler(error_handler)

# Start the bot
application.run_polling()

