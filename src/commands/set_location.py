from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, MessageHandler, Filters
from src.utils.markups import cancel_markup, get_markup, choose_region_markup, yes_no_markup
from src.utils.constants import BTN_CANCEL, BTN_SET_LOCATION
import db_placeholder as db
from src.utils.city_checker import find_city_in_region

REGION, CITY, SET = range(3)



# Initiates the conversation for setting the location.
def set_location_start(update: Update, context: CallbackContext) -> int:
    if update.message:
        user_id = update.message.from_user.id
        user_name = update.message.from_user.first_name
    else:
        user_id = update.callback_query.from_user.id
        user_name = update.callback_query.from_user.first_name

    context.bot.send_message(user_id, "Please choose region.", reply_markup=choose_region_markup)

    return REGION

# Asks the user to enter the city in the selected region.
def ask_city_in_region(update: Update, context: CallbackContext) -> int:
    region = update.message.text
    context.user_data['region'] = region
    update.message.reply_text(f"Please enter the city in {region}.", reply_markup=cancel_markup)
    return CITY

# Checks if the city is in the selected region.
def check_city(update: Update, context: CallbackContext) -> int:
    region = context.user_data['region']
    city = update.message.text
    actual_city = find_city_in_region(region, city)
    if actual_city is None:
        update.message.reply_text("City not found. Please enter the city again.", reply_markup=cancel_markup)
        return CITY
    context.user_data['city'] = actual_city
    # Ask user if the city is correct
    update.message.reply_text(f"Did you mean {actual_city['text_simple']}?", reply_markup=yes_no_markup)
    return SET
    

# Stores the location and ends the conversation.
def set_location(update: Update, context: CallbackContext) -> int:
    if update.message.text != 'Yes':
        update.message.reply_text("Please enter the city again.", reply_markup=cancel_markup)
        return CITY
    user_id = update.message.from_user.id
    location = update.message.location
    context.user_data['location'] = location
    region = context.user_data['region']
    city = context.user_data['city']
    
    db.user_data[user_id]['region'] = region
    db.user_data[user_id]['city'] = {"text" : city['text'], "url" : city['url'], "text_simple" : city['text_simple']}

    update.message.reply_text(f"Location set to {city['text_simple']}, {region}.", reply_markup=get_markup(db.user_data,user_id))
    return ConversationHandler.END

def cancel_location(update: Update, context: CallbackContext) -> int:
    """
    Cancels the location-setting conversation.
    """
    if update.message:
        user_id = update.message.from_user.id
    else:
        user_id = update.callback_query.from_user.id

    update.message.reply_text("Location setting cancelled.", reply_markup=get_markup(db.user_data,user_id))
    return ConversationHandler.END


location_conv_handler = ConversationHandler(
    entry_points=[MessageHandler(Filters.regex(f'^{BTN_SET_LOCATION}$'), set_location_start)],
    states={
        REGION: [MessageHandler(Filters.text & ~Filters.command & ~Filters.regex(f'^{BTN_CANCEL}$'), ask_city_in_region)],
        CITY: [MessageHandler(Filters.text & ~Filters.command & ~Filters.regex(f'^{BTN_CANCEL}$'), check_city)],
        SET: [MessageHandler(Filters.text & ~Filters.command & ~Filters.regex(f'^{BTN_CANCEL}$'), set_location)]

    },
    fallbacks=[CommandHandler('cancel', cancel_location), MessageHandler(Filters.regex(f'^{BTN_CANCEL}$'), cancel_location)]
)