import logging
import os
import json
from database.user_manager import UserManager
from database.finder_manager import FinderManager
from database.flat_offers_manager import FlatOffersManager
from translatorapi import TranslatorAPI
from mapsapi import MapsAPI

maps_api = MapsAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
# Add a file handler for logging
file_handler = logging.FileHandler('warning.log')
info_handler = logging.FileHandler('info.log')
file_handler.setLevel(logging.WARNING)  # Set the level for the file handler
info_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
info_handler.setFormatter(formatter)
# Get the root logger and add the file handler
logger = logging.getLogger()
logger.addHandler(file_handler)
logger.addHandler(info_handler)

# Managers
user_manager = UserManager()
flat_offers_manager = FlatOffersManager()
finder_manager = FinderManager(flat_offers_manager)

# Load language files
LANGUAGE_FILES = {}
language_dir = './languages'
for filename in os.listdir(language_dir):
    if filename.endswith('.json'):
        lang_code = filename.split('.')[0]
        LANGUAGE_FILES[lang_code] = os.path.join(language_dir, filename)

# Check if any language file path is None
for lang, path in LANGUAGE_FILES.items():
    if path is None:
        print(f"Warning: LANGUAGE_FILE_{lang.upper()} is not set in the environment variables.")

# Load language files
# Load all language files dynamically
language_texts = {}
for lang, path in LANGUAGE_FILES.items():
    if path:
        try:
            with open(path, 'r') as f:
                language_texts[f"{lang}_texts"] = json.load(f)
        except FileNotFoundError:
            logging.error(f"Language file not found for {lang}: {path}")
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON in language file for {lang}: {path}")
        except Exception as e:
            logging.error(f"Error loading language file for {lang}: {str(e)}")

# Create global variables for each language
for lang_var, texts in language_texts.items():
    globals()[lang_var] = texts

en_translator = TranslatorAPI('en')
de_translator = TranslatorAPI('de')
ru_translator = TranslatorAPI('ru')

async def main_menu(user_data):
    text_lang = eval(f"{user_data['language']}_texts")
    return text_lang['main']['text'], text_lang['main']['keyboard']

async def language_changed(user_data):
    logging.info(f"Language changed to {user_data['language']} for chat_id={user_data.get('chat_id', 0)}")
    text_lang = eval(f"{user_data['language']}_texts")
    return text_lang['settings']['language_changed'], None

async def offer_type_prompt(user_data):
    text_lang = eval(f"{user_data['language']}_texts")
    return text_lang['new_finder']['offer_type_prompt'], None

async def set_language(user_data):
    chat_id = user_data.get('chat_id', 0)
    logging.info(f"Language selection menu requested: chat_id={chat_id}")
    text_lang = eval(f"{user_data['language']}_texts")
    text = text_lang['language_choose_menu'].get('text')
    keyboard = text_lang['language_choose_menu'].get('keyboard')
    return text, keyboard

async def get_my_offers(user_data):
    chat_id = user_data.get('chat_id', 0)
    logging.info(f"Retrieving offers for chat_id={chat_id}")
    text_lang = eval(f"{user_data['language']}_texts")
    translator = eval(f"{user_data['language']}_translator")
    if user_data['preferences']['address'] == '':
        logging.warning(f"No address set for chat_id={chat_id}")
        return text_lang['errors']['no_address_set']

    finders = await finder_manager.get_finders_by_user(chat_id)
    logging.info(f"Processing {len(finders)} finders for chat_id={chat_id}")
    for finder in finders:
        await finder_manager.find_offers(finder, user_data['preferences']['address'])

    offers_ids = await finder_manager.get_findings_by_user(chat_id)
    if not offers_ids:
        logging.info(f"No offers found for chat_id={chat_id}")
        return text_lang['errors']['no_offers_found']

    response = []
    for offer_id in offers_ids:
        offer = await flat_offers_manager.get_offer(offer_id)
        if offer is None:
            logging.warning(f"Offer not found: chat_id={chat_id}, offer_id={offer_id}")
            continue
        response.append({
            'id': offer_id,
            'text': text_lang['offer_data']['start'] + '\n' +
            text_lang['offer_data']['title'] + f'{translator.translate(offer["name"])}' + '\n' +
            text_lang['offer_data']['location'] + offer['address'] + '\n' +
            text_lang['offer_data']['rent'] + str(offer['total_rent']) + '\n' +
            text_lang['offer_data']['link'] + offer['link']}
        )
    if response == []:
        return None
    logging.info(f"Found {len(response)} valid offers for chat_id={chat_id}")
    return response

async def settings_menu(user_data):
    logging.info('Settings menu command recieved.')
    chat_id = user_data.get('chat_id', 0)
    logging.info(f"Chat ID: {chat_id}")
    text_lang = eval(f"{user_data['language']}_texts")
    response = text_lang['settings_menu'].get('text')
    keyboard = text_lang['settings_menu'].get('keyboard')
    return response, keyboard

async def new_finder_success(user_data):
    logging.info("New finder success command received.")
    text_lang = eval(f"{user_data['language']}_texts")
    return text_lang['new_finder']['new_finder_success'], None

async def get_user_data(user_data):
    chat_id = user_data.get('chat_id', 0)
    logging.info(f"Retrieving user data for chat_id={chat_id}")
    text_lang = eval(f"{user_data['language']}_texts")

    finders = await finder_manager.get_finders_by_user(chat_id)
    logging.info(f"Found {len(finders)} finders for chat_id={chat_id}")

    response = (
        text_lang['user_data']['start'] + "\n\n" +
        text_lang['user_data']['name'] + user_data['name'] + "\n" +
        text_lang['user_data']['address'] + user_data['preferences']['address'] + "\n" +
        text_lang['user_data']['distance'] + str(user_data['preferences']['distance']) + "\n" +
        text_lang['user_data']['notifications'] + str(user_data['preferences']['notifications']) + "\n" +
        text_lang['user_data']['language'] + user_data['language'] + "\n\n" +
        text_lang['user_data']['finders'] + "\n"
    )

    for finder in finders:
        response += "-----------------------------------\n"
        response += text_lang['user_data']['next_finder'] + "\n"
        response += text_lang['finder_data']['id'] + str(finder['finder_id']) + "\n"
        response += text_lang['finder_data']['type'] + text_lang['new_finder']['new_finder_travel_mode_keyboard'].get('finder_type_travel_' + finder['type']) + "\n"
        response += text_lang['finder_data']['offer_type'] + text_lang['new_finder']['new_finder_housing_type_keyboard'].get('finder_type_housing_' + finder['offer_type']) + "\n"
        response += text_lang['finder_data']['duration'] + str(finder['duration'] / 60) + f" {text_lang['offer_details']['duration_param']}" + "\n"

    # response += "\n\n" + text_lang['user_data']['end']
    logging.info(f"User data sent to chat ID: {chat_id}")
    return response, None

async def address_set_success(user_data):
    logging.info(f"Address set successfully for chat_id={user_data.get('chat_id', 0)}")
    text_lang = eval(f"{user_data['language']}_texts")
    return text_lang['settings']['address_set_success'], None

async def address_set_error(user_data):
    logging.warning(f"Invalid address for chat_id={user_data.get('chat_id', 0)}")
    text_lang = eval(f"{user_data['language']}_texts")
    return text_lang['errors']['invalid_address'], None

async def set_address(user_data):
    logging.info(f"Address prompt for chat_id={user_data.get('chat_id', 0)}")
    text_lang = eval(f"{user_data['language']}_texts")
    return text_lang['settings']['address_prompt'], None

async def help_command(user_data):
    text_lang = eval(f"{user_data['language']}_texts")
    return text_lang['info_messages']['help'], None

async def set_new_finder(user_data):
    logging.info(f"New finder setup started for chat_id={user_data.get('chat_id', 0)}")
    text_lang = eval(f"{user_data['language']}_texts")
    text = text_lang['new_finder'].get('new_finder_housing_type_prompt')
    keyboard = text_lang['new_finder'].get('new_finder_housing_type_keyboard')
    return text, keyboard

async def new_finder_duration(user_data):
    chat_id = user_data.get('chat_id', 0)
    finder_id = user_data.get('finder_id', 0)
    finder = await finder_manager.get_finder(finder_id)
    if not finder:
        logging.warning(f"Finder not found: chat_id={chat_id}, finder_id={finder_id}")
        return
    type = finder['type']
    text_lang = eval(f"{user_data['language']}_texts")
    type = text_lang['new_finder'].get('keyboard').get('finder_type_' + type)
    text = text_lang['new_finder'].get('offer_type_prompt') + type + "\n"
    text += text_lang['new_finder'].get('duration_prompt')
    keyboard = text_lang['new_finder'].get('main_menu')
    return text, keyboard

async def delete_finder(user_data):
    chat_id = user_data.get('chat_id', 0)
    logging.info(f"Listing finders for deletion: chat_id={chat_id}")
    text_lang = eval(f"{user_data['language']}_texts")
    finders = await finder_manager.get_finders_by_user(chat_id)
    text = text_lang['finder_data']['all'] + "\n\n"
    for finder in finders:
        text += '-----------------------------------\n'
        text += "<b>" + text_lang['finder_data']['id'] + str(finder['finder_id']) + "</b>\n"
        type = text_lang['new_finder'].get('new_finder_travel_mode_keyboard').get('finder_type_travel_' + finder['type'])
        text += text_lang['finder_data']['type'] + type + "\n"
        offer_type = text_lang['new_finder']['new_finder_housing_type_keyboard'].get('finder_type_housing_' + finder['offer_type'])
        text += text_lang['finder_data']['offer_type'] + offer_type + "\n"
        text += text_lang['finder_data']['duration'] + str(finder['duration'] / 60) + f' {text_lang["offer_details"]["duration_param"]}' + "\n"
    text += text_lang['finder_data']['end']
    keyboard = {}
    for finder in finders:
        keyboard["finder_delete_" + str(finder['finder_id'])] = str(finder['finder_id'])
    keyboard['main'] = text_lang['navigation'].get('cancel').get('cancel')
    return text, keyboard

async def delete_finder_success(user_data):
    logging.info(f"Finder deleted successfully for chat_id={user_data.get('chat_id', 0)}")
    text_lang = eval(f"{user_data['language']}_texts")
    return text_lang['finder_data']['delete_success'], None

async def get_my_finders(user_data):
    chat_id = user_data.get('chat_id', 0)
    logging.info(f"Retrieving finders for chat_id={chat_id}")
    text_lang = eval(f"{user_data['language']}_texts")
    finders = await finder_manager.get_finders_by_user(chat_id)
    logging.info(f"Found {len(finders)} finders for chat_id={chat_id}")
    text = text_lang['finder_data']['all'] + "\n\n"
    for finder in finders:
        text += '-----------------------------------\n'
        text += "<b>" + text_lang['finder_data']['id'] + str(finder['finder_id']) + "</b>\n"
        type = text_lang['new_finder'].get('new_finder_travel_mode_keyboard').get('finder_type_travel_' + finder['type'])
        text += text_lang['finder_data']['type'] + type + "\n"
        offer_type = text_lang['new_finder']['new_finder_housing_type_keyboard'].get('finder_type_housing_' + finder['offer_type'])
        text += text_lang['finder_data']['offer_type'] + offer_type + "\n"
        text += text_lang['finder_data']['duration'] + str(finder['duration'] / 60) + f' {text_lang["offer_details"]["duration_param"]}' + "\n"
    return text, None

async def help_menu(user_data):
    text_lang = eval(f"{user_data['language']}_texts")
    return text_lang['help_menu'].get('text'), None

async def delete_account(user_data):
    chat_id = user_data.get('chat_id', 0)
    logging.info(f"Account deletion confirmation requested: chat_id={chat_id}")
    text_lang = eval(f"{user_data['language']}_texts")
    text = text_lang['delete_account']['text']
    keyboard = text_lang['delete_account']['keyboard']
    return text, keyboard

async def delete_account_success(user_data):
    logging.info(f"Account deleted successfully: chat_id={user_data.get('chat_id', 0)}")
    text_lang = eval(f"{user_data['language']}_texts")
    return text_lang['delete_account']['delete_success'], None

async def delete_account_cancel(user_data):
    logging.info(f"Account deletion cancelled: chat_id={user_data.get('chat_id', 0)}")
    text_lang = eval(f"{user_data['language']}_texts")
    return text_lang['delete_account']['delete_cancel'], None

async def stop_bot(user_data):
    chat_id = user_data.get('chat_id', 0)
    logging.info(f"Bot stopped for chat_id={chat_id}")
    text_lang = eval(f"{user_data['language']}_texts")
    user_data['is_active'] = False
    await user_manager.save_user(chat_id, user_data)
    return text_lang['stop_bot']['text'], None

async def validate_address(user_data, address: str):
    result, is_valid = await maps_api.validate_address(address)
    answer: str = ""
    if is_valid and result:
        user_data['preferences']['address'] = result['result']['address']['formattedAddress']
        user_data['preferences']['address_id'] = result['result']['geocode']['placeId']
        answer = result['result']['address']['formattedAddress']
        return answer, True
    elif not is_valid and result:
        answer = result['componentName']['text']
        return answer, False
    else:
        answer = "Address cannot be validated."
        return answer, False

async def offer_details(user_data, offer_id):
    chat_id = user_data.get('chat_id', 0)
    logging.info(f"Retrieving offer details: chat_id={chat_id}, offer_id={offer_id}")
    text_lang = eval(f"{user_data['language']}_texts")
    translator = eval(f"{user_data['language']}_translator")
    offer = await flat_offers_manager.get_offer(offer_id)
    if offer is None:
        logging.warning(f"Offer not found: chat_id={chat_id}, offer_id={offer_id}")
        return text_lang['errors']['offer_not_found']
    finders = await finder_manager.get_finders_by_user(chat_id)
    finders_with_offer = [f for f in finders if offer_id in f['offers']]
    logging.info(f"Found {len(finders_with_offer)} finders with offer {offer_id}")
    finder_text: str = ""
    for finder in finders_with_offer:
        finder_text += "  " + text_lang['finder_data']['id'] + str(finder['finder_id']) + "\n"
        type = text_lang['new_finder'].get('new_finder_travel_mode_keyboard').get('finder_type_travel_' + finder['type'])
        logging.info(f"Type found: {type} for finder type: {finder['type']}")
        finder_text += "  " + text_lang['finder_data']['type'] + type + "\n"
        offer_type = text_lang['new_finder']['new_finder_housing_type_keyboard'].get('finder_type_housing_' + finder['offer_type'])
        finder_text += "  " + text_lang['finder_data']['offer_type'] + offer_type + "\n"
        finder_text += "  " + text_lang['finder_data']['duration'] + text_lang['offer_details']['duration'] + str(finder['duration'] / 60) + f' {text_lang["offer_details"]["duration_param"]}' + "\n"
    text: str = ""
    logging.info(f"building text")
    print(offer)
    full_description = ""
    if offer.get('description'):  # Check if description exists and is not None
        for description in offer['description']:
            full_description += description + "\n"
    translated_description = ""
    if offer.get('description'):  # Check if description exists and is not None
        for description in offer['description']:
            translated_description += translator.translate(description) + "\n"
    if len(translated_description) > 500:
        translated_description = translated_description[:500] + "..."
    logging.info(f"full description: {full_description}")
    translated_details = ""
    for detail in offer['object_details']:
        translated_details += f"  {translator.translate(detail)}\n"
    text = (text_lang['offer_details']['text'] + '\n\n' +
    text_lang['offer_details']['title'] + f'{translator.translate(offer["name"])}' + '\n' +
    text_lang['offer_details']['location'] + offer['address'] + '\n\n' +
    text_lang['offer_details']['finder'] + "\n" + finder_text + '\n' +
    text_lang['offer_details']['costs'] + "\n" +
    "  " + text_lang['offer_details']['total_rent'] + str(offer['total_rent']) + '\n' +
    "  " + text_lang['offer_details']['rent'] + str(offer['costs']['rent']) + '\n' +
    "  " + text_lang['offer_details']['additional_costs'] + str(offer['costs'].get('additional_costs', 'N/A')) + '\n' +
    "  " + text_lang['offer_details']['other_costs'] + str(offer['costs'].get('other_costs', 'N/A')) + '\n' +
    "  " + text_lang['offer_details']['deposit'] + str(offer['costs'].get('deposit', 'N/A')) + '\n' +
    "\n" +
    text_lang['offer_details']['object_details_translation'] + "\n" + translated_details + '\n' +
    text_lang['offer_details']['translation'] + translated_description + '\n' +
    text_lang['offer_details']['link'] + offer['link'])
    logging.info(f"Offer details: {text[:100]}...")
    return text

async def original_offer_details(user_data, offer_id):
    chat_id = user_data.get('chat_id', 0)
    logging.info(f"Retrieving original offer details: chat_id={chat_id}, offer_id={offer_id}")
    text_lang = eval(f"{user_data['language']}_texts")
    translator = eval(f"{user_data['language']}_translator")
    offer = await flat_offers_manager.get_offer(offer_id)
    finders = await finder_manager.get_finders_by_user(chat_id)
    finders_with_offer = [f for f in finders if offer_id in f['offers']]
    logging.info(f"Found {len(finders_with_offer)} finders with offer {offer_id}")
    finder_text: str = ""
    for finder in finders_with_offer:
        finder_text += "  " + text_lang['finder_data']['id'] + str(finder['finder_id']) + "\n"
        type = text_lang['new_finder'].get('new_finder_travel_mode_keyboard').get('finder_type_travel_' + finder['type'])
        logging.info(f"Type found: {type} for finder type: {finder['type']}")
        finder_text += "  " + text_lang['finder_data']['type'] + type + "\n"
        offer_type = text_lang['new_finder']['new_finder_housing_type_keyboard'].get('finder_type_housing_' + finder['offer_type'])
        finder_text += "  " + text_lang['finder_data']['offer_type'] + offer_type + "\n"
        finder_text += "  " + text_lang['finder_data']['duration'] + text_lang['offer_details']['duration'] + str(finder['duration'] / 60) + f' {text_lang["offer_details"]["duration_param"]}' + "\n"
    text: str = ""
    logging.info(f"building text")
    full_description = ""
    if offer.get('description'):  # Check if description exists and is not None
        for description in offer['description']:
            full_description += description + "\n"

    if len(full_description) > 500:
        full_description = full_description[:500] + "..."
    logging.info(f"full description: {full_description[:100]}...")
    details = ""
    for detail in offer['object_details']:
        details += f"  {detail}\n"
    text = (text_lang['offer_details']['text'] + '\n\n' +
    text_lang['offer_details']['title'] + offer['name'] + '\n' +
    text_lang['offer_details']['location'] + offer['address'] + '\n\n' +
    text_lang['offer_details']['finder'] + "\n" + finder_text + '\n' +
    text_lang['offer_details']['costs'] + "\n" +
    "  " + text_lang['offer_details']['total_rent'] + str(offer['total_rent']) + '\n' +
    "  " + text_lang['offer_details']['rent'] + str(offer['costs']['rent']) + '\n' +
    "  " + text_lang['offer_details']['additional_costs'] + str(offer['costs'].get('additional_costs', 'N/A')) + '\n' +
    "  " + text_lang['offer_details']['other_costs'] + str(offer['costs'].get('other_costs', 'N/A')) + '\n' +
    "  " + text_lang['offer_details']['deposit'] + str(offer['costs'].get('deposit', 'N/A')) + '\n' +
    "\n" +
    text_lang['offer_details']['object_details'] + "\n" + details + '\n' +
    text_lang['offer_details']['description'] + full_description + '\n' +
    text_lang['offer_details']['link'] + offer['link'])
    logging.info(f"Offer details: {text[:100]}...")
    return text


async def user_data_entry_first(user_data):
    text_lang = eval(f"{user_data['language']}_texts")
    return text_lang['user_data_entry']['first'], None

async def user_data_entry_name(user_data):
    text_lang = eval(f"{user_data['language']}_texts")
    return text_lang['user_data_entry']['name'], None
