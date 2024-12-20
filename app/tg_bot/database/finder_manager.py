from typing import Dict, Optional, List
import time
import random
from pymongo import MongoClient
from database.database import create_database, validate_finder_data

db = create_database()

if db is None:
    print("Database not initialized")
    exit(1)

class FinderManager:
    def __init__(self):
        self.db = db
        self.finders_collection = self.db['finders']
        self.cached_findings: Dict[int, dict] = {}
        self.last_access: Dict[int, float] = {}
        self.cache_duration = 600  # 10 minutes in seconds
        self.life_duration = 30*24*60*60  # 30 days in seconds

    def get_finder(self, finder_id: int) -> Optional[dict]:
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
            self.cached_findings[finder_id] = finder
            self.last_access[finder_id] = current_time
            return finder
        return None

    def get_findings_by_user(self, user_id: int) -> List[dict]:
        """Get all finders for a specific user"""
        return list(self.finders_collection.find({'user_id': user_id}))

    def save_finder(self, user_id: int, finder_id: int, finder_data: dict):
        current_time = time.time()
        if not validate_finder_data(finder_data):
            print("Invalid finder data")
            return
        # Ensure active status is set
        finder_data['finder_id'] = finder_id
        finder_data['is_active'] = True
        finder_data['user_id'] = user_id  # Associate finder with user

        # Update cache
        self.cached_findings[finder_id] = finder_data
        self.last_access[finder_id] = current_time

        # Update database
        self.finders_collection.update_one(
            {'finder_id': finder_id},
            {'$set': finder_data},
            upsert=True
        )

    def deactivate_finder(self, finder_id: int):
        finder_data = self.get_finder(finder_id)
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

    def delete_finder(self, finder_id: int):
        # Remove from cache
        if finder_id in self.cached_findings:
            del self.cached_findings[finder_id]
            del self.last_access[finder_id]

        # Remove from database
        self.finders_collection.delete_one({'finder_id': finder_id})

    def generate_finder_id(self) -> int:
        return random.randint(100000, 999999)

    def clean_expired_cache(self):
        current_time = time.time()
        expired_finders = [finder_id for finder_id, last_access in self.last_access.items()
                         if current_time - last_access >= self.life_duration]

        for finder_id in expired_finders:
            del self.cached_findings[finder_id]
            del self.last_access[finder_id]
