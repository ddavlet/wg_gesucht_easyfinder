from typing import Dict, Optional, List
import time
from datetime import datetime, timedelta
from decimal import Decimal
from pymongo import MongoClient
import os

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
client = MongoClient(MONGODB_URI)
db = client['real_estate']

class FlatOffersManager:
    def __init__(self):
        self.db = db
        self.offers_collection = self.db['flat_offers']
        self.cached_offers: Dict[str, dict] = {}
        self.last_access: Dict[str, float] = {}
        self.cache_duration = 600  # 10 minutes in seconds

    def get_offer(self, data_id: str) -> Optional[dict]:
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
        offer = self.offers_collection.find_one({'data-id': data_id})
        if offer:
            self.cached_offers[data_id] = offer
            self.last_access[data_id] = current_time
            return offer
        return None

    def save_offer(self, offer_data: dict):
        """Save or update a flat offer"""
        data_id = offer_data['data-id']
        current_time = time.time()

        # Ensure required fields
        offer_data['is_active'] = True
        if 'availability' not in offer_data:
            offer_data['availability'] = {
                'listed_at': datetime.utcnow()
            }

        # Update cache
        self.cached_offers[data_id] = offer_data
        self.last_access[data_id] = current_time

        # Update database
        self.offers_collection.update_one(
            {'data-id': data_id},
            {'$set': offer_data},
            upsert=True
        )

    def deactivate_offer(self, data_id: str):
        """Mark an offer as inactive"""
        offer = self.get_offer(data_id)
        if offer:
            offer['is_active'] = False
            self.offers_collection.update_one(
                {'data-id': data_id},
                {'$set': {'is_active': False}}
            )
            # Remove from cache
            if data_id in self.cached_offers:
                del self.cached_offers[data_id]
                del self.last_access[data_id]

    def delete_offer(self, data_id: str):
        """Permanently delete an offer"""
        # Remove from cache
        if data_id in self.cached_offers:
            del self.cached_offers[data_id]
            del self.last_access[data_id]

        # Remove from database
        self.offers_collection.delete_one({'data-id': data_id})

    def find_matching_offers(self, user_settings: dict) -> List[dict]:
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

    def get_active_offers_count(self) -> int:
        """Get count of active offers"""
        return self.offers_collection.count_documents({'is_active': True})

    def cleanup_old_offers(self, days: int = 30):
        """Deactivate offers older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Find and deactivate old offers
        old_offers = self.offers_collection.find({
            'is_active': True,
            'availability.listed_at': {'$lt': cutoff_date}
        })

        for offer in old_offers:
            self.deactivate_offer(offer['data-id'])

    def get_offers_by_price_range(self, min_price: float, max_price: float) -> List[dict]:
        """Get active offers within price range"""
        query = {
            'is_active': True,
            'costs.base_rent': {
                '$gte': Decimal(str(min_price)),
                '$lte': Decimal(str(max_price))
            }
        }

        return list(self.offers_collection.find(query))
