from mapsapi import MapsAPI
import os
import json

maps_api = MapsAPI()

class Validators:

    def __init__(self, user_data, texts):
        self.user_data = user_data
        self.texts = texts

    def validate_address(self, address: str):
        result, is_valid = maps_api.validate_address(address)
        answer: str = ""
        if is_valid and result:
            self.user_data['preferences']['address'] = result['result']['address']['formattedAddress']
            self.user_data['preferences']['address_id'] = result['result']['geocode']['placeId']
            answer = self.texts['settings']['address_set']['title'] + \
                result['result']['address']['formattedAddress'] + \
                self.texts['settings']['address_set']['commands']
        elif not is_valid and result:
            answer = self.texts['errors']['invalid_address']['title'] + \
                result['componentName']['text'] + \
                self.texts['settings']['address_set']['commands']
        else:
            answer = self.texts['errors']['wrong_address']
        return answer
