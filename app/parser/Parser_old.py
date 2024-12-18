from typing import Dict, Any
from time import sleep
from DrissionPage import ChromiumPage
from database.flat_offers_manager import FlatOffersManager

class Parser:
    def __init__(self, driver: ChromiumPage, flat_offers_manager: FlatOffersManager):
        self.driver = driver
        self.flat_offers_manager = flat_offers_manager

    def get_page(self, url):
        self.driver.get(url)
        return self.driver.soup

    def get_ads(self):
        ads = self.driver.ele('@class:listenansicht1 offer_list_item')
        return ads

    def get_ad_data(self, offers):
        data_id = offers.attr('data-id')
        adid = offers.attr('adid')
        link = f"https://www.wg-gesucht.de/{adid}" if adid else None
        offer_data = {
            'data-id': data_id,
            'link': link,
            'is_active': True
        }
        return offer_data

    def get_offer_details(self, offer_data):
        sleep(2)
        new_tab = self.driver.new_tab(offer_data['link'])
        # print(self.driver)
        data: Dict[str, str] = {}
        sleep(2)
        # print(new_tab.html)
        data['name'] = new_tab.ele('tag:h1', timeout=3).text
        print(data['name'])
        # Unique identifier for the offer (can be derived from URL or other unique page elements)
        section_footer_dark = new_tab.ele('tag:div@class:section_footer_dark', timeout=3)
        print(section_footer_dark.html)
        if section_footer_dark:
            data['area'] = section_footer_dark.ele('tag:b@text:m²')
            data['costs'] = {}
            data['costs']['rent'] = section_footer_dark.ele('tag:b@text:€')
        else:
            data['area'] = None

        self.flat_offers_manager.update_offer_data(offer_data['data-id'], data)

    def parse_ads(self):
        # ads = self.get_ads()
        for i in range(10):
            sleep(5)
            offers = self.driver.eles('@class:listenansicht1 offer_list_item')
            print("offers")
            for offer in offers:
                offer_data = self.get_ad_data(offer)
                print("offer_data")
                if self.flat_offers_manager.save_offer(offer_data):
                    print("offer_data saved")
                    self.get_offer_details(offer_data)
                    return
            self.driver.ele('tag:a@class:page-link next').click()
        # print(element)
