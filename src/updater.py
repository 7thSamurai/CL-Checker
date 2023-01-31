from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from subprocess import CREATE_NO_WINDOW

from bs4 import BeautifulSoup
import chromedriver_autoinstaller

from config import config
from db import DB, Product

from PyQt5.QtCore import *
import logging, time, re

class Updater(QThread):
    """
    Threaded Craigslist web-scraper and updater
    """

    def __init__(self):
        super().__init__()

        self.driver = None

        self.total_products = {}
        self.status = 'ok'
        self.query_statuses = {}

    def quit(self):
        # Clean up
        if self.driver != None:
            logging.info('Cleaning up Chromdriver')
            self.driver.close()
            self.driver.quit()

    def setup_driver(self):
        if self.driver != None:
            return

        logging.info('Installing chromedriver')
        chromedriver_autoinstaller.install()
        logging.info('Starting webdriver')

        # Setup the browser to run headless
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        
        # Disable loading images, as we don't need them. (It'll make things go a lot quicker)
        options.add_experimental_option('prefs', {'profile.default_content_setting_values.images': 2})
        options.add_experimental_option('excludeSwitches', ['enable-logging'])

        service = ChromeService('ChromeDriver')
        service.creationflags = CREATE_NO_WINDOW

        # Start the headless version of chrome
        self.driver = webdriver.Chrome(service=service, chrome_options=options)
        self.driver.maximize_window()
        self.driver.delete_all_cookies()

    def search_page1(self, query_url, db):
        """
        Helper function to search the current page for new products, update the 
        database, and return a list of newly found products.
        """

        logging.info(f'Searching {self.driver.current_url} using method 1')

        # Parse the webpage and find the search results
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        results = soup.find('ul', {'id': 'search-results'})
        
        # List of new products that we have found
        new_products = []
        
        # Attempt to locate the nearby results banner
        stop_tag = soup.find('h4', {'class': 'ban nearby'})

        # If there is one, stop there
        if stop_tag != None:
            rows = stop_tag.findAllPrevious('li', {'class': 'result-row'})
        else:
            rows = results.findAll('li', {'class': 'result-row'})
 
        # Go through each search result
        for result in rows:
            # Extract the different information that we need
            link = result.find('a', {'class': 'result-title hdrlnk'})
            name = link.text
            id = link.get('data-id')
            url = link.get('href')

            # Create a product data structure representing it
            product = Product(id, name, url, query_url)
            
            # Check if this is a new product that we've not found before
            if db.get_product(product) == None:
                new_products.append(product)
            
            # Add or update the product in the database
            db.add_product(product)
            
        return new_products

    def search_page2(self, query_url, db):
        """
        Helper function to search the current page for new products, update the 
        database, and return a list of newly found products.
        """

        logging.info(f'Searching {self.driver.current_url} using method 2')

        # Parse the webpage and find the search results
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        results = soup.find('div', {'id': 'search-results-page-1'})
        
        # List of new products that we have found
        new_products = []
        
        # Attempt to locate the nearby results seperator
        stop_tag = results.find('li', {'class': 'nearby-separator'})

        # If there is one, stop there
        if stop_tag != None:
            rows = stop_tag.findAllPrevious('li', {'class': 'cl-search-result'})
        else:
            rows = results.findAll('li', {'class': 'cl-search-result'})
 
        # Go through each search result
        for result in rows:
            # Extract the different information that we need
            link = result.find('a', {'class': 'titlestring'})
            name = link.text
            url = link.get('href')
            id = re.findall('^.+/(\d+)\.html$', url)

            # Make sure that we were able to extract an ID
            if not len(id):
                logging.error(f'Unable to extract ID from URL {url}, skipping')
                continue

            # Create a product data structure representing it
            product = Product(id[0], name, url, query_url)
            
            # Check if this is a new product that we've not found before
            if db.get_product(product) == None:
                new_products.append(product)
            
            # Add or update the product in the database
            db.add_product(product)
            
        return new_products

    def next_page1(self):
        # Check if there's a link to the next page
        try:
            next_link = self.driver.find_element('xpath', '//a[@class="button next"]')
            href = next_link.get_attribute('href')
            more_pages = len(href) != 0
                
            # Load the new page
            if more_pages:
                self.driver.get(href)
            
        except:
            more_pages = False

        return more_pages

    def next_page2(self):
        # Locate the next page button
        next_page = self.driver.find_element('xpath', '//button[contains(@class, "cl-next-page")]')

        # Check if the button is disabled, i.e. no more pages
        disabled = 'bd-disabled' in next_page.get_attribute('class').split()
        if disabled:
            return False

        # If not, then click the button to move onto the next page
        next_page.click()
        return True

    def update_products(self, query_url, db):
        """
        Goes to the query-url, iterates through all the pages, and finds and returns
        a list of all new products while updating the database.
        """
        
        # Load the webpage
        self.driver.get(query_url)
        time.sleep(1)

        # List of new products that we have found
        new_products = []

        # Loop until we've reached all the pages
        more_pages = True
        while more_pages:
            # Make sure that an interruption is not requested
            if self.isInterruptionRequested():
                return new_products
        
            # Check if what type of URL we have, so we know what method to search the pages with
            if re.search('^.+#search=\d+~.+~\d+~\d+$', self.driver.current_url):
                new_products.extend(self.search_page2(query_url, db))
                more_pages = self.next_page2()
            else:
                new_products.extend(self.search_page1(query_url, db))
                more_pages = self.next_page1()

        return new_products
        
    def run(self):
        self.total_products = {}
        self.query_statuses = {}
        self.status = 'ok'

        try:
            # Make sure that the driver is setup
            self.setup_driver()

            # Free up space in the database by deleting any of the products we found a long time ago
            db = DB(config.db_path)
            db.delete_old_products()
        
            # Grab the queries
            queries = db.get_queries()
        except Exception as e:
            logging.exception(f'Failed to setup Chromedriver: {e}')
            self.status = 'bad'
            self.driver = None
            return

        # Update each query
        for query in queries:
            # Make sure that an interruption is not requested
            if self.isInterruptionRequested():
                return
        
            # Ignore any empty searches
            if len(query.query.strip()) == 0:
                continue
        
            # Update the products
            try:
                products = self.update_products(query.url(), db)

                if products != None:
                    self.total_products[query.id] = products

                self.query_statuses[query.url()] = 'ok'
            except Exception as e:
                logging.exception(f'Failed to update {query.url()}. Reason: {e}')
                self.query_statuses[query.url()] = 'bad'
                self.status = 'bad'
                continue
