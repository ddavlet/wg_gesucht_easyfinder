from datetime import datetime
import requests
import os
import json

class MapsAPI:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        self.base_link = 'https://addressvalidation.googleapis.com/v1:validateAddress?key='
        self.full_link = self.base_link + self.api_key

    def validate_address(self, address: str):
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
                    return component, False
            return result, True
        else:
            return None, False


    def directions(self, origin_id: str, dest):
        dest, result_destination = self.validate_address(dest)
        if not result_destination:
            return dest, False
        destination_id = dest['result']['geocode']['placeId']
        query = f"?origin=place_id:{origin_id}&destination=place_id:{destination_id}&mode=transit&key={self.api_key}"
        directions_result = requests.get(f'https://maps.googleapis.com/maps/api/directions/json{query}')
        if directions_result.status_code == 200:
            return directions_result.json(), True
        else:
            return None, False


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
