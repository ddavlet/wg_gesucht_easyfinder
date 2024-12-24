import json
import os
import logging
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
flat_offers_manager = FlatOffersManager()

# Configure logging
logging.basicConfig(level=logging.INFO)


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
    message_id = update.callback_query.message.message_id
    keyboard_texts = None
    if state is None:
        state = user_data['state']
        text = text_lang[state]['text']
        keyboard_texts = text_lang[state].get('keyboard', None)
        logging.info(f"State is None, using user state: {state}")
    else:
        text, keyboard_texts = await eval(state)(user_data)
        logging.info(f"Using state: {state} to get text and keyboard texts.")

    logging.info(f"Message ID: {message_id}, Text: {text}, Keyboard texts: {keyboard_texts}")
    if keyboard_texts is None:
        keyboard_texts = {'main': 'Main menu'}
    keyboard = await create_keyboard(keyboard_texts)
    reply_markup = InlineKeyboardMarkup(keyboard)
    await bot.edit_message_text(chat_id=user_data['chat_id'], message_id=message_id, text=text, reply_markup=reply_markup)
    logging.info("Message edited with new text and reply markup.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Start command received.")
    chat_id = update.effective_chat.id
    logging.info(f"Chat ID: {chat_id}")
    user_data = await user_manager.get_user(chat_id)
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
        await context.bot.send_message(chat_id=chat_id, text=text_lang['start']['text_new_profile'])
    text_lang = eval(f"{user_data['language']}_texts")
    await context.bot.send_message(chat_id=chat_id, text=text_lang['main']['text'], reply_markup= InlineKeyboardMarkup(await create_keyboard(text_lang['main']['keyboard'])))
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
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Set language command received.")
    chat_id = update.effective_chat.id
    logging.info(f"Chat ID: {chat_id}")
    user_data = await user_manager.get_user(chat_id)
    logging.info(f"User data: {user_data}")
    if not user_data:
        logging.warning(f"No user data found for chat ID: {chat_id}")
        return
    text_lang = eval(f"{user_data['language']}_texts")
    keyboard = [
        [InlineKeyboardButton("English", callback_data='lang_en')],
        [InlineKeyboardButton("Deutsch", callback_data='lang_de')],
        [InlineKeyboardButton("Русский", callback_data='lang_ru')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, text=text_lang['settings']['choose_language'], reply_markup=reply_markup)
    logging.info("Language selection keyboard sent.")

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
        await context.bot.send_message(
            chat_id=chat_id,
            text=text_lang['settings']['language_changed']
        )
        logging.info(f"User {chat_id} language changed to {lang}.")
    elif query.data.startswith('finder_type_'):
        logging.info("Finder type selection requested.")
        new_finder = get_finder_fields()
        new_finder['type'] = query.data.split('_')[2]
        new_finder['user_id'] = user_data['chat_id']
        new_finder['finder_id'] = await finder_manager.generate_finder_id()
        await finder_manager.save_finder(chat_id, new_finder['finder_id'], new_finder)
        user_data['finder_id'] = new_finder['finder_id']
        await user_manager.save_user(chat_id, user_data)
        logging.info(f"New finder created for user {chat_id} with ID {new_finder['finder_id']}.")
        keyboard = [
            [InlineKeyboardButton("WG-room", callback_data='offer_type_wgroom')],
            [InlineKeyboardButton("1 room flat", callback_data='offer_type_1roomflat')],
            [InlineKeyboardButton("2+ room flat", callback_data='offer_type_2roomflat')],
            [InlineKeyboardButton("House", callback_data='offer_type_house')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=chat_id,
            text=text_lang['new_finder']['offer_type_prompt'],
            reply_markup=reply_markup
        )

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

async def set_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Set settings command received.")
    chat_id = update.effective_chat.id
    settings = json.loads(update.message.text.split(' ', 1)[1])
    logging.info(f"Settings received: {settings}")
    user_data = await user_manager.get_user(chat_id)
    logging.info(f"User data: {user_data}")
    if not user_data:
        logging.warning(f"No user data found for chat ID: {chat_id}")
        return
    text_lang = eval(f"{user_data['language']}_texts")
    user_data.update(settings)
    await user_manager.save_user(chat_id, user_data)
    await context.bot.send_message(
        chat_id=chat_id,
        text=text_lang['settings']['updated']
    )
    logging.info(f"User {chat_id} settings updated.")

async def delete_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Delete account command received.")
    chat_id = update.effective_chat.id
    logging.info(f"Chat ID: {chat_id}")
    user_data = await user_manager.get_user(chat_id)
    logging.info(f"User data: {user_data}")
    if not user_data:
        logging.warning(f"No user data found for chat ID: {chat_id}")
        return
    text_lang = eval(f"{user_data['language']}_texts")
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data='delete_account_yes')],
        [InlineKeyboardButton("No", callback_data='delete_account_no')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=chat_id,
        text=text_lang['account']['delete_confirmation'],
        reply_markup=reply_markup
    )
    logging.info(f"Delete account confirmation sent to user {chat_id}.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Update {update} caused error {context.error}")

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
        validators = Validators(user_data, text_lang)
        user_data['state'] = 'main'
        try:
            answer = await validators.validate_address(update.message.text)
            logging.info(f"Address validation result: {answer}")
        except Exception as e:
            logging.error(f"Error validating address: {e}")
            answer = text_lang['errors']['wrong_address']
        await user_manager.save_user(chat_id, user_data)
        await context.bot.send_message(chat_id=chat_id, text=answer)
    elif user_data['state'] == 'new_finder_duration':
        logging.info("New finder duration setting in progress.")
        try:
            duration: int = int(update.message.text)
            if duration > 300:
                raise Exception("Duration is too long")
            finder_data = await finder_manager.get_finder(user_data['finder_id'])
            finder_data['duration'] = duration * 60  # convert to seconds
            await finder_manager.save_finder(chat_id, user_data['finder_id'], finder_data)
            await context.bot.send_message(chat_id=chat_id, text=text_lang['new_finder']['new_finder_success'])
            logging.info(f"Finder duration set to {duration} minutes for user {chat_id}.")
        except Exception as e:
            logging.error(f"Error setting duration: {e}")
            finder_manager.delete_finder(user_data['finder_id'])
            await context.bot.send_message(chat_id=chat_id, text=text_lang['errors']['wrong_duration'])
        user_data['state'] = 'main'
        user_data['finder_id'] = None
        await user_manager.save_user(chat_id, user_data)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data = await user_manager.get_user(chat_id)
    if not user_data:
        logging.warning(f"No user data found for chat ID: {chat_id}")
        return
    text_lang = eval(f"{user_data['language']}_texts")
    return text_lang['info_messages']['help'], None

async def set_new_finder_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data = await user_manager.get_user(chat_id)
    if not user_data:
        logging.warning(f"No user data found for chat ID: {chat_id}")
        return
    text_lang = eval(f"{user_data['language']}_texts")
    keyboard = [
        [InlineKeyboardButton(text_lang['new_finder']['walking'], callback_data='finder_type_walking')],
        [InlineKeyboardButton(text_lang['new_finder']['bicycling'], callback_data='finder_type_bicycling')],
        [InlineKeyboardButton(text_lang['new_finder']['driving'], callback_data='finder_type_driving')],
        [InlineKeyboardButton(text_lang['new_finder']['transit'], callback_data='finder_type_transit')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, text=text_lang['new_finder']['new_finder_prompt'], reply_markup=reply_markup)

async def set_address_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data = await user_manager.get_user(chat_id)
    if not user_data:
        logging.warning(f"No user data found for chat ID: {chat_id}")
        return
    text_lang = eval(f"{user_data['language']}_texts")
    # Prompt the user to enter their address
    user_data['state'] = 'address'
    await user_manager.save_user(chat_id, user_data)
    await context.bot.send_message(
        chat_id=chat_id,
        text=text_lang['settings']['address_prompt']
    )

async def clean_cache(context: ContextTypes.DEFAULT_TYPE):
    user_manager.clean_expired_cache()
    finder_manager.clean_expired_cache()
    finder_manager.delete_expired_finders()

async def set_notifications_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data = await user_manager.get_user(chat_id)
    if not user_data:
        logging.warning(f"No user data found for chat ID: {chat_id}")
        return
    text_lang = eval(f"{user_data['language']}_texts")
    user_data['preferences']['notifications'] = not user_data['preferences']['notifications']
    await user_manager.save_user(chat_id, user_data)
    await context.bot.send_message(chat_id=chat_id, text=text_lang['settings']['notifications_set']['enabled'] if user_data['preferences']['notifications'] else text_lang['settings']['notifications_set']['disabled'])

async def get_user_data(user_data):
    chat_id = user_data['chat_id']
    logging.info(f"Getting user data for chat ID: {chat_id}")
    user_data = await user_manager.get_user(chat_id)
    if not user_data:
        logging.warning(f"No user data found for chat ID: {chat_id}")
        return
    text_lang = eval(f"{user_data['language']}_texts")
    print(user_data)
    response = (
        text_lang['user_data']['start'] +
        text_lang['user_data']['name'] + user_data['name'] +
        text_lang['user_data']['address'] + user_data['preferences']['address'] +
        text_lang['user_data']['distance'] + str(user_data['preferences']['distance']) +
        text_lang['user_data']['notifications'] + str(user_data['preferences']['notifications']) +
        text_lang['user_data']['language'] + user_data['language'] +
        text_lang['user_data']['finders']
    )

    finders = await finder_manager.get_finders_by_user(user_data['chat_id'])
    logging.info(f"Found {len(finders)} finders for user ID: {user_data['chat_id']}")
    for finder in finders:
        response += text_lang['user_data']['next_finder']
        response += text_lang['finder_data']['type'] + finder['type']
        response += text_lang['finder_data']['duration'] + str(finder['duration'])
        response += text_lang['finder_data']['id'] + str(finder['finder_id'])

    response += text_lang['user_data']['end']
    logging.info(f"User data sent to chat ID: {chat_id}")
    return response, None

async def get_my_offers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Get my offers command received.")
    chat_id = update.effective_chat.id
    logging.info(f"Chat ID: {chat_id}")
    user_data = await user_manager.get_user(chat_id)
    logging.info(f"User data: {user_data}")
    if not user_data:
        logging.warning(f"No user data found for chat ID: {chat_id}")
        return
    text_lang = eval(f"{user_data['language']}_texts")
    if user_data['preferences']['address'] == '':
        logging.info("No address set, sending error message.")
        await context.bot.send_message(chat_id=chat_id, text=text_lang['errors']['no_address_set'])
        return
    logging.info("Retrieving offers for finders.")
    finders = await finder_manager.get_finders_by_user(user_data['chat_id'])
    for finder in finders:
        await finder_manager.find_offers(finder, user_data['preferences']['address'])
    logging.info("Retrieving offers for user.")
    offers_ids = await finder_manager.get_findings_by_user(user_data['chat_id'])
    logging.info(f"Offers IDs: {offers_ids}")
    if not offers_ids:
        await context.bot.send_message(chat_id=chat_id, text=text_lang['errors']['no_offers_found'])
        logging.info(f"No offers found for user {chat_id}.")
        return

    for offer_id in offers_ids:
        offer = await flat_offers_manager.get_offer(offer_id)
        if offer is None:
            logging.warning(f"Offer not found for ID {offer_id}, user: {user_data['chat_id']}")
            continue
        response = (
            text_lang['offer_data']['start'] +
            text_lang['offer_data']['title'] + offer['name'] +
            text_lang['offer_data']['location'] + offer['address'] +
            text_lang['offer_data']['rent'] + str(offer['costs']['rent']) +
            text_lang['offer_data']['link'] + offer['link']
        )

        # Send the response to the user
        logging.info(f"Sent offer to user {chat_id}: {offer['name']}")
        return response, None

async def delete_finder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data = await user_manager.get_user(chat_id)
    if not user_data:
        logging.warning(f"No user data found for chat ID: {chat_id}")
        return
    finder_id = update.message.text.split(' ')[1]
    logging.info(f"Deleting finder with ID: {finder_id}")
    await finder_manager.delete_finder(finder_id)
    await context.bot.send_message(chat_id=chat_id, text=f"Finder with ID {finder_id} deleted")
    logging.info(f"Finder with ID {finder_id} deleted for user {chat_id}")

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
        await send_message(context.bot, update, user_data, 'get_user_data')
    elif command_type == 'myfinders':
        await send_message(context.bot, update, user_data, 'my_finders')
    elif command_type == 'myoffers':
        await send_message(context.bot, update, user_data, 'my_offers')
    elif command_type == 'settings':
        await send_message(context.bot, update, user_data, 'settings')
    elif command_type == 'help':
        await send_message(context.bot, update, user_data, 'help')
    elif command_type == 'stop':
        await send_message(context.bot, update, user_data, 'stop')

async def return_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Returning to main menu.")
    user_data = await user_manager.get_user(update.effective_chat.id)
    if not user_data:
        logging.warning(f"No user data found for chat ID: {update.effective_chat.id}")
        return
    text_lang = eval(f"{user_data['language']}_texts")
    await context.bot.edit_message_text(chat_id=user_data['chat_id'], message_id=update.callback_query.message.message_id, text=text_lang['main']['text'], reply_markup=InlineKeyboardMarkup(await create_keyboard(text_lang['main']['keyboard'])))

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
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("set_notifications", set_notifications_command))
application.add_handler(CommandHandler("my_data", get_user_data))
application.add_handler(CommandHandler("my_offers", get_my_offers))
application.add_handler(CommandHandler("delete_finder", delete_finder))

# Callback handlers
application.add_handler(CallbackQueryHandler(callback_handler, pattern='^lang_'))
application.add_handler(CallbackQueryHandler(callback_handler, pattern='^finder_type_'))
application.add_handler(CallbackQueryHandler(callback_handler, pattern='^offer_type_'))
application.add_handler(CallbackQueryHandler(callback_handler, pattern='^delete_account_'))
application.add_handler(CallbackQueryHandler(main_menu_callback_handler, pattern='^main_menu_'))
application.add_handler(CallbackQueryHandler(return_to_main_menu, pattern='main'))

# Add a handler for any other messages
application.add_handler(MessageHandler(filters.TEXT, handle_other_messages))

# Add error handler
application.add_error_handler(error_handler)

# Start the bot
logging.info("Bot is starting...")

# Set up a job queue to clean the cache every 10 minutes
job_queue = application.job_queue
job_queue.run_repeating(clean_cache, interval=600, first=0)  # 600 seconds = 10 minutes

application.run_polling(drop_pending_updates=True)

