

offer_sources = [
    {
        'name': 'Otodom',
        'url': 'https://www.otodom.pl'
    },
    {
        'name': 'OLX',
        'url': 'https://www.olx.pl'
    },
    {
        'name': 'Nieruchomości Online',
        'url': 'https://www.nieruchomosci-online.pl'
    }
]

#define names for keyboard buttons
BTN_OFFER_SOURCES = 'List Offer Sources 📋'
BTN_FILTERS = 'Show Filters ⚙️'
BTN_CHANGE_FILTERS = 'Change Filters ⚙️'
BTN_PRICE_RANGE = 'Set Price Range 🤑'
BTN_AREA_RANGE = 'Set Area Range 🏰'
BTN_START_MONITORING = 'Start Monitoring 🕵️'
BTN_STOP_MONITORING = 'Stop Monitoring 🛑'
BTN_ROOMS = 'Select Rooms 🛏️'
BTN_OFFER_TYPE = 'Switch Offer Type 🏠'
BTN_CANCEL = 'Cancel 🚫'

DEFAULT_USER_DATA = {
    'minimum_price': 0,
    'maximum_price': 1000000,
    'owner_type': 'ALL',
    'view_type': 'listing',
    'limit': '36',
    'area_min': '0',
    'area_max': '1000',
    'by': 'DEFAULT',
    'direction': 'DESC',
    'days': '1',
    'last_seen_offer_olx': None,
    'last_seen_offer_otodom': None,
    'last_seen_offer_nieruchomosci_online': None,
    'selected_rooms': [1,2,3,4],
    'selected_sources': ['otodom', 'olx'],
    'offer_type': 'rent'
}