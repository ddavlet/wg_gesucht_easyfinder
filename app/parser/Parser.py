from typing import Dict
from time import sleep
from DrissionPage import ChromiumPage
from database.flat_offers_manager import FlatOffersManager
from database.database import get_flat_offer_fields
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Parser:
    def __init__(self, driver: ChromiumPage, flat_offers_manager: FlatOffersManager, type: int):
        self.driver = driver
        self.flat_offers_manager = flat_offers_manager
        self.type_code = type
        switch = {
            0: "WG-Zimmer",
            1: "1-Zimmer-Wohnung",
            2: "Wohnung",
            3: "Haus"
        }
        self.unselect_list_option('dropdown-menu inner')
        self.type = switch[type]
        self.select_list_option('dropdown-menu inner', type)
        self.fill_input('form-control autocomplete wgg_input city_loader_bar', 'Munchen')
        self.driver.ele('tag:input@id:search_button').click()



    def fill_input(self, class_name: str, value: str):
        logging.info("Filling input: %s", class_name)
        form_element = self.driver.ele(f'tag:form@id:formPortal')
        form_element.ele(f'tag:input@class:{class_name}').input(value)
        logging.info("Input filled")
        sleep(0.01)
        self.driver.ele(f'tag:div@class:autocomplete-suggestion').click()
        logging.info("Suggestion clicked")
    def select_list_option(self, list_class_name: str, option_index: int):
        logging.info("Selecting option from list: %s", list_class_name)
        form_element = self.driver.ele(f'tag:form@id:formPortal')
        form_element.ele(f'tag:button@class:btn dropdown-toggle form-control wgg_select').click()
        list_element = form_element.ele(f'tag:ul@class:{list_class_name}')  # Locate the list
        logging.info("List element: %s", list_element)
        options = list_element.eles('tag:li')  # Get all list items
        logging.info("Options: %s", options)
        if 0 <= option_index < len(options):
            # Click the desired option
            logging.info("Option: %s", options[option_index].html)
            if options[option_index].attr('class') != 'selected':
                options[option_index].click()
                logging.info("Option clicked")
        else:
            logging.error("Option index out of range: %d", option_index)
        form_element.ele(f'tag:button@class:btn dropdown-toggle form-control wgg_select').click()
        sleep(1)

    def unselect_list_option(self, list_class_name: str):
        logging.info("Unselecting option from list: %s", list_class_name)
        form_element = self.driver.ele(f'tag:form@id:formPortal')
        form_element.ele(f'tag:button@class:btn dropdown-toggle form-control wgg_select').click()
        list_element = form_element.ele(f'tag:ul@class:{list_class_name}')  # Locate the list
        options = list_element.eles('tag:li')  # Get all list items
        for option in options:
            sleep(0.11)
            if option.attr('class') == 'selected':
                option.click()
                logging.info("Option unselected")
            else:
                logging.info("Option already unselected")
        form_element.ele(f'tag:button@class:btn dropdown-toggle form-control wgg_select').click()
        sleep(0.11)
        sleep(1)

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
        offer_fields['type'] = self.type
        offer_fields['data_id'] = id
        offer_fields['link'] = link
        offer_fields['is_active'] = True

        return offer_fields

    def get_offer_details(self, page, offer_data):
        sleep(3)
        data = offer_data
        logging.info('Fetching offer details...')
        main_column = page.ele('tag:div@id=main_column')
        row_main_column = main_column.ele('tag:div@class=row')

        # First row
        logging.info('First row')
        data['name'] = row_main_column.ele('tag:h1', timeout=3).text
        image_elements = row_main_column.eles('tag:img@class=sp-image')
        for image_element in image_elements:
            data['images'].append(image_element.attr('data-default'))

        section_footer_dark = row_main_column.ele('tag:div@class=section_footer_dark')
        data['area'] = section_footer_dark.ele('tag:b@text():m²').text
        data['total_rent'] = section_footer_dark.ele('tag:b@text():€').text

        row_main_column = row_main_column.next()

        # Second row
        logging.info('Second row')
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
            logging.error("Error getting costs: %s", e)
            logging.error("Error in: %s", row.html)
            raise e

        row_main_column = row_main_column.next()

        # Third row
        logging.info('Third row')
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
                    logging.error("Error getting availability: %s", e)
                    logging.error("Error in: %s", row.html)
                    logging.info("Continuing...")

        row_main_column = row_main_column.next().next()

        # Fifth row
        logging.info('Fifth row')
        try:
            row = row_main_column.ele('tag:div@class=row')
            details = row.eles('tag:div@class=text-center')
            for detail in details:
                data['object_details'].append(detail.text)
        except Exception as e:
            logging.error("Error getting object details: %s", e)
            logging.error("Error in: %s", row.html)
            raise e

        row_main_column = row_main_column.next().next()

        # Sixth row
        logging.info('Sixth row')
        row = row_main_column.ele('tag:div@class=row')
        descriptions = row.eles('tag:div@id:freitext_')
        for description in descriptions:
            data['description'].append(description.text)

        # Save offer
        self.flat_offers_manager.save_offer(data)
        logging.info("New offer saved, id: %s", data['data_id'])

    def parse_ads(self):
        for i in range(2):
            sleep(5)
            logging.info("Parsing page: %d", i)
            offers = self.driver.eles('@class:truncate_title noprint')
            logging.info("Offers received, number of offers on page: %d", len(offers))
            logging.info('--------------------------------')
            for offer in offers:
                offer = offer.ele('tag:a')
                logging.info("Offer clicked")
                new_tab = self.driver.new_tab(offer.attr('href'))
                sleep(5)
                try:
                    offer_data = self.get_ad_data(new_tab)
                    logging.info("Offer data received")
                    sleep(3)
                    if not self.flat_offers_manager.get_offer(offer_data['data_id']):
                        logging.info("Offer with id: %s does not exist", offer_data['data_id'])
                        try:
                            self.get_offer_details(new_tab, offer_data)
                            logging.info("Offer with id: %s created", offer_data['data_id'])
                        except Exception as e:
                            logging.error("Error getting offer details: %s", e)
                            logging.info("Skipping offer with id: %s", offer_data['data_id'])
                        sleep(3)
                    else:
                        logging.info("Offer with id: %s already exists", offer_data['data_id'])
                except Exception as e:
                    logging.error('Skipped: %s', e)
                logging.info("New tab closing")
                logging.info('--------------------------------')
                new_tab.close()

            logging.info(self.driver.url)
            self.driver.ele('tag:a@class:page-link next').click()
