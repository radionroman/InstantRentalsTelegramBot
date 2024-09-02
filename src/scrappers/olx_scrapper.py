from bs4 import BeautifulSoup
import sys
import requests

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

# https://www.olx.pl/nieruchomosci/mieszkania/wynajem/warszawa/?search%5Border%5D=created_at:desc&search%5Bfilter_float_price:from%5D=1000&search%5Bfilter_float_m:from%5D=25&search%5Bfilter_float_m:to%5D=50&search%5Bfilter_enum_rooms%5D%5B0%5D=one&search%5Bfilter_enum_rooms%5D%5B1%5D=two
def build_url(filters):
    base_url = 'https://www.olx.pl/nieruchomosci/mieszkania/wynajem/warszawa/?'
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

    url = f"{base_url}search%5Border%5D=created_at:desc&search%5Bfilter_float_price:from%5D={price_min}&search%5Bfilter_float_price:to%5D={price_max}&search%5Bfilter_float_m:from%5D={area_min}&search%5Bfilter_float_m:to%5D={area_max}&{selected_rooms_url}"
    return url





def scrape_olx(filters):
    url = build_url(filters)
    print("Requesting", url)
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(response.content, 'html.parser')



    listings = []

    if soup.find('div', class_='css-wsrviy'):
        return listings

    # Find all listings by selecting the main div that holds each offer
    offers = soup.find_all('div', class_='css-1g5933j')

    for offer in offers:
        # Extract the title

        if offer.find('div', {'data-testid': 'adCard-featured'}):
            continue
    
        title_tag = offer.find('h6', class_='css-1wxaaza')
        title = title_tag.text.strip() if title_tag else None
        
        # Extract the link
        link_tag = offer.find('a', class_='css-z3gu2d')
        link = link_tag['href'] if link_tag else None

        #ignore link to otodom
        if 'otodom' in link:
            continue

        # Extract the price
        price_tag = offer.find('p', class_='css-13afqrm')
        price = price_tag.text.strip().replace(u'\xa0', ' ') if price_tag else None

        # Extract the location and date
        location_date_tag = offer.find('p', class_='css-1mwdrlh')
        location_date = location_date_tag.text.strip() if location_date_tag else None
        location, updated_date = location_date.split(' - ') if location_date and ' - ' in location_date else (location_date, None)

        # Extract the area
        area_tag = offer.find('span', class_='css-643j0o')
        area = area_tag.text.strip() if area_tag else None

        listings.append({
            'title': title,
            'link': f"https://www.olx.pl{link}" if link else None,
            'price': price,
            'location': location,
            'updated_date': updated_date,
            'area': area
        })

    return listings


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python otodom_scrapper.py <min_price> <max_price>')
        sys.exit(1)

    min_price = int(sys.argv[1])
    max_price = int(sys.argv[2])

    