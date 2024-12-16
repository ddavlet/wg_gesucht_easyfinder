import requests
# import os
from bs4 import BeautifulSoup
from database.flat_offers_manager import FlatOffersManager
from pymongo import MongoClient

# Connect to MongoDB
# MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://mongodb:27017')
# client = MongoClient(MONGODB_URI)
# db = client[os.getenv('MONGO_DB_NAME', 'app_db')]

flat_offers_manager = FlatOffersManager()

def start_parser():
    print("Starting parser")
    try:
        url = 'https://www.wg-gesucht.de/1-zimmer-wohnungen-in-Muenchen.90.1.1.0.html'
        response = requests.get(url)
        html_content = response.text
        print("Got response")
        soup = BeautifulSoup(html_content, 'html.parser')
        ads = soup.find_all(class_='wgg_card offer_list_item')
        print(f"Found {len(ads)} ads")

        for proposal in ads:
            try:
                data_id = proposal.get('data-id')
                link = proposal.find('a', href=True)
                if link:
                    base_url = "https://www.wg-gesucht.de"
                    ad_link = base_url + link['href']
                    offer_data = {
                        'data-id': data_id,
                        'link': ad_link,
                        'is_active': True
                    }
                    flat_offers_manager.save_offer(offer_data)
            except Exception as e:
                print(f"Error processing ad: {e}")
                continue

# TODO: parse offer data

    except Exception as e:
        print(f"Parser main error: {e}")
