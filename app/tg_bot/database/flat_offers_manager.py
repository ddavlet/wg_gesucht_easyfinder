from typing import Dict, Optional, List
import time
from datetime import datetime, timedelta
from decimal import Decimal
from database.database import create_database, validate_flat_offer
import logging  # Import logging module

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

db = create_database()

if db is None:
    print("Database not initialized")
    exit(1)

class FlatOffersManager:
    def __init__(self):
        self.db = db
        self.offers_collection = self.db['flat_offers']
        self.cached_offers: Dict[str, dict] = {}
        self.last_access: Dict[str, float] = {}
        self.cache_duration = 600  # 10 minutes in seconds
        self.life_duration = 10*24*60*60  # 10 days in seconds
        logging.info("FlatOffersManager initialized")  # Log initialization

    async def get_offer(self, data_id: str) -> Optional[dict]:
        current_time = time.time()

        # Check if offer is in cache and still fresh
        if data_id in self.cached_offers:
            if current_time - self.last_access[data_id] < self.cache_duration:
                self.last_access[data_id] = current_time
                return self.cached_offers[data_id]
            else:
                # Remove expired cache
                del self.cached_offers[data_id]
                del self.last_access[data_id]

        # Get from database
        offer = self.offers_collection.find_one({'data_id': data_id})
        if offer and offer['is_active']:
            self.cached_offers[data_id] = offer
            self.last_access[data_id] = current_time
            return offer
        return None

    async def save_offer(self, offer_data: dict):
        """Save a new flat offer if it doesn't already exist"""
        data_id: str = offer_data['data_id']
        if not validate_flat_offer(offer_data):
            logging.warning("Invalid offer data")  # Log warning for invalid data
            return False
        # Check if the offer already exists
        existing_offer = self.get_offer(data_id)
        if existing_offer:
            return False # Exit if the offer already exists

        # Ensure required fields
        offer_data['is_active'] = True
        offer_data['created_at'] = datetime.now()
        if 'availability' not in offer_data:
            offer_data['availability'] = {
                'listed_at': datetime.now()
            }
        # Update cache
        self.cached_offers[data_id] = offer_data
        self.last_access[data_id] = time.time()

        # Update database
        self.offers_collection.update_one(
            {'data_id': data_id},
            {'$set': offer_data},
            upsert=True
        )
        return True # Return True if the offer was saved
    async def deactivate_offer(self, data_id: str):
        """Mark an offer as inactive"""
        offer = await self.get_offer(data_id)
        if offer:
            offer['is_active'] = False
            self.offers_collection.update_one(
                {'data_id': data_id},
                {'$set': {'is_active': False}}
            )
            # Remove from cache
            if data_id in self.cached_offers:
                del self.cached_offers[data_id]
                del self.last_access[data_id]

    async def delete_offer(self, data_id: str):
        """Permanently delete an offer"""
        # Remove from cache
        if data_id in self.cached_offers:
            del self.cached_offers[data_id]
            del self.last_access[data_id]

        # Remove from database
        self.offers_collection.delete_one({'data_id': data_id})

    async def find_matching_offers(self, user_settings: dict) -> List[dict]:
        """Find offers matching user preferences"""
        query = {'is_active': True}

        # Add city filter if specified
        if user_settings.get('city'):
            query['address.city'] = user_settings['city']

        # Add price range filter if specified
        if user_settings.get('max_price'):
            query['costs.base_rent'] = {'$lte': Decimal(str(user_settings['max_price']))}

        # Add furnished filter if specified
        if user_settings.get('furnished') is not None:
            query['properties.furnished'] = user_settings['furnished']

        # Add district filter if specified
        if user_settings.get('districts'):
            query['address.district'] = {'$in': user_settings['districts']}

        # Find matching offers
        offers = self.offers_collection.find(
            query,
            sort=[('availability.listed_at', -1)]  # Sort by newest first
        ).limit(10)  # Limit to 10 results

        return list(offers)

    async def get_active_offers_count(self) -> int:
        """Get count of active offers"""
        return await self.offers_collection.count_documents({'is_active': True})

    async def cleanup_old_offers(self, days: int = 30):
        """Deactivate offers older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Find and deactivate old offers
        old_offers = self.offers_collection.find({
            'is_active': True,
            'availability.listed_at': {'$lt': cutoff_date}
        })

        for offer in old_offers:
            self.deactivate_offer(offer['data_id'])

    async def get_offers_by_price_range(self, min_price: float, max_price: float) -> List[dict]:
        """Get active offers within price range"""
        query = {
            'is_active': True,
            'costs.base_rent': {
                '$gte': Decimal(str(min_price)),
                '$lte': Decimal(str(max_price))
            }
        }
    async def update_offer_data(self, data_id: str, updated_data: dict) -> bool:
        """Update offer data by data_id"""
        result = self.offers_collection.update_one(
            {'data_id': data_id},
            {'$set': updated_data}
        )
        return result.modified_count > 0

    async def get_active_offers(self) -> List[dict]:
        """Get active offers"""
        return list(self.offers_collection.find({'is_active': True}))

    async def deactivate_expired_offers(self):
        """Deactivate offers older than life duration"""
        cutoff_date = time.time() - self.life_duration
        self.offers_collection.update_many(
            {'is_active': True, 'created_at': {'$lt': cutoff_date}},
            {'$set': {'is_active': False}}
        )

    async def clean_expired_cache(self):
        """Clean expired cache"""
        for data_id in list(self.cached_offers):
            if self.last_access[data_id] + self.cache_duration < time.time():
                del self.cached_offers[data_id]
                del self.last_access[data_id]
