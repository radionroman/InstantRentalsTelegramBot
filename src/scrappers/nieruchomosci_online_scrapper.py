import requests
from bs4 import BeautifulSoup
import urllib


# https://www.nieruchomosci-online.pl/szukaj.html?3,mieszkanie,wynajem,,Warszawa:20571,,,,1000-2500,40-70,,,,,,1-4

def set_type(base_url, offer_type):
    if offer_type == 'sale':
        base_url = base_url.replace('wynajem', 'sprzedaz')
    return base_url

def set_city(base_url, city):
    city = city['text_simple']
    # incode city name to url format
    city = urllib.parse.quote(city)
    base_url = base_url.replace('Warszawa', city)
    return base_url


def build_url(filters):
    base_url = 'https://www.nieruchomosci-online.pl/szukaj.html?3,mieszkanie,wynajem,,Warszawa'
    base_url = set_city(base_url, filters['city'])
    owner_type = filters['owner_type']
    view_type =  filters['view_type']
    limit = filters['limit']
    price_min = filters['min_price']
    price_max = filters['max_price']
    area_min = filters['area_min']
    area_max = filters['area_max']
    selected_rooms = filters['selected_rooms']
    by = filters['by']
    direction = filters['direction']
    days = filters['days']
    offer_type = filters['offer_type']


    base_url = set_type(base_url, offer_type)

    url = f"{base_url},,,,,{price_min}-{price_max},{area_min}-{area_max},,,,,,,{selected_rooms[0]}-{selected_rooms[-1]}"


    return url

def scrape_nieruchomosci(filters):
    url = build_url(filters)

    print("Requesting", url) 
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(response.content, 'html.parser')

    listings = []

    rental_offers = soup.find_all('div', class_='tile tile-tile')

# Extract and print the data
    for offer in rental_offers:
        title = offer.find('h2', class_='name').text.strip()
        link = offer.find('h2', class_='name').find('a')['href']
        location = offer.find('p', class_='province').text.strip().replace('\n', ' ')
        price = offer.find('p', class_='title-a primary-display').find_all('span')[0].text.strip()
        area = offer.find('p', class_='title-a primary-display').find('span', class_='area').text.strip()

        listings.append({
            'title': title,
            'link': link,
            'location': location,
            'price': price,
            'area': area
        })



    return listings