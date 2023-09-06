import scrapy
import pycountry
import uuid
import json
import asyncio
from locations.items import GeojsonPointItem
from locations.categories import Code
from pyppeteer import launch

class GuardianSpider(scrapy.Spider):
    name = 'guardian'
    brand_name = 'guardian'
    spider_type = 'chain'
    spider_chain_id = '1839'
    spider_categories = [Code.BANK, Code.ATM]
    spider_countries = [pycountry.countries.lookup('MY').alpha_2]
    allowed_domains = ['guardian.com.my']
    start_urls = ['https://guardian.com.my/store_locator']

    # Initialize data_list outside of the parse_store function
    data_list = []

    async def parse(self, response):
        browser = await launch()
        page = await browser.newPage()
        await page.goto(response.url)
        content = await page.content()

        # Scraping data using XPath selectors with Scrapy
        # You can use BeautifulSoup here as well if you prefer
        for store_div in response.xpath('//div[contains(@class, "storeLocator-activeRecords-Mzj")]'):
            name = store_div.xpath('.//b/text()').get()
            address = store_div.xpath('.//div[contains(@style, "flex: 9 1 0%;")]/text()').get()
            postal_code = store_div.xpath('.//div[contains(@style, "flex: 9 1 0%;")]/following-sibling::div[2]/text()').get()

            store_url = 'https://guardian.com.my/store_details/' + name.replace(' ', '-').lower()
            yield scrapy.Request(store_url, callback=self.parse_store, meta={
                'name': name,
                'address': address,
                'postal_code': postal_code,
            })

        await browser.close()

    def parse_store(self, response, **cb_kwargs):
        name = cb_kwargs['name']
        address = cb_kwargs['address']
        postal_code = cb_kwargs['postal_code']

        data = {
            'ref': uuid.uuid4().hex,
            'store_name': name,
            'chain_id': '1839',
            'chain_name': 'GUARDIAN',
            '@spider': 'guardian_dac',
            'country': 'Malaysia',
            'brand': 'GUARDIAN',
            'postcode': postal_code,
            'addr_full': address,
            'website': "https://guardian.com.my/store_locator",
        }
        # Add the data to the data_list
        self.data_list.append(data)

    def close(self, reason):
        # Create GeoJSON features without geometry
        features = []
        for item in self.data_list:
            feature = {
                'type': 'Feature',
                'properties': item
            }
            features.append(feature)

        # Create GeoJSON FeatureCollection
        geojson_data = {}
           
