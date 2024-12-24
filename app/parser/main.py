from time import sleep
from DrissionPage import ChromiumPage
from database.flat_offers_manager import FlatOffersManager
from Parser import Parser

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
        driver = ChromiumPage()
        print("driver set")
        driver.get(base_url)
        sleep(5)
        parser = Parser(driver, flat_offers_manager)
        print("parser set")
        print("Got response")
        parser.parse_ads()

        driver.quit()
    except Exception as e:
        print(f"Parser main error: {e}")

if __name__ == "__main__":
    start_parser()

