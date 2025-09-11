import requests
from bs4 import BeautifulSoup
import urllib.parse
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "pl,en;q=0.9",
}
AREA_RE = re.compile(r'(\d+(?:[.,]\d+)?)\s*(m²|m2)\b', re.IGNORECASE)

def set_type(base_url, offer_type):
    if offer_type == 'sale':
        base_url = base_url.replace('wynajem', 'sprzedaz')
    return base_url

def set_city(base_url, city):

    city_name = urllib.parse.quote(city['text_simple'])
    return base_url.replace('Warszawa', city_name)

def build_url(filters):
    base_url = 'https://www.nieruchomosci-online.pl/szukaj.html?3,mieszkanie,wynajem,,Warszawa'
    base_url = set_city(base_url, filters['city'])
    base_url = set_type(base_url, filters['offer_type'])

    price_min = filters['min_price']
    price_max = filters['max_price']
    area_min  = filters['area_min']
    area_max  = filters['area_max']
    rooms_min = min(filters['selected_rooms']) if filters.get('selected_rooms') else 1
    rooms_max = max(filters['selected_rooms']) if filters.get('selected_rooms') else 4

    # format: ... ,,,,{priceMin}-{priceMax},{areaMin}-{areaMax},,,,,,,{roomsMin}-{roomsMax}
    url = f"{base_url},,,,{price_min}-{price_max},{area_min}-{area_max},,,,,,,{rooms_min}-{rooms_max}&o=modDate,desc"
    return url

def _txt(el):
    return el.get_text(strip=True) if el else None

def _area_from_node(node):
    # prefer the dedicated span.area
    span = node.select_one('span.area')
    if span:
        return _txt(span)
    # fallback: regex scan the price/area line or whole card
    t = _txt(node)
    if t:
        m = AREA_RE.search(t.replace('\xa0', ' '))
        if m:
            return m.group(0)
    return None

def _extract_floor(attr_box):
    # structure: <p><span>Piętro:</span><strong>parter</strong><strong>/</strong><strong>3</strong></p>
    if not attr_box:
        return None
    for item in attr_box.select('.attributes__box--item'):
        label = _txt(item.select_one('p span'))
        if label and 'piętro' in label.lower():
            strongs = [s.get_text(strip=True) for s in item.select('p strong')]
            # common patterns: ['parter', '/', '3'] or ['2', '/', '8']
            if strongs:
                # compress with slash if multiple parts
                return ''.join(strongs)
    return None

def _extract_rooms(attr_box):
    # structure: <p><span>Liczba pokoi:</span><strong>3</strong></p>
    if not attr_box:
        return None
    for item in attr_box.select('.attributes__box--item'):
        label = _txt(item.select_one('p span'))
        if label and ('liczba pokoi' in label.lower() or 'poko' in label.lower()):
            val = item.select_one('p strong')
            return _txt(val)
    return None

def parse_card(card):
    # Title + link
    h2 = card.select_one('h2.name a[href]')
    title = _txt(h2)
    link  = h2['href'] if h2 and h2.has_attr('href') else None

    # Location (district + city)
    loc_p = card.select_one('p.province')
    location = None
    if loc_p:
        # clean inner text, preserve commas/spaces
        location = ' '.join(loc_p.get_text(" ", strip=True).split())

    # Price + area (in same line)
    price_area_p = card.select_one('p.title-a.primary-display')
    price = None
    area  = None
    if price_area_p:
        spans = price_area_p.find_all('span')
        if spans:
            price = _txt(spans[0]).replace('\xa0', ' ') if _txt(spans[0]) else None
        area = _area_from_node(price_area_p)

    # Attributes (floor, rooms) are in the teaser box under .attributes__box
    attributes_box = card.select_one('#attributes_5, .attributes__box')  # specific id from snippet OR generic class
    floor = _extract_floor(attributes_box)
    rooms = _extract_rooms(attributes_box)

    # Short description (optional)
    desc = _txt(card.select_one('p.desc'))

    return {
        'title': title,
        'link': link,
        'location': location,
        'price': price,
        'area': area,
        'floor': floor,
        'rooms': rooms,
        'desc': desc
    }


def scrape_nieruchomosci(filters):
    url = build_url(filters)
    print("Requesting", url)
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'html.parser')

    listings = []

    cards = soup.select('div[id^="off-inner_"]') or soup.select('div.tile-inner.tile-inner-primary')

    for card in cards:
        data = parse_card(card)
        if data.get('link'):
            listings.append(data)

    return listings
