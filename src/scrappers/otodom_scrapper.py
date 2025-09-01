from bs4 import BeautifulSoup
import sys
import requests

# selected_rooms = [2,3]
# selected_rooms_url = '%5BTWO%2CTHREE%5D'

def build_selected_rooms_url(selected_rooms):
    selected_rooms_url = '%5B'
    for room in selected_rooms:
        if room == 1:
            selected_rooms_url += 'ONE'
        elif room == 2:
            selected_rooms_url += 'TWO'
        elif room == 3:
            selected_rooms_url += 'THREE'
        elif room == 4:
            selected_rooms_url += 'FOUR%2CFIVE%2CSIX_OR_MORE'
        if room != selected_rooms[-1]:
            selected_rooms_url += '%2C'
    
    selected_rooms_url += '%5D'
    return selected_rooms_url

def set_type(base_url, offer_type):
    if offer_type == 'sale':
        base_url = base_url.replace('wynajem', 'sprzedaz')
    return base_url

def set_region_and_city(url, region, city):
    #remove polish characters
    city = city['url']
    url = url.replace('warszawa', city.lower())
    url = url.replace('mazowieckie', region.lower().replace('ą', 'a').replace('ł', 'l').replace('ń', 'n').replace('ć', 'c').replace('ó', 'o').replace('ę', 'e').replace('ś', 's').replace('ż', 'z').replace('ź', 'z'))
    return url

# https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/mazowieckie/warszawa/warszawa/warszawa?limit=36&priceMin=0&priceMax=3000&areaMin=5&areaMax=50&roomsNumber=%5BTWO%2CTHREE%5D&by=DEFAULT&direction=DESC&viewType=listing
def build_url(filters):
    base_url = 'https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/mazowieckie/warszawa/warszawa/warszawa?'
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

    base_url = set_type(base_url, offer_type)

    selected_rooms_url = build_selected_rooms_url(selected_rooms)

    url = f"{base_url}ownerTypeSingleSelect={owner_type}&viewType={view_type}&limit={limit}&priceMin={price_min}&priceMax={price_max}&areaMin={area_min}&areaMax={area_max}&roomsNumber={selected_rooms_url}&by={by}&direction={direction}"
    return url


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python otodom_scrapper.py <min_price> <max_price>')
        sys.exit(1)

    min_price = int(sys.argv[1])
    max_price = int(sys.argv[2])

    from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests

OTODOM = "https://www.otodom.pl"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "pl,en;q=0.9",
}

def _txt(el):
    return el.get_text(strip=True) if el else None

def _infer_spec(text):
    """Return ('rooms'|'area'|'floor', cleaned_value) or (None, None)."""
    if not text:
        return None, None
    t = text.lower()
    if 'pok' in t:   # '1 pokój', '2 pokoje', etc.
        return 'rooms', text
    if 'm²' in t or 'm2' in t:
        return 'area', text
    if 'piętro' in t or 'pietro' in t:
        return 'floor', text
    return None, None

def _is_promoted(card):
    # promoted if any ancestor has the promoted container marker
    par = card
    while par:
        if getattr(par, 'attrs', None) and par.attrs.get('data-cy') == 'search.listing.promoted':
            return True
        par = par.parent
    # soft fallback: look for "PODBITE" badge / label near the card
    if card.find(string=lambda s: isinstance(s, str) and 'PODBITE' in s.upper()):
        return True
    return False

def parse_listing_card(card):
    # Link + Title
    link_a = card.select_one('a[data-cy="listing-item-link"]')
    link = urljoin(OTODOM, link_a['href']) if link_a and link_a.has_attr('href') else None

    title_el = card.select_one('[data-cy="listing-item-title"]')
    title = _txt(title_el)

    # Price (main + possible extra like '+ czynsz...')
    price_main_el = card.select_one('span[data-sentry-element="MainPrice"]')
    price_main = _txt(price_main_el)
    # the extra is often the next sibling span inside the same price wrapper
    price_extra = None
    if price_main_el and price_main_el.parent:
        extra_spans = [s for s in price_main_el.parent.find_all('span') if s is not price_main_el]
        if extra_spans:
            price_extra = _txt(extra_spans[0])

    # Address
    address_el = card.select_one('p[data-sentry-component="Address"]')
    address = _txt(address_el)

    # Specs: rooms / area / floor
    rooms = area = floor = None
    # The grid uses a <dl> list; dd holds human text like '1 pokój', '30 m²', '10 piętro'
    for dd in card.select('dl dd'):
        val = _txt(dd)
        kind, cleaned = _infer_spec(val)
        if kind == 'rooms' and rooms is None:
            rooms = cleaned
        elif kind == 'area' and area is None:
            area = cleaned
        elif kind == 'floor' and floor is None:
            floor = cleaned

    return {
        'title': title,
        'link': link,
        'price': price_main,
        'price_extra': price_extra,
        'location': address,
        'room_count': rooms,
        'area': area,
        'floor': floor,
        'promoted': _is_promoted(card),
    }

def scrape_otodom(filters):
    url = build_url(filters)  
    print("Requesting", url)
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'html.parser')

    # This matches both "Promowane ogłoszenia" and regular list cards
    cards = soup.select('article[data-sentry-component="AdvertCard"]')

    listings = []
    for card in cards:
        data = parse_listing_card(card)
        # require at least a link to consider it a valid listing
        if data.get('link'):
            listings.append(data)

    return listings
