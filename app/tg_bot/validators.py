from mapsapi import MapsAPI
from database.flat_offers_manager import FlatOffersManager
from database.finder_manager import FinderManager
import os
import json

maps_api = MapsAPI()

class Validators:

    def __init__(self, user_data):
        self.user_data = user_data

    async def validate_address(self, address: str):
        result, is_valid = await maps_api.validate_address(address)
        answer: str = ""
        if is_valid and result:
            self.user_data['preferences']['address'] = result['result']['address']['formattedAddress']
            self.user_data['preferences']['address_id'] = result['result']['geocode']['placeId']
            answer = result['result']['address']['formattedAddress']
            return answer, True
        elif not is_valid and result:
            answer = result['componentName']['text']
            return answer, False
        else:
            answer = "Address cannot be validated."
            return answer, False
