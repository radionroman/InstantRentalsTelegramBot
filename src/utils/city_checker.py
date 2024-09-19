import json
from thefuzz import fuzz

# [{'region_name': 'Dolnośląskie', 'cities': [{'id': '21325', 'text': 'Bielany Wrocławskie, gm. Kobierzyce, wrocławski, Dolnośląskie', 'text_simple': 'Bielany Wrocławskie', 'text_gray': 'wrocławski', 'lon': '16.97184', 'lat': '51.03923', 'zoom': '12', 'url': 'bielany-wroclawskie', 'districts': []}, {'id': '3197', 'text': 'Bielawa, dzierżoniowski, Dolnośląskie', 'text_simple': 'Bielawa', 'text_gray': 'dzierżoniowski', 'lon': '16.62663', 'lat': '50.68988', 'zoom': '12', 'url': 'bielawa', 'districts': []}, {'id': '24495', 'text': 'Bogatynia, zgorzelecki, Dolnośląskie', 'text_simple': 'Bogatynia', 'text_gray': 'zgorzelecki', 'lon': '14.95655', 'lat': '50.91416', 'zoom': '12', 'url': 'bogatynia', 'districts': [{'id': '545', 'city_id': '24495', 'text': 'Bogatynia, Centrum', 'text_district': 'Centrum', 'text_gray': '', 'lon': '14.95679', 'lat': '50.90693', 'zoom': 13}, {'id': '547', 'city_id': '24495', 'text': 'Bogatynia, Markocice', 'text_district': 'Markocice', 'text_gray': '', 'lon': '14.95679', 'lat': '50.90693', 'zoom': 13}, {'id': '413', 'city_id': '24495', 'text': 'Bogatynia, Zatonie', 'text_district': 'Zatonie', 'text_gray': '', 'lon': '14.95655', 'lat': '50.91416', 'zoom': 13}, {'id': '549', 'city_id': '24495', 'text': 'Bogatynia, Zatonie-Kolonia', 'text_district': 'Zatonie-Kolonia', 'text_gray': '', 'lon': '14.95679', 'lat': '50.90693', 'zoom': 13}]}, {'id': '42471', 'text': 'Boguszów-Gorce, wałbrzyski, Dolnośląskie', 'text_simple': 'Boguszów-Gorce', 'text_gray': 'wałbrzyski', 'lon': '16.20327', 'lat': '50.75229', 'zoom': '12', 'url': 'boguszow-gorce', 'districts': []}, {'id': '24545', 'text': 'Bolesławiec, bolesławiecki, Dolnośląskie', 'text_simple': 'Bolesławiec', 'text_gray': 'bolesławiecki', 'lon': '15.56956', 'lat': '51.26247', 'zoom': '12', 'url': 'boleslawiec', 'districts': []},

def remove_polish_chars(city):
    city = city.lower().replace('ą', 'a').replace('ć', 'c').replace('ę', 'e').replace('ł', 'l').replace('ń', 'n').replace('ó', 'o').replace('ś', 's').replace('ź', 'z').replace('ż', 'z')
    return city

def find_city_in_region(region, city_) -> bool:
    # Parse miasta_.json to get the list of cities in the region
    with open('src/utils/miasta_.json', 'r') as file:
        data = json.load(file)

    cities_in_region = []
    for region_ in data:
        if fuzz.ratio(remove_polish_chars(region_['region_name']), remove_polish_chars(region)) > 95:
            print(region_['region_name'])
            cities_in_region = region_['cities']
            break

    print(cities_in_region)
    # Check if the city is in the list of cities in the region
    for city in cities_in_region:
        if not city:
            continue
        
        if fuzz.ratio(remove_polish_chars(city['text_simple']), remove_polish_chars(city_)) > 80:
            return city
    return None



