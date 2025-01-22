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
        logging.info(f"Initializing Parser for type: {switch[type]} (code: {type})")
        self.accept_cookies()
        self.unselect_list_option('dropdown-menu inner')
        self.type = switch[type]
        self.offer_type_id = type
        self.select_list_option('dropdown-menu inner', type)
        self.fill_input('form-control autocomplete wgg_input city_loader_bar', 'Munchen')
        logging.info("Clicking search button")
        self.driver.ele('tag:input@id:search_button').click()

    def accept_cookies(self):
        try:
            logging.info("Accepting cookies")
            box = self.driver.ele('tag:div@class=cmpbox cmpstyleroot cmpbox3 cmpboxWelcomeGDPR cmpBoxWelcomeOI')
            box = box.ele('tag:div@class=cmpboxbtns')
            box.ele('tag:a@role:button').click()
            logging.info("Cookies consent box accepted")
            sleep(1)
        except Exception as e:
            logging.info(f"No cookies consent box found: {e}")

    def fill_input(self, class_name: str, value: str):
        logging.info(f"Filling input field '{class_name}' with value: {value}")
        form_element = self.driver.ele(f'tag:form@id:formPortal')
        form_element.ele(f'tag:input@class:{class_name}').input(value)
        logging.debug(f"Input field '{class_name}' filled successfully")
        sleep(0.01)
        logging.info("Selecting autocomplete suggestion")
        self.driver.ele(f'tag:div@class:autocomplete-suggestion').click()
        logging.debug("Autocomplete suggestion selected successfully")

    def select_list_option(self, list_class_name: str, option_index: int):
        logging.info(f"Selecting option {option_index} from dropdown list '{list_class_name}'")
        form_element = self.driver.ele(f'tag:form@id:formPortal')
        logging.debug("Opening dropdown menu")
        form_element.ele(f'tag:button@class:btn dropdown-toggle form-control wgg_select').click()
        list_element = form_element.ele(f'tag:ul@class:{list_class_name}')
        options = list_element.eles('tag:li')
        logging.debug(f"Found {len(options)} options in dropdown")

        if 0 <= option_index < len(options):
            option_text = options[option_index].html
            logging.info(f"Selecting option: {option_text}")
            if options[option_index].attr('class') != 'selected':
                options[option_index].click()
                logging.debug(f"Option {option_index} selected successfully")
            else:
                logging.debug(f"Option {option_index} was already selected")
        else:
            logging.error(f"Invalid option index: {option_index}. Available options: 0-{len(options)-1}")

        form_element.ele(f'tag:button@class:btn dropdown-toggle form-control wgg_select').click()
        sleep(1)

    def unselect_list_option(self, list_class_name: str):
        logging.info(f"Unselecting all options from list '{list_class_name}'")
        form_element = self.driver.ele(f'tag:form@id:formPortal')
        form_element.ele(f'tag:button@class:btn dropdown-toggle form-control wgg_select').click()
        list_element = form_element.ele(f'tag:ul@class:{list_class_name}')
        options = list_element.eles('tag:li')
        logging.debug(f"Found {len(options)} options to check for unselection")

        unselected_count = 0
        for i, option in enumerate(options):
            sleep(0.11)
            if option.attr('class') == 'selected':
                option.click()
                unselected_count += 1
                logging.debug(f"Unselected option {i}")

        logging.info(f"Unselected {unselected_count} options in total")
        form_element.ele(f'tag:button@class:btn dropdown-toggle form-control wgg_select').click()
        sleep(1.11)

    def get_page(self, url):
        logging.info(f"Navigating to URL: {url}")
        self.driver.get(url)
        return self.driver.soup

    def get_ads(self):
        logging.info("Fetching advertisement listings")
        ads = self.driver.ele('@class:listenansicht1 offer_list_item')
        logging.debug(f"Found {len(ads) if ads else 0} advertisements")
        return ads

    def get_ad_data(self, page: ChromiumPage):
        logging.info(f"Extracting basic data from advertisement at URL: {page.url}")
        id = page.ele('tag:div@class:col-xs-12 col-md-6').text
        id = id.split(' ')[1]
        link = page.url
        offer_fields = get_flat_offer_fields()
        offer_fields['type'] = self.type
        offer_fields['data_id'] = id
        offer_fields['link'] = link
        offer_fields['is_active'] = True
        logging.debug(f"Extracted ad data - ID: {id}, Type: {self.type}")
        return offer_fields

    def get_offer_details(self, page, offer_data):
        logging.info(f"Fetching detailed offer information for ID: {offer_data['data_id']}")
        sleep(3)
        data = offer_data

        main_column = page.ele('tag:div@id=main_column')
        row_main_column = main_column.ele('tag:div@class=row')

        # First row
        logging.info('Processing offer title and images')
        data['name'] = row_main_column.ele('tag:h1', timeout=3).text
        image_elements = row_main_column.eles('tag:img@class=sp-image')
        data['images'] = [image.attr('data-default') for image in image_elements]
        logging.debug(f"Found {len(data['images'])} images")

        section_footer_dark = row_main_column.ele('tag:div@class=section_footer_dark')
        data['area'] = section_footer_dark.ele('tag:b@text():m²').text
        data['total_rent'] = section_footer_dark.ele('tag:b@text():€').text
        logging.debug(f"Basic details - Area: {data['area']}, Total Rent: {data['total_rent']}")

        row_main_column = row_main_column.next()

        # Second row
        logging.info('Processing cost information')
        try:
            row = row_main_column.ele('tag:div@class=row')
            rows = row.eles('tag:div@class=row')
            keys = ['rent', 'additional_costs', 'other_costs', 'deposit', 'transfer_agreement']
            count = 0
            for row, key in zip(rows, keys):
                value = row.ele('tag:span@class=section_panel_value').text
                data['costs'][key] = value
                logging.debug(f"Cost detail - {key}: {value}")
                count += 1
                if count == 5:
                    break
        except Exception as e:
            logging.error(f"Failed to extract cost information: {str(e)}")
            logging.error(f"Problematic HTML: {row.html}")
            raise e

        row_main_column = row_main_column.next()

        # Third row
        logging.info('Processing address and availability information')
        row = row_main_column.ele('tag:div@class=row')
        rows = row.eles('tag:div@class=row')
        data['address'] = rows[0].ele('tag:span@class=section_panel_detail').text
        logging.debug(f"Address: {data['address']}")
        rows.pop(0)
        for row in rows:
            try:
                name = row.ele('tag:span@class=section_panel_detail')
                data['availability'][name.text] = row.ele('tag:span@class=section_panel_value').text
                logging.debug(f"Availability detail - {name.text}: {data['availability'][name.text]}")
            except Exception as e:
                try:
                    name = row.ele('tag:span@class=noprint section_panel_detail')
                    data['availability'][name.text] = row.ele('tag:b@class=noprint').text
                    logging.debug(f"Availability detail (alternate) - {name.text}: {data['availability'][name.text]}")
                except Exception as e:
                    logging.warning(f"Failed to extract availability information: {str(e)}")
                    logging.debug(f"Skipped problematic row: {row.html}")

        row_main_column = row_main_column.next().next()

        # Fifth row
        logging.info('Processing object details')
        try:
            row = row_main_column.ele('tag:div@class=row')
            details = row.eles('tag:div@class=text-center')
            data['object_details'] = [detail.text for detail in details]
            logging.debug(f"Found {len(data['object_details'])} object details")
        except Exception as e:
            logging.error(f"Failed to extract object details: {str(e)}")
            logging.error(f"Problematic HTML: {row.html}")
            raise e

        row_main_column = row_main_column.next().next()

        # Sixth row
        logging.info('Processing description')
        row = row_main_column.ele('tag:div@class=row')
        descriptions = row.eles('tag:div@id:freitext_')
        data['description'] = [desc.text for desc in descriptions]
        logging.debug(f"Found {len(data['description'])} description sections")

        # Save offer
        logging.info(f"Saving offer with ID: {data['data_id']}")
        self.flat_offers_manager.save_offer(data)
        logging.info(f"Successfully saved offer {data['data_id']} - {data['name']}")

    def parse_ads(self):
        for i in range(2):
            logging.info(f"Processing page {i+1} of listings")
            sleep(5)
            offers = self.driver.eles('@class:truncate_title noprint')
            logging.info(f"Found {len(offers)} offers on page {i+1}")

            for j, offer in enumerate(offers, 1):
                offer = offer.ele('tag:a')
                offer_url = offer.attr('href')
                logging.info(f"Processing offer {j}/{len(offers)} on page {i+1}")
                logging.debug(f"Opening offer URL: {offer_url}")

                new_tab = self.driver.new_tab(offer_url)
                sleep(5)
                try:
                    offer_data = self.get_ad_data(new_tab)
                    sleep(3)

                    if not self.flat_offers_manager.get_offer(offer_data['data_id']):
                        logging.info(f"Processing new offer with ID: {offer_data['data_id']}")
                        try:
                            self.get_offer_details(new_tab, offer_data)
                            logging.info(f"Successfully processed offer {offer_data['data_id']}")
                        except Exception as e:
                            logging.error(f"Failed to process offer {offer_data['data_id']}: {str(e)}")
                        sleep(3)
                    else:
                        logging.info(f"Skipping existing offer with ID: {offer_data['data_id']}")
                except Exception as e:
                    logging.error(f"Failed to extract offer data: {str(e)}")

                logging.debug("Closing offer tab")
                new_tab.close()
                logging.info("------------------------")

            logging.info(f"Completed page {i+1}, current URL: {self.driver.url}")
            logging.info("Navigating to next page")
            self.driver.ele('tag:a@class:page-link next').click()
