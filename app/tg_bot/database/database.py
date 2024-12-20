from pymongo import MongoClient
import os
from typing import Dict, Any

def create_database():
    """Create and initialize the database"""
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://admin:your_mongodb_password@localhost:27017')
    client = MongoClient(MONGODB_URI)
    db = client[os.getenv('MONGO_DB_NAME', 'app_db')]

    # Create collections if they don't exist
    if 'flat_offers' not in db.list_collection_names():
        print("No flat_offers collection found")
        return None

    if 'users' not in db.list_collection_names():
        db.create_collection('users')
        print("Created 'users' collection")

    if 'finders' not in db.list_collection_names():
        db.create_collection('finders')
        print("Created 'finders' collection")

    print("Database initialized successfully")
    return db

def validate_user_data(user_data: Dict[str, Any]) -> bool:
    """Validate user data"""
    required_fields = ['chat_id', 'is_active', 'notifications', 'premium_subscription']
    for field in required_fields:
        if field not in user_data:
            print(f"Validation error: Missing field {field}")
            return False
    if not isinstance(user_data['chat_id'], int):
        print("Validation error: 'chat_id' must be an integer")
        return False
    if not isinstance(user_data['is_active'], bool):
        print("Validation error: 'is_active' must be a boolean")
        return False
    if not isinstance(user_data['notifications'], bool):
        print("Validation error: 'notifications' must be a boolean")
        return False
    if not isinstance(user_data['premium_subscription'], bool):
        print("Validation error: 'premium_subscription' must be a boolean")
        return False
    return True

def validate_finder_data(finder_data: Dict[str, Any]) -> bool:
    """Validate finder data"""
    required_fields = ['finder_id', 'type', 'duration', 'user_id']
    for field in required_fields:
        if field not in finder_data:
            print(f"Validation error: Missing field {field}")
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
        'duration': -1,
        'user_id': 0
    }



