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
        db.create_collection('flat_offers')
        print("Created 'flat_offers' collection")

    print("Database initialized successfully")

def validate_flat_offer(offer_data: Dict[str, Any]) -> bool:
    """Validate flat offer data"""
    required_fields = ['data_id', 'link', 'is_active', 'costs', 'address', 'availability', 'object_details', 'description']
    for field in required_fields:
        if field not in offer_data:
            print(f"Validation error: Missing field {field}")
            return False
    if not isinstance(offer_data['is_active'], bool):
        print("Validation error: 'is_active' must be a boolean")
        return False
    return True

def get_flat_offer_fields() -> Dict[str, Any]:
    """Return the fields for the flat_offers table"""
    return {
        'data_id': '',
        'link': '',
        'is_active': True,
        'name': '',
        'area': '',
        'images': [],
        'costs': {
            'rent': '0',
            'additional_costs': '0',
            'other_costs': '0',
            'deposit': '0',
            'transfer_agreement': '0',
            'credit_check': '0'
        },
        'address': '',
        'availability': {},
        'object_details': [],
        'description': []
    }





