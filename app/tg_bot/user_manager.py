from typing import Dict, Optional
import time
from pymongo import MongoClient
import os

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
client = MongoClient(MONGODB_URI)
db = client[os.getenv('MONGO_DB_NAME', 'app_db')]

class UserManager:
    def __init__(self):
        self.db = db
        self.users_collection = self.db['users']
        self.cached_users: Dict[int, dict] = {}
        self.last_access: Dict[int, float] = {}
        self.cache_duration = 600  # 10 minutes in seconds

    def get_user(self, chat_id: int) -> dict:
        current_time = time.time()

        # Check if user is in cache and still fresh
        if chat_id in self.cached_users:
            if current_time - self.last_access[chat_id] < self.cache_duration:
                self.last_access[chat_id] = current_time
                return self.cached_users[chat_id]
            else:
                # Remove expired cache
                del self.cached_users[chat_id]
                del self.last_access[chat_id]

        # Get from database
        user = self.users_collection.find_one({'chat_id': chat_id})
        if user:
            self.cached_users[chat_id] = user
            self.last_access[chat_id] = current_time
            return user
        return None

    def save_user(self, chat_id: int, user_data: dict):
        current_time = time.time()

        # Ensure active status is set
        user_data['is_active'] = True

        # Update cache
        self.cached_users[chat_id] = user_data
        self.last_access[chat_id] = current_time

        # Update database
        self.users_collection.update_one(
            {'chat_id': chat_id},
            {'$set': user_data},
            upsert=True
        )

    def deactivate_user(self, chat_id: int):
        user_data = self.get_user(chat_id)
        if user_data:
            user_data['is_active'] = False
            self.users_collection.update_one(
                {'chat_id': chat_id},
                {'$set': {'is_active': False}}
            )
            # Remove from cache
            if chat_id in self.cached_users:
                del self.cached_users[chat_id]
                del self.last_access[chat_id]

    def delete_user(self, chat_id: int):
        # Remove from cache
        if chat_id in self.cached_users:
            del self.cached_users[chat_id]
            del self.last_access[chat_id]

        # Remove from database
        self.users_collection.delete_one({'chat_id': chat_id})
