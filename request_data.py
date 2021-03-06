import pandas as pd
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
from contextlib import closing
from requests import get
import unicodedata
import re
import json
import logging
logging.basicConfig(filename='hemnet.log',level=logging.INFO)
import os
import sys

def simple_get(url):
    """
    Attempts to get the content at `url` by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the
    text content, otherwise return None.
    """
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None

    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))
        return None


def is_good_response(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200
            and content_type is not None
            and content_type.find('html') > -1)


def log_error(e):
    """
    It is always a good idea to log errors.
    This function just prints them, but you can
    make it do anything.
    """
    print(e)


def find_numbers(text):
    regexp = re.compile('(\d+)')

    results = regexp.findall(text)
    price_str = ''
    for result in results:
        price_str += result
    return float(price_str)


def load_house_data(url):
    data = {}

    raw_html = simple_get(url=url)
    html_ = BeautifulSoup(raw_html, 'html.parser')

    item = html_.find(class_='sold-property__price')
    text = item.find(class_='sold-property__price-value').text
    text_ = unicodedata.normalize('NFKD', text)
    data['price'] = text_

    item = html_.find(class_='sold-property__details')
    attribute_names = []
    for attribute in item.find_all(class_='sold-property__attribute'):
        attribute_names.append(attribute.text)

    attributes = {}

    for name, value_item in zip(attribute_names, item.find_all(class_='sold-property__attribute-value')):
        value_str = unicodedata.normalize('NFKD', value_item.text)
        # value = find_numbers(text = value_str)
        attributes[name] = value_str

    data.update(attributes)

    map_item = html_.find(class_='sold-property__map')
    map_data = json.loads(map_item['data-initial-data'])

    listing = map_data['listing']
    data['id'] = listing['id']
    data['coordinate'] = listing.get('coordinate')
    data['type'] = listing.get('type')
    if not data['type']:
        data['type'] = listing.get('typeSummary')
        if not data['type']:
            data['type'] = listing.get('iconName')

    data['address'] = listing.get('address')
    data['map_url'] = map_data.get('map_url')
    data['url'] = listing.get('url')
    data['sale_date'] = listing.get('sale_date')

    data = pd.Series(data)
    data.name = data['id']

    #data.drop(index='Prisutveckling', inplace=True)

    return data


def get_data(file_path,i_max = None):

    logging.info('Running from:%s' % os.path.abspath(''))
    part1 = r'https://www.hemnet.se/salda/bostader?item_types%5B%5D=villa&item_types%5B%5D=radhus&location_ids%5B%5D=17783&location_ids%5B%5D=18010&location_ids%5B%5D=18030&page='
    part2 = r'&sold_age=all'

    #if os.path.exists(file_path):
    #    os.remove(file_path)

    ok = True
    i = 0
    checked_urls = []
    if os.path.exists(file_path):
        old_house_data = pd.read_csv(os.path.join(file_path), sep=';')
        checked_urls = old_house_data['url']

    columns = ['Antal rum',
               'Begärt pris',
               'Boarea',
               'Byggår',
               'Driftskostnad',
               'Pris per kvadratmeter',
               'Tomtarea',
               'address',
               'coordinate',
               'id',
               'map_url',
               'price',
               'sale_date',
               'type',
               'url',
               'Biarea',
               'Avgift/månad',
               'Prisutveckling',]

    while ok:
        i+= 1

        if not i_max is None:
            if i > i_max:
                break

        try:
            url = part1 + '%i' % i + part2
            logging.info('Loading data from url:%s' % url)
            raw_html = simple_get(url=url)
            html = BeautifulSoup(raw_html, 'html.parser')

            house_data = pd.DataFrame(columns=columns)

            for item_link_contaier in html.find_all(class_="item-link-container"):
                house_url = item_link_contaier['href']
                if house_url in checked_urls:
                    continue
                try:
                    data = load_house_data(url=house_url)
                except:
                    logging.exception('Skipping house')
                else:
                    house_data = house_data.append(data)

            #Saving (By appending):
            logging.info('Saving data to:%s' % file_path)
            house_data[columns].to_csv(file_path, index=False, mode='a', sep=';')

        except:
            ok = False
            logging.exception('Could not find page:%i' % i)



if __name__ == '__main__':

    file_path = sys.argv[1]
    print(file_path)
    house_data = get_data(file_path=file_path)
