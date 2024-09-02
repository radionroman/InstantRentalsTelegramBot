import db_placeholder as db
from telegram import Update
from telegram.ext import CallbackContext


def get_filters(update: Update, context: CallbackContext) -> None:
    """
    This function shows the current filters set by the user
    """
    if update.message:
        user_id = update.message.from_user.id
        user_name = update.message.from_user.first_name
    else:
        user_id = update.callback_query.from_user.id
        user_name = update.callback_query.from_user.first_name


    minimum_price = db.user_data[user_id]['minimum_price']
    maximum_price = db.user_data[user_id]['maximum_price']
    area_min = db.user_data[user_id]['area_min']
    area_max = db.user_data[user_id]['area_max']
    selected_rooms = db.user_data[user_id].get('selected_rooms', [])
    offer_type = db.user_data[user_id]['offer_type']


    print(f'User {user_name} requested the filters')

    context.bot.send_message(
        user_id,
        f"Current filters:\n"
        f"Price range: {minimum_price} PLN - {maximum_price} PLN\n"
        f"Area range: {area_min} m² - {area_max} m²\n"
        f"Rooms: {', '.join(f'{room}' for room in sorted(selected_rooms))}\n"
        f"Offer type: {offer_type}",
        
        
    )