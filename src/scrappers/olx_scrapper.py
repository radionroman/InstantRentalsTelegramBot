from bs4 import BeautifulSoup
import sys
import requests
import re
from urllib.parse import urljoin

# <div class="css-wsrviy" data-testid="qa-header-message"><div class="css-1kbfsd9"></div><div><p class="css-8gj8ho"></p><p class="css-196yitg">Nie znaleźliśmy żadnych wyników, ale poniżej znajdziesz ogłoszenia powiązane z ostatnio oglądanymi ogłoszeniami:</p></div></div>

# selected_rooms = [1,2]
# selected_rooms_url = 'search%5Bfilter_enum_rooms%5D%5B0%5D=one&search%5Bfilter_enum_rooms%5D%5B1%5D=two'

def build_selected_rooms_url(selected_rooms):
    selected_rooms_url = ''
    for room in selected_rooms:
        if room == 1:
            selected_rooms_url += 'search%5Bfilter_enum_rooms%5D%5B0%5D=one&'
        elif room == 2:
            selected_rooms_url += 'search%5Bfilter_enum_rooms%5D%5B1%5D=two&'
        elif room == 3:
            selected_rooms_url += 'search%5Bfilter_enum_rooms%5D%5B2%5D=three&'
        else:
            selected_rooms_url += 'search%5Bfilter_enum_rooms%5D%5B3%5D=four&'
        
    return selected_rooms_url

def set_type(base_url, offer_type):
    if offer_type == 'sale':
        base_url = base_url.replace('wynajem', 'sprzedaz')
    return base_url

def set_region_and_city(url, region, city):
    #remove polish characters
    city = city['url']
    url = url.replace('warszawa', city.lower())
    return url

# https://www.olx.pl/nieruchomosci/mieszkania/wynajem/warszawa/?search%5Border%5D=created_at:desc&search%5Bfilter_float_price:from%5D=1000&search%5Bfilter_float_m:from%5D=25&search%5Bfilter_float_m:to%5D=50&search%5Bfilter_enum_rooms%5D%5B0%5D=one&search%5Bfilter_enum_rooms%5D%5B1%5D=two
def build_url(filters):
    base_url = 'https://www.olx.pl/nieruchomosci/mieszkania/wynajem/warszawa/?'
    base_url = set_region_and_city(base_url, filters['region'], filters['city'])
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
    region = filters['region']
    city = filters['city']

    base_url = set_type(base_url, offer_type)

    selected_rooms_url = build_selected_rooms_url(selected_rooms)

    url = f"{base_url}search%5Border%5D=created_at:desc&search%5Bfilter_float_price:from%5D={price_min}&search%5Bfilter_float_price:to%5D={price_max}&search%5Bfilter_float_m:from%5D={area_min}&search%5Bfilter_float_m:to%5D={area_max}&{selected_rooms_url}"
    
    
    return url





OLX = "https://www.olx.pl"

AREA_RE = re.compile(r'(\d+(?:[.,]\d+)?)\s*(?:m²|m2)\b', re.IGNORECASE)

def _txt(el):
    return el.get_text(strip=True) if el else None

def _first(soup, selectors):
    for sel in selectors:
        n = soup.select_one(sel)
        if n:
            return n
    return None

def _area_from_blueprint(card):

    block = card.select_one('[data-testid="blueprint-card-param-icon"]')
    if block:
        parent_text = _txt(block.parent)  # e.g. "25 m²"
        if parent_text and AREA_RE.search(parent_text):
            return AREA_RE.search(parent_text).group(0)

    for el in card.select('span, p, li, dd, div'):
        t = _txt(el)
        if t and AREA_RE.search(t):
            return AREA_RE.search(t).group(0)
    return None

def _is_featured(card):
    if card.find(string=lambda s: isinstance(s, str) and 'wyróżnione' in s.lower()):
        return True
    
    if card.find(string=lambda s: isinstance(s, str) and 'promowan' in s.lower()):
        return True
    return False

def parse_card(card):

    title_block = card.select_one('[data-cy="ad-card-title"]')
    link_a = None
    if title_block:
        link_a = title_block.select_one('a[href]')
    if not link_a:
        link_a = _first(card, ['a.css-1tqlkj0[href]', 'a[href^="/d/oferta/"]', 'a[href^="/oferta/"]'])
    href = link_a['href'] if link_a and link_a.has_attr('href') else None
    if href and href.startswith('/'):
        href = urljoin(OLX, href)

    title_el = title_block.select_one('h4') if title_block else None
    title = _txt(title_el) or (link_a.get('title') if link_a and link_a.has_attr('title') else None)

    price_el = card.select_one('[data-testid="ad-price"]')
    price = _txt(price_el)
    if price:
        price = price.replace('\xa0', ' ')

    loc_el = card.select_one('[data-testid="location-date"]')
    location = updated_date = None
    if loc_el:
        raw = _txt(loc_el)
        if raw and ' - ' in raw:
            location, updated_date = [s.strip() for s in raw.split(' - ', 1)]
        else:
            location = raw

    area = _area_from_blueprint(card)

    return {
        'title': title,
        'link': href,
        'price': price,
        'location': location,
        'updated_date': updated_date,
        'area': area,
        'featured': _is_featured(card),
    }

def scrape_olx(filters):
    url = build_url(filters) 
    print("Requesting", url)
    r = requests.get(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "pl,en;q=0.9",
    }, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'html.parser')



    if soup.select_one('[data-testid="qa-header-message"]'):
        return []

    cards = soup.select('[data-cy="l-card"][data-testid="l-card"]') or \
            soup.select('[data-cy="l-card"]') or \
            soup.select('[data-testid="l-card"]')

    listings = []
    for card in cards:
        data = parse_card(card)
        
        if data and data.get('link'):
            listings.append(data)

    return listings
