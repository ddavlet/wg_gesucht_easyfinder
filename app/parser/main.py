from time import sleep
from DrissionPage import ChromiumPage
from database.flat_offers_manager import FlatOffersManager
from pymongo import MongoClient
from parser.Parser import Parser

# Connect to MongoDB
# MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://mongodb:27017')
# client = MongoClient(MONGODB_URI)
# db = client[os.getenv('MONGO_DB_NAME', 'app_db')]

flat_offers_manager = FlatOffersManager()

def get_details(offer: dict):
    url = offer['link']
    page = ChromiumPage()
    page.get(url)
    html_content = page.html
    print(page.soup)

def start_parser():
    print("Starting parser")
    try:
        base_url = 'https://www.wg-gesucht.de'
        # url = 'https://www.wg-gesucht.de/1-zimmer-wohnungen-in-Muenchen.90.1.1.1.html'
        driver = ChromiumPage()
        # base = ChromiumPage()
        print("driver set")
        driver.get(base_url)
        sleep(5)
        parser = Parser(driver, flat_offers_manager)
        print("parser set")
        # base.get(base_url)
        # sleep(5)
        print("Got response")
        parser.parse_ads()



        # for proposal in ads:
        #     try:
        #         data_id = proposal.get('data-id')
        #         adid = proposal.get('adid')
        #         link = f"https://www.wg-gesucht.de/{adid}" if adid else None
        #         if link:
        #             base_url = "https://www.wg-gesucht.de"
        #             ad_link = base_url + link
        #             offer_data = {
        #                 'data-id': data_id,
        #                 'link': ad_link,
        #                 'is_active': True
        #             }
        #             flat_offers_manager.save_offer(offer_data)
        #             # get_details(offer_data)
        #             # if flat_offers_manager.save_offer(offer_data):
        #             #     get_details(offer_data)
        #             # else:
        #             #     print(f"Offer {data_id} already exists")
        #             break
        #     except Exception as e:
        #         print(f"Error processing ad: {e}")
        #         continue
        # driver.quit()
    except Exception as e:
        print(f"Parser main error: {e}")

# TODO: parse offer data

