from time import sleep
import logging
from DrissionPage import ChromiumPage, ChromiumOptions
from database.flat_offers_manager import FlatOffersManager
from Parser import Parser
import dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('parser.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

dotenv.load_dotenv()
logger.info("Environment variables loaded")

# Connect to MongoDB
# MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://mongodb:27017')
# client = MongoClient(MONGODB_URI)
# db = client[os.getenv('MONGO_DB_NAME', 'app_db')]

flat_offers_manager = FlatOffersManager()
logger.info("FlatOffersManager initialized")

def get_options():
    logger.debug("Configuring ChromiumOptions")
    options = ChromiumOptions()
    options.headless()
    options.set_argument('--no-sandbox')
    options.set_argument('--headless=new')
    options.set_argument('--disable-backgrounding-occluded-windows')
    # options.set_argument('--disable-dev-shm-usage')
    logger.debug("ChromiumOptions configured with headless mode and no-sandbox")
    return options

def start_parser(type: int, city: int):
    logger.info("Starting parser process")
    try:
        base_url = 'https://www.wg-gesucht.de'
        logger.info(f"Initializing ChromiumPage with base URL: {base_url}")

        driver = ChromiumPage()
        logger.info("ChromiumPage driver initialized successfully")

        driver.get(base_url)
        logger.info(f"Navigated to base URL: {base_url}")

        sleep(1)
        logger.debug("Waited 1 second for page load")

        logger.info("Initializing Parser for WG-Zimmer (type 0)")

        # types: 0 - WG-Zimmer, 1 - 1-Zimmer-Wohnung, 2 - Wohnung, 3 - Haus
        # cities: 0 - München, 1 - Berlin
        parser = Parser(driver, flat_offers_manager, type, city)
        logger.info("Parser initialized successfully")

        try:
            logger.info("Starting to parse advertisements")
            parser.parse_ads()
            logger.info("Advertisement parsing completed successfully")
        except Exception as e:
            logger.error(f"Error during parsing advertisements: {str(e)}", exc_info=True)
            raise

        logger.info("Closing ChromiumPage driver")
        driver.quit()
        logger.info("Parser process completed successfully")

    except Exception as e:
        logger.error(f"Critical error in parser main process: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    try:
        user_input = int(input("Enter the type of offer to parse (0 for WG-Zimmer, 1 for 1-room-Wohnung, 2 for Wohnung, 3 for Haus, 4 for all): "))
        city = int(input("Enter the city to parse (0 for München, 1 for Berlin): "))
        if user_input == 4:
            for i in range(4):
                start_parser(i, city)
        else:
            start_parser(user_input, city)
    except Exception as e:
        logger.critical("Parser failed to complete", exc_info=True)
        raise

