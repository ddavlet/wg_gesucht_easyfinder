from typing import Dict
from database.flat_offers_manager import FlatOffersManager
import logging
import dotenv
import asyncio

dotenv.load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def clean_database():
    """Delete all offers that do not have offer_type_id field"""
    flat_offers_manager = FlatOffersManager()
    offers = await flat_offers_manager.get_all_offers()

    deleted_count = 0
    for offer in offers:
        if 'offer_type_id' not in offer:
            await flat_offers_manager.delete_offer(offer['data_id'])
            deleted_count += 1
            logging.info(f"Deleted offer {offer['data_id']} - missing offer_type_id")

    logging.info(f"Cleaned database - removed {deleted_count} offers without offer_type_id")

if __name__ == "__main__":
    asyncio.run(clean_database())
