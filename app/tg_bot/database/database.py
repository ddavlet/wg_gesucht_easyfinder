import os
import logging
from pymongo import MongoClient
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_database():
    """Create and initialize the database"""
    MONGODB_URI = os.getenv('MONGODB_URI')
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME')
    client = MongoClient(MONGODB_URI)
    db = client[MONGO_DB_NAME]

    # Create collections if they don't exist
    if 'flat_offers' not in db.list_collection_names():
        logging.info("No flat_offers collection found, creating it.")
        db.create_collection('flat_offers')
        logging.info("Created 'flat_offers' collection.")

    if 'users' not in db.list_collection_names():
        db.create_collection('users')
        logging.info("Created 'users' collection.")

    if 'finders' not in db.list_collection_names():
        db.create_collection('finders')
        logging.info("Created 'finders' collection.")

    logging.info("Database initialized successfully")
    return db

def validate_user_data(user_data: Dict[str, Any]) -> bool:
    """Validate user data"""
    required_fields = ['chat_id', 'is_active', 'notifications', 'premium_subscription', 'language']
    for field in required_fields:
        if field not in user_data:
            logging.error(f"Validation error: Missing field {field}")
            return False
    if not isinstance(user_data['chat_id'], int):
        logging.error("Validation error: 'chat_id' must be an integer")
        return False
    if not isinstance(user_data['is_active'], bool):
        logging.error("Validation error: 'is_active' must be a boolean")
        return False
    if not isinstance(user_data['notifications'], bool):
        logging.error("Validation error: 'notifications' must be a boolean")
        return False
    if not isinstance(user_data['premium_subscription'], bool):
        logging.error("Validation error: 'premium_subscription' must be a boolean")
        return False
    if not isinstance(user_data['language'], str):
        logging.error("Validation error: 'language' must be a string")
        return False
    if user_data['language'] not in ['en', 'de', 'ru']:
        logging.error("Validation error: 'language' must be 'en', 'de' or 'ru'")
        return False
    return True

def validate_flat_offer(offer_data: Dict[str, Any]) -> bool:
    """Validate flat offer data"""
    required_fields = ['data_id', 'link', 'is_active', 'costs', 'address', 'availability', 'object_details', 'description']
    for field in required_fields:
        if field not in offer_data:
            logging.error(f"Validation error: Missing field {field}")
            return False
    if not isinstance(offer_data['is_active'], bool):
        logging.error("Validation error: 'is_active' must be a boolean")
        return False
    return True

def validate_finder_data(finder_data: Dict[str, Any]) -> bool:
    """Validate finder data"""
    required_fields = ['finder_id', 'type', 'duration', 'user_id']
    for field in required_fields:
        if field not in finder_data:
            logging.error(f"Validation error: Missing field {field}")
            return False
    return True

def get_user_fields() -> Dict[str, Any]:
    """Return the fields for the users table"""
    return {
        'chat_id': '',
        'is_active': True,
        'name': '',
        'notifications': True,
        'preferences': {
            'address': '',
            'address_id': '',
            'distance': 0,
            'notifications': True
        },
        'premium_subscription': False,
        'language': 'en',
        'state': 'main'
    }

def get_finder_fields() -> Dict[str, Any]:
    """Return the fields for the finders table"""
    return {
        'finder_id': '',
        'type': '',
        'offer_type': '',
        'duration': -1,
        'user_id': 0,
        'offers': [],
        'parsed_offers': []
    }



