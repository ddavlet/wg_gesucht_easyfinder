from typing import Dict
from time import sleep
from DrissionPage import ChromiumPage
from database.flat_offers_manager import FlatOffersManager
from database.database import get_flat_offer_fields

class Parser:
    def __init__(self, driver: ChromiumPage, flat_offers_manager: FlatOffersManager):
        self.driver = driver
        self.flat_offers_manager = flat_offers_manager
        self.driver.ele('tag:input@id:search_button').click()

    def get_page(self, url):
        self.driver.get(url)
        return self.driver.soup

    def get_ads(self):
        ads = self.driver.ele('@class:listenansicht1 offer_list_item')
        return ads

    def get_ad_data(self, page: ChromiumPage):
        id = page.ele('tag:div@class:col-xs-12 col-md-6').text
        id = id.split(' ')[1]
        link = page.url
        offer_fields = get_flat_offer_fields()

        offer_fields['data-id'] = id
        offer_fields['link'] = link
        offer_fields['is_active'] = True

        return offer_fields

    def get_offer_details(self, page, offer_data):
        sleep(3)
        # print(self.driver)
        data = offer_data
        # print(new_tab.html)
        main_column = page.ele('tag:div@id=main_column')
        row_main_column = main_column.ele('tag:div@class=row')

        # First row
        print('First row')
        data['name'] = row_main_column.ele('tag:h1', timeout=3).text
        image_elements = row_main_column.eles('tag:img@class=sp-image')
        for image_element in image_elements:
            data['images'].append(image_element.attr('data-default'))

        section_footer_dark = row_main_column.ele('tag:div@class=section_footer_dark')
        data['area'] = section_footer_dark.ele('tag:b@text():m²').text
        data['costs']['rent'] = section_footer_dark.ele('tag:b@text():€').text


        row_main_column = row_main_column.next()

        # Second row
        print('Second row')
        try:
            row = row_main_column.ele('tag:div@class=row')
            rows = row.eles('tag:div@class=row')
            keys = ['rent', 'additional_costs', 'other_costs', 'deposit', 'transfer_agreement']
            count = 0
            for row, key in zip(rows, keys):
                value = row.ele('tag:span@class=section_panel_value').text
                data['costs'][key] = value
                count += 1
                if count == 5:
                    break
        except Exception as e:
            print("Error getting costs: ", e)
            print("Error in: ")
            print(row.html)
            raise e


        row_main_column = row_main_column.next()

        # Third row
        print('Third row')
        row = row_main_column.ele('tag:div@class=row')
        rows = row.eles('tag:div@class=row')
        data['address'] = rows[0].ele('tag:span@class=section_panel_detail').text
        rows.pop(0)
        for row in rows:
            try:
                name = row.ele('tag:span@class=section_panel_detail')
                data['availability'][name.text] = row.ele('tag:span@class=section_panel_value').text
            except Exception as e:
                try:
                    name = row.ele('tag:span@class=noprint section_panel_detail')
                    data['availability'][name.text] = row.ele('tag:b@class=noprint').text
                except Exception as e:
                    print("Error getting availability: ", e)
                    print("Error in: ")
                    print(row.html)
                    print("Continuing...")


        row_main_column = row_main_column.next().next()

        # Fifth row
        print('Fifth row')
        try:
            row = row_main_column.ele('tag:div@class=row')
            details = row.eles('tag:div@class=text-center')
            for detail in details:
                data['object_details'].append(detail.text)
        except Exception as e:
            print("Error getting object details: ", e)
            print("Error in: ")
            print(row.html)
            raise e


        row_main_column = row_main_column.next().next()

        # Sixth row
        print('Sixth row')
        # print(row_main_column.html)
        row = row_main_column.ele('tag:div@class=row')
        descriptions = row.eles('tag:div@id:freitext_')
        for description in descriptions:
            data['description'].append(description.text)

        # Save offer
        self.flat_offers_manager.save_offer(data)
        print("New offer saved, id: ", data['data-id'])

    def parse_ads(self):
        # ads = self.get_ads()
        for i in range(2):
            sleep(5)
            print("Parsing page: ", i)
            offers = self.driver.eles('@class:truncate_title noprint')
            print("offers received, number of offers on page: ", len(offers))
            print('--------------------------------')
            for offer in offers:
                offer = offer.ele('tag:a')
                print("offer clicked")
                new_tab = self.driver.new_tab(offer.attr('href'))
                sleep(5)
                try:
                    offer_data = self.get_ad_data(new_tab)
                    print("offer_data_received")
                    sleep(3)
                    if not self.flat_offers_manager.get_offer(offer_data['data-id']):
                        print("Offer with id: ", offer_data['data-id'], " does not exist")
                        try:
                            self.get_offer_details(new_tab, offer_data)
                            print("Offer with id: ", offer_data['data-id'], " created")
                        except Exception as e:
                            print("Error getting offer details: ", e)
                            print("Skipping offer with id: ", offer_data['data-id'])
                        sleep(3)
                    else:
                        print("Offer with id: ", offer_data['data-id'], " already exists")
                except Exception as e:
                    print('skipped')
                    print(e)
                    raise e
                print("new_tab closing")
                print('--------------------------------')
                new_tab.close()

            print(self.driver.url)
            self.driver.ele('tag:a@class:page-link next').click()
        # print(element)
