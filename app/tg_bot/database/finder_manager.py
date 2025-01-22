from typing import Dict, Optional, List
import time
import random
from database.database import create_database, validate_finder_data
from mapsapi import maps_api
from database.flat_offers_manager import FlatOffersManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

db = create_database()

if db is None:
    print("Database not initialized")
    exit(1)

class FinderManager:
    def __init__(self, flat_offers_manager: FlatOffersManager):
        self.db = db
        self.finders_collection = self.db['finders']
        self.cached_findings: Dict[int, dict] = {}
        self.last_access: Dict[int, float] = {}
        self.cache_duration = 600  # 10 minutes in seconds
        self.life_duration = 30*24*60*60  # 30 days in seconds
        self.flat_offers_manager = flat_offers_manager
        logging.info("FinderManager initialized")

    async def get_finder(self, finder_id: int) -> Optional[dict]:
        current_time = time.time()

        # Check if finder is in cache and still fresh
        if finder_id in self.cached_findings:
            if current_time - self.last_access[finder_id] < self.cache_duration:
                self.last_access[finder_id] = current_time
                return self.cached_findings[finder_id]
            else:
                # Remove expired cache
                del self.cached_findings[finder_id]
                del self.last_access[finder_id]

        # Get from database
        finder = self.finders_collection.find_one({'finder_id': finder_id})
        if finder:
            logging.info(f"Finder found: {finder}")
            self.cached_findings[finder_id] = finder
            self.last_access[finder_id] = current_time
            return finder
        else:
            logging.warning(f"Finder with ID {finder_id} not found")
        return None

    async def save_finder(self, user_id: int, finder_id: int, finder_data: dict):
        current_time = time.time()
        if not validate_finder_data(finder_data):
            print("Invalid finder data")
            return
        # Ensure active status is set
        finder_data['finder_id'] = finder_id
        finder_data['is_active'] = True
        finder_data['user_id'] = user_id  # Associate finder with user
        finder_data['created_at'] = current_time
        # Update cache
        self.cached_findings[finder_id] = finder_data
        self.last_access[finder_id] = current_time

        # Update database
        self.finders_collection.update_one(
            {'finder_id': finder_id},
            {'$set': finder_data},
            upsert=True
        )
        logging.info(f"Saving finder with ID: {finder_id} for user ID: {user_id}")

    async def deactivate_finder(self, finder_id: int):
        finder_data = await self.get_finder(finder_id)
        if finder_data:
            finder_data['is_active'] = False
            self.finders_collection.update_one(
                {'finder_id': finder_id},
                {'$set': {'is_active': False}}
            )
            # Remove from cache
            if finder_id in self.cached_findings:
                del self.cached_findings[finder_id]
                del self.last_access[finder_id]
            logging.info(f"Deactivating finder with ID: {finder_id}")

    async def delete_finder(self, finder_id: int):
        # Remove from cache
        if finder_id in self.cached_findings:
            del self.cached_findings[finder_id]
            del self.last_access[finder_id]

        # Remove from database
        self.finders_collection.delete_one({'finder_id': finder_id})
        logging.info(f"Deleting finder with ID: {finder_id}")

    async def update_finder(self, finder_id: int, finder_data: dict):
        self.finders_collection.update_one(
            {'finder_id': finder_id},
            {'$set': finder_data}
        )
        logging.info(f"Updating finder with ID: {finder_id}")

    async def generate_finder_id(self) -> int:
        return random.randint(100000, 999999)

    async def clean_expired_cache(self):
        current_time = time.time()
        expired_finders = [finder_id for finder_id, last_access in self.last_access.items()
                         if current_time - last_access >= self.life_duration]

        for finder_id in expired_finders:
            del self.cached_findings[finder_id]
            del self.last_access[finder_id]
        logging.info("Cleaning expired cache")

    async def delete_expired_finders(self):
        current_time = time.time()
        expired_finders = [finder_id for finder_id, last_access in self.last_access.items()
                         if current_time - last_access >= self.life_duration]
        for finder_id in expired_finders:
            await self.delete_finder(finder_id)
        logging.info("Deleting expired finders")

    async def get_finders_by_user(self, user_id: int) -> List[dict]:
        logging.info(f"Fetching finders for user ID: {user_id}")
        return list(self.finders_collection.find({'user_id': user_id}))

    async def get_offers_by_finder(self, finder_id: int) -> List[dict]:
        finder = await self.get_finder(finder_id)
        if finder:
            return finder['offers']
        logging.info(f"Fetching offers for finder ID: {finder_id}")
        return []

    async def get_findings_by_user(self, user_id: int) -> List[int]:
        finders = await self.get_finders_by_user(user_id)
        findings: List[str] = []
        findings.clear()
        for finder in finders:
            findings.extend(finder['offers'])
        logging.info(f"Fetching findings for user ID: {user_id}")
        return findings

    async def set_offer_to_finder(self, finder_id: int, offer_id: str):
        await self.finders_collection.update_one(
            {'finder_id': finder_id},
            {'$push': {'offers': offer_id}}
        )
        logging.info(f"Setting offer ID: {offer_id} to finder ID: {finder_id}")

    async def delete_offer_from_finder(self, finder_id: int, offer_id: str):
        await self.finders_collection.update_one(
            {'finder_id': finder_id},
            {'$pull': {'offers': offer_id}}
        )
        logging.info(f"Deleting offer ID: {offer_id} from finder ID: {finder_id}")

    async def find_offers(self, finder: dict, address: str) -> None:
        finder_id = finder['finder_id']
        duration = finder['duration']
        offers = await self.flat_offers_manager.get_active_offers()
        for offer in offers:
            if offer['data_id'] in finder['parsed_offers']:
                logging.info("Offer already parsed")
                continue
            distance = await maps_api.directions(offer['address'], address, finder['type'])
            if distance is None:
                logging.warning("Distance is None, skipping offer")
                continue
            logging.info("Distance information retrieved")
            finder['parsed_offers'].append(offer['data_id'])
            self.update_finder(finder_id, finder)
            if distance['routes'][0]['legs'][0]['distance']['value'] < int(duration) and offer['offer_type_id'] == finder['offer_type_id']:
                finder['offers'].append(offer['data_id'])
                self.update_finder(finder_id, finder)
                logging.info(f"Offer added for: {duration}, offer ID: {offer['data_id']}")
                logging.info(f"Because duration is: {distance['routes'][0]['legs'][0]['duration']['value']}")
            else:
                logging.info(f"Offer not added due to duration or type: {offer['data_id']}")
                continue
            logging.info("____________________")
        await self.update_finder(finder_id, finder)
        logging.info(f"Finding offers for finder ID: {finder_id} at address: {address}")

    async def delete_incomplete_finders(self):
        finders = self.finders_collection.find({'is_active': True, 'duration': -1})
        for finder in finders:
            await self.delete_finder(finder['finder_id'])
