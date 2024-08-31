from bs4 import BeautifulSoup
import sys
import requests


# https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/mazowieckie/warszawa/warszawa/warszawa?limit=36&priceMin=0&priceMax=3000&areaMin=5&areaMax=50&roomsNumber=%5BTWO%2CTHREE%5D&by=DEFAULT&direction=DESC&viewType=listing
def build_url(filters):
    base_url = 'https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/mazowieckie/warszawa/warszawa/warszawa?'
    owner_type = filters['owner_type']
    view_type =  filters['view_type']
    limit = filters['limit']
    price_min = filters['min_price']
    price_max = filters['max_price']
    area_min = filters['area_min']
    area_max = filters['area_max']
    rooms_number = filters['rooms_number']
    by = filters['by']
    direction = filters['direction']
    days = filters['days']

    url = f"{base_url}ownerTypeSingleSelect={owner_type}&viewType={view_type}&limit={limit}&priceMin={price_min}&priceMax={price_max}&areaMin={area_min}&areaMax={area_max}&roomsNumber={rooms_number}&by={by}&direction={direction}&daysSinceCreated={days}"
    return url





def scrape_otodom(filters):
    # url = offer_sources[0]['url']
    url = build_url(filters)
    print("Requesting", url)
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})


    soup = BeautifulSoup(response.content, 'html.parser')


    listings = []

    # Find all listings
    sections = soup.find_all('section', class_='eeungyz1 css-hqx1d9 e12fn6ie0')
    
    index = 0
    for section in sections:
        index += 1
        if index <= 3:
            continue
        
        # Extract the title
        title_tag = section.find('a', class_='css-16vl3c1 e17g0c820')
        title = title_tag.text.strip() if title_tag else None
        
        # Extract the link
        link = title_tag['href'] if title_tag else None
        
        # Extract the price
        price_tag = section.find('span', class_='css-2bt9f1 evk7nst0')
        price = price_tag.text.strip().replace(u'\xa0', ' ') if price_tag else None
        
        # Extract the location
        location_tag = section.find('p', class_='css-42r2ms eejmx80')
        location = location_tag.text.strip() if location_tag else None
        
        # Extract room count, area, and floor
        details = section.find('div', class_='css-1c1kq07 e1clni9t0')
        room_count = details.find('dd').text if details.find('dt').text == 'Liczba pokoi' else None
        area = details.find_all('dd')[1].text if len(details.find_all('dd')) > 1 else None
        floor = details.find_all('dd')[2].text if len(details.find_all('dd')) > 2 else None

        listings.append({
            'title': title,
            'link': f"https://www.otodom.pl{link}" if link else None,
            'price': price,
            'location': location,
            'room_count': room_count,
            'area': area,
            'floor': floor
        })

    return listings


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python otodom_scrapper.py <min_price> <max_price>')
        sys.exit(1)

    min_price = int(sys.argv[1])
    max_price = int(sys.argv[2])

    