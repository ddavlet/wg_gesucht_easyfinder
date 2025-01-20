import json
import os
import logging
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from database.user_manager import UserManager
from database.finder_manager import FinderManager
from database.flat_offers_manager import FlatOffersManager
from database.database import get_user_fields, get_finder_fields
from validators import *
from answers import *

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
flat_offers_manager = FlatOffersManager()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Add a file handler for logging
file_handler = logging.FileHandler('bot.log')
file_handler.setLevel(logging.ERROR)  # Set the level for the file handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Get the root logger and add the file handler
logger = logging.getLogger()
logger.addHandler(file_handler)

async def create_keyboard(keys: dict):
    keyboard = []
    keyboard.clear()
    for key, value in keys.items():
        keyboard.append([InlineKeyboardButton(value, callback_data=key)])
    logging.info(keyboard)
    return keyboard

async def send_message(bot: Bot, update: Update, user_data: dict, state: str = None):
    logging.info("Sending message...")
    text_lang = eval(f"{user_data['language']}_texts")

    if state is None:
        state = user_data['state']
        logging.info(f"State is None, using user state: {state}")
        text = text_lang[state]['text']
    else:
        text, keyboard_texts = await eval(state)(user_data)
        logging.info(f"Using state: {state} to get text and keyboard texts.")

    await bot.send_message(chat_id=user_data.get('chat_id', 0), text=text, parse_mode='HTML')
    logging.info(f"Message sent with text: {text}")

async def send_message_with_keyboard(bot: Bot, update: Update, user_data: dict, state: str = None, modify_message: bool = False):
    logging.info("Sending message with keyboard...")
    text_lang = eval(f"{user_data['language']}_texts")
    text = None
    keyboard_texts = None
    if state is None:
        state = user_data['state']
        logging.info(f"State is None, using user state: {state}")
        text = text_lang[state]['text']
        keyboard_texts = text_lang[state].get('keyboard', None)
    else:
        text, keyboard_texts = await eval(state)(user_data)
        logging.info(f"Using state: {state} to get text and keyboard texts.")
    if keyboard_texts is None:
        keyboard_texts = text_lang['navigation']['main']
    if 'settings_setnotifications' in keyboard_texts:
        if user_data['preferences']['notifications']:
            keyboard_texts['settings_setnotifications'] = text_lang['settings_menu']['keyboard']['settings_setnotifications'] + ' ✅'
        else:
            keyboard_texts['settings_setnotifications'] = text_lang['settings_menu']['keyboard']['settings_setnotifications'] + ' ❌'
    keyboard: list[list[InlineKeyboardButton]] = await create_keyboard(keyboard_texts)
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query and modify_message:
        message_id = update.callback_query.message.message_id
        await bot.edit_message_text(chat_id=user_data.get('chat_id', 0), message_id=message_id, text=text, reply_markup=reply_markup, parse_mode='HTML')
        logging.info("Message edited with new text and reply markup.")
    else:
        await bot.send_message(chat_id=user_data.get('chat_id', 0), text=text, reply_markup=reply_markup, parse_mode='HTML')
        logging.info("Message sent with new text and reply markup.")
    logging.info(f"Text: {text}, Keyboard texts: {keyboard_texts}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Start command received.")
    chat_id = update.effective_chat.id
    logging.info(f"Chat ID: {chat_id}")
    user_data = await user_manager.get_any_user(chat_id)
    if user_data and not user_data.get('is_active', False):
        user_data['is_active'] = True
        await user_manager.save_user(chat_id, user_data)
        text_lang = eval(f"{user_data['language']}_texts")
        await context.bot.send_message(chat_id=chat_id, text=text_lang['start']['text_reactivated_profile'])
    elif not user_data:
        name = update.effective_chat.username
        user_data = get_user_fields()
        user_data['chat_id'] = chat_id
        user_data['name'] = name
        logging.info(f"User data: {user_data}")
        # message = text_lang['main']['text']
        # keyboard = text_lang['main']['keyboard']
        text_lang = eval(f"{user_data['language']}_texts")
        await user_manager.save_user(chat_id, user_data)
        await context.bot.send_message(chat_id=chat_id, text=text_lang['start']['text_new_profile'], parse_mode='HTML')
    text_lang = eval(f"{user_data['language']}_texts")
    user_data['state'] = 'main'
    await user_manager.save_user(chat_id, user_data)
    await send_message_with_keyboard(context.bot, update, user_data, 'main_menu', modify_message=False)
    # await send_message(context.bot, update, user_data)

    logging.info(f"New user data: {user_data}")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Stop command received.")
    chat_id = update.effective_chat.id
    logging.info(f"Chat ID: {chat_id}")
    user_data = await user_manager.get_user(chat_id)
    logging.info(f"User data: {user_data}")
    if not user_data:
        logging.warning(f"No user data found for chat ID: {chat_id}")
        return
    text_lang = eval(f"{user_data['language']}_texts")
    user_data['state'] = 'main'
    await user_manager.save_user(chat_id, user_data)
    user_manager.deactivate_user(chat_id)
    logging.info(f"User {chat_id} has been stopped.")
    await context.bot.send_message(
        chat_id=chat_id,
        text=text_lang['account']['stopped']
    )
    return None, None

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Callback handler triggered.")
    query = update.callback_query
    chat_id = query.message.chat_id
    logging.info(f"Chat ID: {chat_id}, Query data: {query.data}")
    await query.answer()
    user_data = await user_manager.get_user(chat_id)
    if not user_data:
        logging.warning(f"No user data found for chat ID: {chat_id}")
        return
    text_lang = eval(f"{user_data['language']}_texts")

    if query.data.startswith('lang_'):
        logging.info("Language change requested.")
        lang = query.data.split('_')[1]
        user_data['language'] = lang
        await user_manager.save_user(chat_id, user_data)
        text_lang = eval(f"{lang}_texts")
        await send_message_with_keyboard(context.bot, update, user_data, 'language_changed', modify_message=True)
        logging.info(f"User {chat_id} language changed to {lang}.")

    elif query.data.startswith('offer_type_'):
        logging.info("Offer type selection requested.")
        offer_type = query.data.split('_')[2]
        logging.info(f"Offer type: {offer_type}")
        finder = await finder_manager.get_finder(user_data['finder_id'])
        finder['offer_type'] = offer_type
        await finder_manager.update_finder(finder['finder_id'], finder)
        user_data['state'] = 'new_finder_duration'
        await user_manager.save_user(chat_id, user_data)
        await context.bot.send_message(chat_id=chat_id, text=text_lang['new_finder']['duration_prompt'])
        logging.info(f"Offer type set to {offer_type} for user {chat_id}.")

    elif query.data.startswith('delete_account_'):
        logging.info("Account deletion requested.")
        if query.data == 'delete_account_yes':
            await user_manager.delete_user(chat_id)
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=query.message.message_id,
                text=text_lang['account']['deleted']
            )
            logging.info(f"User {chat_id} account deleted.")
        elif query.data == 'delete_account_no':
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=query.message.message_id,
                text=text_lang['account']['delete_cancel']
            )
            logging.info(f"User {chat_id} canceled account deletion.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Update: {update} caused error:\n------------\n{context.error}\n------------")

async def handle_other_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Handling other messages.")
    chat_id = update.effective_chat.id
    logging.info(f"Chat ID: {chat_id}")
    user_data = await user_manager.get_user(chat_id)
    logging.info(f"User data: {user_data}")
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    if not user_data:
        logging.warning(f"No user data found for chat ID: {chat_id}")
        return
    text_lang = eval(f"{user_data['language']}_texts")
    if user_data['state'] == 'main':
        await context.bot.send_message(chat_id=chat_id, text=text_lang['errors']['unknown_command'])
        logging.info(f"Unknown command sent to user {chat_id}.")
    elif user_data['state'] == 'address':
        logging.info("Address validation in progress.")
        validators = Validators(user_data)
        user_data['state'] = 'main'
        try:
            answer, is_valid = await validators.validate_address(update.message.text)
            logging.info(f"Address validation result: {answer}")
            if is_valid:
                await send_message(context.bot, update, user_data, 'address_set_success')
            else:
                await send_message(context.bot, update, user_data, 'address_set_error')
            await context.bot.send_message(chat_id=chat_id, text=answer)
        except Exception as e:
            logging.error(f"Error validating address: {e}")
            answer = text_lang['errors']['wrong_address']
            await send_message(context.bot, update, user_data, 'address_set_error')
            await context.bot.send_message(chat_id=chat_id, text=answer)
        await user_manager.save_user(chat_id, user_data)
        await send_message_with_keyboard(context.bot, update, user_data, modify_message=False)
    elif user_data['state'] == 'new_finder_duration':
        logging.info("New finder duration setting in progress.")
        try:
            duration: int = int(update.message.text)
            if duration > 300:
                raise Exception("Duration is too long")
            finder_data = await finder_manager.get_finder(user_data['finder_id'])
            finder_data['duration'] = duration * 60  # convert to seconds
            await finder_manager.save_finder(chat_id, user_data['finder_id'], finder_data)
            user_data['finder_id'] = None
            await user_manager.save_user(chat_id, user_data)
            await send_message_with_keyboard(context.bot, update, user_data, 'new_finder_success', modify_message=True)
            logging.info(f"Finder duration set to {duration} minutes for user {chat_id}.")
        except Exception as e:
            logging.error(f"Error setting duration: {e}")
            await finder_manager.delete_finder(user_data['finder_id'])
            user_data['finder_id'] = None
            await context.bot.send_message(chat_id=chat_id, text=text_lang['errors']['wrong_duration'])
        user_data['state'] = 'main'
        user_data['finder_id'] = None
        await user_manager.save_user(chat_id, user_data)

async def clean_cache(context: ContextTypes.DEFAULT_TYPE):
    user_manager.clean_expired_cache()
    finder_manager.clean_expired_cache()
    finder_manager.delete_expired_finders()
    flat_offers_manager.clean_expired_cache()
    flat_offers_manager.deactivate_expired_offers()

async def main_menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Callback handler triggered.")
    query = update.callback_query
    chat_id = query.message.chat_id
    logging.info(f"Chat ID: {chat_id}, Query data: {query.data}")
    await query.answer()
    user_data = await user_manager.get_user(chat_id)
    if not user_data:
        logging.warning(f"No user data found for chat ID: {chat_id}")
        return
    command_type = query.data.split('_')[2]
    logging.info(f"Command type: {command_type}")
    if command_type == 'mydata':
        logging.info('get_my_data mathced')
        await send_message_with_keyboard(context.bot, update, user_data, 'get_user_data', modify_message=True)
    elif command_type == 'myfinders':
        logging.info('get_my_finders mathced')
        await send_message_with_keyboard(context.bot, update, user_data, 'get_my_finders', modify_message=True)
    elif command_type == 'myoffers':
        logging.info('get_my_offers mathced')
        await process_offers(context.bot, user_data)
        await send_message_with_keyboard(context.bot, update, user_data, modify_message=False)
    elif command_type == 'settings':
        logging.info('settings_menu mathced')
        await send_message_with_keyboard(context.bot, update, user_data, 'settings_menu', modify_message=True)
    elif command_type == 'help':
        logging.info('help mathced')
        await send_message_with_keyboard(context.bot, update, user_data, 'help_menu', modify_message=True)
    elif command_type == 'stop':
        logging.info('stop mathced')
        await send_message(context.bot, update, user_data, 'stop_bot')

async def return_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Returning to main menu.")
    user_data = await user_manager.get_user(update.effective_chat.id)
    if not user_data:
        logging.warning(f"No user data found for chat ID: {update.effective_chat.id}")
        return
    user_data['state'] = 'main'
    if user_data['finder_id']:
        await finder_manager.delete_finder(user_data['finder_id'])
        user_data['finder_id'] = None
    await user_manager.save_user(update.effective_chat.id, user_data)
    text_lang = eval(f"{user_data['language']}_texts")
    text = text_lang['main']['text']
    keyboard = text_lang['main']['keyboard']
    await context.bot.edit_message_text(chat_id=user_data.get('chat_id', 0), message_id=update.callback_query.message.message_id, text=text, reply_markup=InlineKeyboardMarkup(await create_keyboard(keyboard)), parse_mode='HTML')

async def process_offers(bot, user_data):
    bot.send_chat_action(chat_id=user_data.get('chat_id', 0), action="typing")
    logging.info("Processing offers.")
    chat_id = user_data.get('chat_id', 0)
    logging.info(f"Chat ID: {chat_id}")
    offers = await get_my_offers(user_data)
    text_lang = eval(f"{user_data['language']}_texts")
    if offers == None:
        await bot.send_message(chat_id=chat_id, text=text_lang['offer_data']['no_offers'])
    elif not isinstance(offers, list):
        logging.info(f"Offers is not list: {offers}")
        await bot.send_message(chat_id=chat_id, text=offers, parse_mode='HTML')
    else:
        logging.info(f"Offers separate: {offers}")
        await bot.send_message(chat_id=chat_id, text=text_lang['offer_data']['first'], parse_mode='HTML')
        for offer in offers:
            await bot.send_message(chat_id=chat_id, text=offer.get('text'), reply_markup=InlineKeyboardMarkup(await create_keyboard({f"offer_details_{offer.get('id')}" : text_lang['offer_data']['keyboard']['offer_details']})), parse_mode='HTML')
    return user_data, None

async def settings_menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Callback handler triggered.")
    query = update.callback_query
    chat_id = query.message.chat_id
    logging.info(f"Chat ID: {chat_id}, Query data: {query.data}")
    await query.answer()
    user_data = await user_manager.get_user(chat_id)
    if not user_data:
        logging.warning(f"No user data found for chat ID: {chat_id}")
        return
    command_type = query.data.split('_')[1]
    logging.info(f"Command type: {command_type}")
    if command_type == 'setlanguage':
        logging.info('set_language matched')
        await send_message_with_keyboard(context.bot, update, user_data, 'set_language', modify_message=True)
    elif command_type == 'setaddress':
        logging.info('set_address matched')
        user_data['state'] = 'address'
        await user_manager.save_user(chat_id, user_data)
        await send_message(context.bot, update, user_data, 'set_address')
    elif command_type == 'setnewfinder':
        logging.info('set_new_finder matched')
        await send_message_with_keyboard(context.bot, update, user_data, 'set_new_finder', modify_message=True)
    elif command_type == 'setnotifications':
        logging.info('set_notifications matched')
        user_data['preferences']['notifications'] = not user_data['preferences']['notifications']
        await user_manager.save_user(chat_id, user_data)
        await send_message_with_keyboard(context.bot, update, user_data, 'settings_menu', modify_message=True)
    elif command_type == 'deletefinder':
        logging.info('delete_finder matched')
        await send_message_with_keyboard(context.bot, update, user_data, 'delete_finder', modify_message=True)
    elif command_type == 'deleteaccount':
        logging.info('delete_account matched')
        await send_message_with_keyboard(context.bot, update, user_data, 'delete_account', modify_message=True)
    elif command_type == 'back':
        await send_message_with_keyboard(context.bot, update, user_data, modify_message=True)

async def new_finder_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Callback handler triggered.")
    query = update.callback_query
    chat_id = query.message.chat_id
    logging.info(f"Chat ID: {chat_id}, Query data: {query.data}")
    await query.answer()
    user_data = await user_manager.get_user(chat_id)
    if not user_data:
        logging.warning(f"No user data found for chat ID: {chat_id}")
        return
    text_lang = eval(f"{user_data['language']}_texts")
    command_type = query.data.split('_')[2]
    logging.info(f"Command type: {command_type}")
    data_type = query.data.split('_')[3]
    if command_type == "housing":
        new_finder = get_finder_fields()
        new_finder['offer_type'] = data_type
        offer_types = ['shared', 'oneroom', 'flat', 'house']
        offer_type_id = offer_types.index(data_type) if data_type in offer_types else -1
        new_finder['offer_type_id'] = offer_type_id
        new_finder['type'] = 'housing'
        new_finder['user_id'] = user_data.get('chat_id', 0)
        new_finder['finder_id'] = await finder_manager.generate_finder_id()
        await finder_manager.save_finder(chat_id, new_finder['finder_id'], new_finder)
        user_data['finder_id'] = new_finder['finder_id']
        await user_manager.save_user(chat_id, user_data)
        keyboard = await create_keyboard(text_lang['new_finder'].get('new_finder_travel_mode_keyboard'))
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = text_lang['new_finder'].get('new_finder_travel_mode_prompt')
        await context.bot.edit_message_text(chat_id=chat_id, message_id=query.message.message_id, text=text, reply_markup=reply_markup, parse_mode='HTML')
    elif command_type == "travel":
        finder = await finder_manager.get_finder(user_data['finder_id'])
        finder['type'] = data_type
        await finder_manager.save_finder(chat_id, user_data['finder_id'], finder)
        user_data['state'] = 'new_finder_duration'
        await user_manager.save_user(chat_id, user_data)
        keyboard = await create_keyboard(text_lang['new_finder'].get('main_menu'))
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = text_lang['new_finder'].get('duration_prompt')
        await context.bot.edit_message_text(chat_id=chat_id, message_id=query.message.message_id, text=text, reply_markup=reply_markup, parse_mode='HTML')


async def delete_finder_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Callback handler triggered.")
    query = update.callback_query
    chat_id = query.message.chat_id
    logging.info(f"Chat ID: {chat_id}, Query data: {query.data}")
    await query.answer()
    user_data = await user_manager.get_user(chat_id)
    if not user_data:
        logging.warning(f"No user data found for chat ID: {chat_id}")
        return
    finder_id = int(query.data.split('_')[2])
    await finder_manager.delete_finder(finder_id)
    await send_message(context.bot, update, user_data, 'delete_finder_success')
    await send_message_with_keyboard(context.bot, update, user_data, modify_message=False)

async def delete_account_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Callback handler triggered.")
    query = update.callback_query
    chat_id = query.message.chat_id
    logging.info(f"Chat ID: {chat_id}, Query data: {query.data}")
    await query.answer()
    user_data = await user_manager.get_user(chat_id)
    if not user_data:
        logging.warning(f"No user data found for chat ID: {chat_id}")
        return
    command_type = query.data.split('_')[2]
    if command_type == 'delete_account_yes':
        await delete_account(user_data)
        await send_message(context.bot, update, user_data, 'delete_account_success')
    elif command_type == 'delete_account_no':
        await send_message(context.bot, update, user_data, 'delete_account_cancel')
    await send_message_with_keyboard(context.bot, update, user_data, modify_message=False)

async def offer_original_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Callback handler triggered.")
    query = update.callback_query
    chat_id = query.message.chat_id
    offer_id = query.data.split('_')[2]
    user_data = await user_manager.get_user(chat_id)
    if not user_data:
        logging.warning(f"No user data found for chat ID: {chat_id}")
        return
    text = await original_offer_details(user_data, offer_id)
    if len(text) > 4000:
        for i in range(0, len(text) - 4000, 4000):
            await context.bot.send_message(chat_id=chat_id, text=text[i:i+4000], parse_mode='HTML')
        await context.bot.send_message(chat_id=chat_id, text=text[i+4000:], parse_mode='HTML')
        await send_message_with_keyboard(context.bot, update, user_data, modify_message=False)
    else:
        await context.bot.edit_message_text(chat_id=chat_id, message_id=query.message.message_id, text=text, parse_mode='HTML')

async def offer_details_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Callback handler triggered.")
    query = update.callback_query
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    logging.info(f"Chat ID: {chat_id}, Query data: {query.data}")
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    user_data = await user_manager.get_user(chat_id)
    if not user_data:
        logging.warning(f"No user data found for chat ID: {chat_id}")
        return
    await query.answer()
    offer_id = query.data.split('_')[2]
    text_lang = eval(f"{user_data['language']}_texts")
    text = await offer_details(user_data, offer_id)
    logging.info(f"Offer details text and link formed")
    keyboard: list[list[InlineKeyboardButton]] = [[InlineKeyboardButton(text_lang['offer_details']['keyboard']['language_original'], callback_data=f"offer_original_{offer_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if len(text) > 4000:
        for i in range(0, len(text) - 4000, 4000):
            await context.bot.send_message(chat_id=user_data.get('chat_id', 0), text=f"{text[i:i+4000]}\n\n{text_lang['offer_details']['text_more']}", parse_mode='HTML')
        await context.bot.send_message(chat_id=user_data.get('chat_id', 0), text=f"{text[i+4000:]}", reply_markup=reply_markup, parse_mode='HTML')
        await send_message_with_keyboard(context.bot, update, user_data, modify_message=False)
    else:
        await context.bot.edit_message_text(chat_id=user_data.get('chat_id', 0), message_id=message_id, text=text, reply_markup=reply_markup, parse_mode='HTML')


async def clean_database(context: ContextTypes.DEFAULT_TYPE):
    await finder_manager.delete_incomplete_finders()


# Initialize bot with application builder
application = ApplicationBuilder().token(TOKEN).build()
# Account handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("stop", stop))
# application.add_handler(CommandHandler("delete_account", delete_account))

# # Settings handlers
# # application.add_handler(CommandHandler("set_language", set_language))
# application.add_handler(CommandHandler("set_address", set_address_command))
# application.add_handler(CommandHandler("set_new_finder", set_new_finder_command))
# application.add_handler(CommandHandler("help", help_command))
# application.add_handler(CommandHandler("set_notifications", set_notifications_command))
# # application.add_handler(CommandHandler("my_data", get_user_data))
# # application.add_handler(CommandHandler("my_offers", get_my_offers))
# application.add_handler(CommandHandler("delete_finder", delete_finder))

# Callback handlers
application.add_handler(CallbackQueryHandler(callback_handler, pattern='^lang_'))
application.add_handler(CallbackQueryHandler(callback_handler, pattern='^offer_type_'))
application.add_handler(CallbackQueryHandler(main_menu_callback_handler, pattern='^main_menu_'))
application.add_handler(CallbackQueryHandler(settings_menu_callback_handler, pattern='^settings_'))
application.add_handler(CallbackQueryHandler(new_finder_callback_handler, pattern='^finder_type_'))
application.add_handler(CallbackQueryHandler(delete_finder_callback_handler, pattern='^finder_delete_'))
application.add_handler(CallbackQueryHandler(delete_account_callback_handler, pattern='^delete_account_'))
application.add_handler(CallbackQueryHandler(return_to_main_menu, pattern='main'))
application.add_handler(CallbackQueryHandler(offer_details_callback_handler, pattern='^offer_details_'))
application.add_handler(CallbackQueryHandler(offer_original_callback_handler, pattern='^offer_original_'))
# Add a handler for any other messages
application.add_handler(MessageHandler(filters.TEXT, handle_other_messages))

# Add error handler
application.add_error_handler(error_handler)

# Start the bot
logging.info("Bot is starting...")

# Set up a job queue to clean the cache every 10 minutes
job_queue = application.job_queue
job_queue.run_repeating(clean_cache, interval=600, first=0)  # 600 seconds = 10 minutes
job_queue.run_repeating(clean_database, interval=12*60*60, first=0)  # 12 hours


application.run_polling(drop_pending_updates=True)

