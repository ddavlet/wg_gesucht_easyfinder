import requests
import os
import logging
import dotenv

dotenv.load_dotenv()

logging.basicConfig(level=logging.INFO)
class TranslatorAPI:
    def __init__(self, target_language: str):
        self.api_key = os.getenv('TRANSLATOR_API_KEY')
        self.base_url = 'https://translation.googleapis.com/language/translate/v2'
        self.full_link = f'{self.base_url}?key={self.api_key}'
        self.target_language = target_language

    def translate(self, text: str):
        data = {
            "q": text,
            "target": self.target_language
        }
        response = requests.post(self.full_link, json=data)
        if response.status_code == 200:
            return response.json()['data']['translations'][0]['translatedText']
        else:
            return ""
