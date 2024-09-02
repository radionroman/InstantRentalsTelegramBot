from telegram import ReplyKeyboardMarkup
from src.utils.constants import *

start_menu_keyboard = [
    [BTN_OFFER_SOURCES, BTN_FILTERS],
    [BTN_PRICE_RANGE, BTN_AREA_RANGE],
    [BTN_ROOMS, BTN_OFFER_TYPE],
    [BTN_START_MONITORING],
]

cancel_keyboard = [[BTN_CANCEL]]

stop_monitoring_keyboard = [[BTN_STOP_MONITORING]]

def get_markup(user_data, user_id):
    if user_data[user_id]['last_seen_offer_otodom']:
        return stop_monitoring_markup
    else:
        return start_menu_markup


start_menu_markup = ReplyKeyboardMarkup(start_menu_keyboard, one_time_keyboard=False, resize_keyboard=True)
cancel_markup = ReplyKeyboardMarkup(cancel_keyboard, one_time_keyboard=True, resize_keyboard=True)
stop_monitoring_markup = ReplyKeyboardMarkup(stop_monitoring_keyboard, one_time_keyboard=True, resize_keyboard=True)

