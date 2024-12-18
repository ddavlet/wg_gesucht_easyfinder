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

def get_details(offer: dict):
    url = offer['link']
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    response = requests.get(url, headers=headers)
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')
    print(soup)

def start_parser():
    print("Starting parser")
    try:
        url = 'https://www.wg-gesucht.de/1-zimmer-wohnungen-in-Muenchen.90.1.0.0.html'
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

        response = requests.get(url, headers=headers)
        html_content = response.text
        print("Got response")
        soup = BeautifulSoup(html_content, 'html.parser')
        print(soup.prettify())
        ads = soup.find_all(class_='listenansicht1 offer_list_item')
        print(f"Found {len(ads)} ads")
        if len(ads) == 0:
            print(soup.prettify())
            return
        for proposal in ads:
            try:
                data_id = proposal.get('data-id')
                adid = proposal.get('adid')
                link = f"https://www.wg-gesucht.de/{adid}" if adid else None
                if link:
                    base_url = "https://www.wg-gesucht.de"
                    ad_link = base_url + link['href']
                    offer_data = {
                        'data-id': data_id,
                        'link': ad_link,
                        'is_active': True
                    }
                    flat_offers_manager.save_offer(offer_data)
                    # get_details(offer_data)
                    # if flat_offers_manager.save_offer(offer_data):
                    #     get_details(offer_data)
                    # else:
                    #     print(f"Offer {data_id} already exists")
                    break
            except Exception as e:
                print(f"Error processing ad: {e}")
                continue
    except Exception as e:
        print(f"Parser main error: {e}")

# TODO: parse offer data

