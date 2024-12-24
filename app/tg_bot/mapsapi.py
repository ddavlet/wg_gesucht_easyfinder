from datetime import datetime
import requests
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MapsAPI:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        self.base_link = 'https://addressvalidation.googleapis.com/v1:validateAddress?key='
        self.full_link = self.base_link + self.api_key
        logging.info("MapsAPI initialized with API key.")

    async def validate_address(self, address: str):
        logging.info(f"Validating address: {address}")
        address_data = {
            "address": {
                "regionCode": "DE",
                "locality": "Munich",
                "addressLines": [address]
            }
        }
        addressvalidation_result = requests.post(self.full_link, json=address_data)
        if addressvalidation_result.status_code == 200:
            result = addressvalidation_result.json()
            to_check = result['result']['address']['addressComponents']
            for component in to_check:
                if component['confirmationLevel'] != 'CONFIRMED':
                    logging.warning(f"Address component not confirmed: {component}")
                    return component, False
            logging.info("Address validation successful.")
            return result, True
        else:
            logging.error(f"Address validation failed with status code: {addressvalidation_result.status_code}")
            return None, False

    async def directions(self, origin: str, dest: str, mode: str = 'transit'):
        logging.info(f"Fetching directions from {origin} to {dest} with mode {mode}.")
        query = f"?origin={origin}&destination={dest}&mode={mode}&key={self.api_key}"
        directions_result = requests.get(f'https://maps.googleapis.com/maps/api/directions/json{query}')
        if directions_result.status_code == 200:
            logging.info("Directions fetched successfully.")
            return directions_result.json()
        else:
            logging.error(f"Failed to fetch directions with status code: {directions_result.status_code}")
            return None

maps_api = MapsAPI()

# # Test validation
# result, is_valid = maps_api.validate_address('Ludwigshöher 42 81479')
# if is_valid and result:
#     print(json.dumps(result, indent=4))
#     print(is_valid)
# elif not is_valid and result:
#     print("This block is not valid", result['componentName']['text'])
# elif not result:
#     print('Error')

# # Test directions
# orig_id = result['result']['geocode']['placeId']


# result, is_valid = maps_api.directions(orig_id, 'Heidemannstraße 220, 80939')
# if is_valid and result:
#     print(json.dumps(result, indent=4))
#     print(is_valid)
# elif not is_valid and result:
#     print("This block is not valid", result)
#     print(is_valid)
# else:
#     print('Error')
