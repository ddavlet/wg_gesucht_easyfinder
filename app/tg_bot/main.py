import json
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    JobQueue
)
from database.user_manager import UserManager
from database.finder_manager import FinderManager
from database.database import get_user_fields, get_finder_fields
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
finder_manager = FinderManager()
maps_api = MapsAPI()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("start")
    chat_id = update.effective_chat.id
    user_data = user_manager.get_user(chat_id)

    if user_data and user_data.get('is_active', False):
        await context.bot.send_message(
            chat_id=chat_id,
            text=eval(f"{user_data['language']}_texts")['registration']['already_registered']
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
    user_data['state'] = 'main'
    user_manager.save_user(chat_id, user_data)
    await context.bot.send_message(chat_id=chat_id, text=en_texts['start'])

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("stop")
    chat_id = update.effective_chat.id
    user_data = user_manager.get_user(chat_id)
    if not user_data:
        return
    user_data['state'] = 'main'
    user_manager.save_user(chat_id, user_data)
    user_manager.deactivate_user(chat_id)
    await context.bot.send_message(
        chat_id=chat_id,
        text=eval(f"{user_data['language']}_texts")['account']['stopped']
    )

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data = user_manager.get_user(chat_id)
    if not user_data:
        return
    keyboard = [
        [InlineKeyboardButton("English", callback_data='lang_en')],
        [InlineKeyboardButton("Deutsch", callback_data='lang_de')],
        [InlineKeyboardButton("Русский", callback_data='lang_ru')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, text=eval(f"{user_data['language']}_texts")['settings']['choose_language'], reply_markup=reply_markup)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    await query.answer()
    user_data = user_manager.get_user(chat_id)
    if not user_data:
        return
    text_lang = eval(f"{user_data['language']}_texts")

    if query.data.startswith('lang_'):
        print("query lang_")
        lang = query.data.split('_')[1]
        user_data['language'] = lang
        user_manager.save_user(chat_id, user_data)
        await context.bot.send_message(
            chat_id=chat_id,
            text=eval(f"{lang}_texts")['settings']['language_changed']
        )
    elif query.data.startswith('finder_type_'):
        print("query finder_type_")
        new_finder = get_finder_fields()
        new_finder['type'] = query.data.split('_')[2]
        new_finder['user_id'] = user_data['chat_id']
        new_finder['finder_id'] = finder_manager.generate_finder_id()
        finder_manager.save_finder(chat_id, new_finder['finder_id'], new_finder)
        await context.bot.send_message(
            chat_id=chat_id,
            text=text_lang['new_finder']['duration_prompt']
        )
        user_data['state'] = 'new_finder_duration'
        user_data['finder_id'] = new_finder['finder_id']
        user_manager.save_user(chat_id, user_data)

    elif query.data.startswith('delete_account_'):
        print("query delete_account_")
        if query.data == 'delete_account_yes':
            user_manager.delete_user(chat_id)
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=query.message.message_id,
                text=text_lang['account']['deleted']
            )
        elif query.data == 'delete_account_no':
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=query.message.message_id,
                text=text_lang['account']['delete_cancel']
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
    if not user_data:
        return
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data='delete_account_yes')],
        [InlineKeyboardButton("No", callback_data='delete_account_no')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=chat_id,
        text=eval(f"{user_data['language']}_texts")['account']['delete_confirmation'],
        reply_markup=reply_markup
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")

async def handle_other_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("handle_other_messages")
    chat_id = update.effective_chat.id
    user_data = user_manager.get_user(chat_id)
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    if not user_data:
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
    elif user_data['state'] == 'new_finder_duration':
        print("new_finder_duration")
        try:
            duration: int = int(update.message.text)
            finder_data = finder_manager.get_finder(user_data['finder_id'])
            finder_data['duration'] = duration
            finder_manager.save_finder(chat_id, user_data['finder_id'], finder_data)
            user_data['state'] = 'main'
            user_data['finder_id'] = None
            user_manager.save_user(chat_id, user_data)
            await context.bot.send_message(chat_id=chat_id, text=eval(f"{user_data['language']}_texts")['new_finder']['new_finder_success'])
        except Exception as e:
            print(f"Error setting duration: {e}")
            finder_manager.delete_finder(user_data['finder_id'])
            user_data['state'] = 'main'
            user_data['finder_id'] = None
            user_manager.save_user(chat_id, user_data)
            await context.bot.send_message(chat_id=chat_id, text=eval(f"{user_data['language']}_texts")['errors']['wrong_duration'])


# New command handler functions
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data = user_manager.get_user(chat_id)
    if not user_data:
        return
    await context.bot.send_message(chat_id=chat_id, text=eval(f"{user_data['language']}_texts")['help'])

async def set_settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data = user_manager.get_user(chat_id)
    if not user_data:
        return
    await context.bot.send_message(chat_id=chat_id, text="Please provide your settings in JSON format.")

async def set_distance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data = user_manager.get_user(chat_id)
    if not user_data:
        return
    await context.bot.send_message(chat_id=chat_id, text=eval(f"{user_data['language']}_texts")['registration']['distance_prompt'])

async def set_new_finder_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data = user_manager.get_user(chat_id)
    if not user_data:
        return
    text_lang = eval(f"{user_data['language']}_texts")
    keyboard = [
        [InlineKeyboardButton(text_lang['new_finder']['walking'], callback_data='finder_type_walk')],
        [InlineKeyboardButton(text_lang['new_finder']['biking'], callback_data='finder_type_bike')],
        [InlineKeyboardButton(text_lang['new_finder']['driving'], callback_data='finder_type_drive')],
        [InlineKeyboardButton(text_lang['new_finder']['public_transport'], callback_data='finder_type_transport')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, text=text_lang['new_finder']['new_finder_prompt'], reply_markup=reply_markup)

async def set_address_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data = user_manager.get_user(chat_id)
    if not user_data:
        return

    # Prompt the user to enter their address
    user_data['state'] = 'address'
    user_manager.save_user(chat_id, user_data)
    await context.bot.send_message(
        chat_id=chat_id,
        text=eval(f"{user_data['language']}_texts")['registration']['address_prompt']
    )

async def clean_cache(context: ContextTypes.DEFAULT_TYPE):
    user_manager.clean_expired_cache()

# Initialize bot with application builder
application = ApplicationBuilder().token(TOKEN).build()

# Account handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("stop", stop))
application.add_handler(CommandHandler("delete_account", delete_account))

# Settings handlers
application.add_handler(CommandHandler("set_language", set_language))
application.add_handler(CommandHandler("set_address", set_address_command))
application.add_handler(CommandHandler("set_new_finder", set_new_finder_command))
application.add_handler(CommandHandler("set_distance", set_distance_command))
application.add_handler(CommandHandler("set_settings", set_settings_command))
application.add_handler(CommandHandler("help", help_command))

# Callback handlers
application.add_handler(CallbackQueryHandler(callback_handler))

# Add a handler for any other messages
application.add_handler(MessageHandler(filters.TEXT, handle_other_messages))

# Add error handler
application.add_error_handler(error_handler)

# Start the bot

# Set up a job queue to clean the cache every 10 minutes
job_queue = application.job_queue
job_queue.run_repeating(clean_cache, interval=600, first=0)  # 600 seconds = 10 minutes

application.run_polling()

