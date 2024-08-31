import logging
import os
import requests
from bs4 import BeautifulSoup
from otodom_scrapper import scrape_otodom
from olx_scrapper import scrape_olx

from dotenv import load_dotenv
from collections import defaultdict
from telegram import Update, ForceReply, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler, ConversationHandler, JobQueue
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)



DEFAULT_USER_DATA = {
    'minimum_price': 0,
    'maximum_price': 1000000,
    'owner_type': 'ALL',
    'view_type': 'listing',
    'limit': '36',
    'area_min': '0',
    'area_max': '1000',
    'rooms_number': '%5BONE%2CTWO%2CTHREE%5D',
    'by': 'DEFAULT',
    'direction': 'DESC',
    'days': '1',
    'last_seen_offer_olx': None,
    'last_seen_offer_otodom': None,
    'selected_rooms': [1,2,3,4,5,6]
}

user_data = defaultdict(lambda: DEFAULT_USER_DATA.copy())

offer_sources = [
    {
        'name': 'Otodom',
        'url': 'https://www.otodom.pl'
    },
    {
        'name': 'OLX',
        'url': 'https://www.olx.pl'
    }
]

#define names for keyboard buttons
BTN_OFFER_SOURCES = 'List Offer Sources 📋'
BTN_FILTERS = 'Show Filters ⚙️'
BTN_PRICE_RANGE = 'Set Price Range 🤑'
BTN_AREA_RANGE = 'Set Area Range 🏰'
BTN_START_MONITORING = 'Start Monitoring 🕵️'
BTN_STOP_MONITORING = 'Stop Monitoring 🛑'
BTN_ROOMS = 'Select Rooms 🛏️'
BTN_CANCEL = 'Cancel 🚫'


start_menu_keyboard = [
    [BTN_OFFER_SOURCES, BTN_FILTERS],
    [BTN_PRICE_RANGE, BTN_AREA_RANGE],
    [BTN_ROOMS, BTN_START_MONITORING]
]

cancel_keyboard = [[BTN_CANCEL]]

stop_monitoring_keyboard = [[BTN_STOP_MONITORING]]

def get_markup(user_id):
    if user_data[user_id]['last_seen_offer_otodom']:
        return stop_monitoring_markup
    else:
        return start_menu_markup


start_menu_markup = ReplyKeyboardMarkup(start_menu_keyboard, one_time_keyboard=False, resize_keyboard=True)
cancel_markup = ReplyKeyboardMarkup(cancel_keyboard, one_time_keyboard=True, resize_keyboard=True)
stop_monitoring_markup = ReplyKeyboardMarkup(stop_monitoring_keyboard, one_time_keyboard=True, resize_keyboard=True)


def echo(update: Update, context: CallbackContext) -> None:
    """
    This function would be added to the dispatcher as a handler for messages coming from the Bot API
    """
    # Print to console
    print(f'{update.message.from_user.first_name} wrote {update.message.text}')
    update.message.reply_text("I'm sorry, I'm not sure what you mean. Please use the /menu command to see the available options.")


def site_list(update: Update, context: CallbackContext) -> None:
    """
    This function shows a list of available offer sources
    """
    if update.message:
        user_id = update.message.from_user.id
        user_name = update.message.from_user.first_name
    else:
        user_id = update.callback_query.from_user.id
        user_name = update.callback_query.from_user.first_name

    print(f'user {user_name} requested the list of offer sources')
    context.bot.send_message(
        user_id,
        "Here are the available offer sources:\n\n"
        + "\n".join([f"{source['name']}: {source['url']}" for source in offer_sources]),
        ParseMode.HTML
    )

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text( "Please choose an action", reply_markup=get_markup(update.message.from_user.id))


MIN_PRICE, MAX_PRICE = range(2)

def set_price_start(update: Update, context: CallbackContext) -> int:
    """
    Initiates the conversation for setting the price range.
    """
    if update.message:
        user_id = update.message.from_user.id
        user_name = update.message.from_user.first_name
    else:
        user_id = update.callback_query.from_user.id
        user_name = update.callback_query.from_user.first_name

    context.bot.send_message(user_id, "Please enter the minimum price in PLN.", reply_markup=cancel_markup)
    return MIN_PRICE

def set_min_price(update: Update, context: CallbackContext) -> int:
    """
    Stores the minimum price and asks for the maximum price.
    """
    try:
        print('set_min_price')
        if update.message:
            user_id = update.message.from_user.id
        else:
            user_id = update.callback_query.from_user.id
        minimum_price = int(update.message.text)
        context.user_data['minimum_price'] = minimum_price
        context.bot.send_message(user_id, "Now, please enter the maximum price in PLN.")
        return MAX_PRICE
    except ValueError:
        context.bot.send_message(user_id, "Please enter a valid number for the minimum price.")
        return MIN_PRICE

def set_max_price(update: Update, context: CallbackContext) -> int:
    """
    Stores the maximum price and ends the conversation.
    """
    try:
        if update.message:
            user_id = update.message.from_user.id
        else:
            user_id = update.callback_query.from_user.id

        maximum_price = int(update.message.text)
        minimum_price = context.user_data['minimum_price']

        if maximum_price < minimum_price:
            context.bot.send_message(user_id, "Maximum price should be greater than or equal to minimum price. Please enter the maximum price again.")
            return MAX_PRICE

        
        user_data[user_id]['minimum_price'] = minimum_price
        user_data[user_id]['maximum_price'] = maximum_price

        context.bot.send_message(user_id, f"Price range set to {minimum_price} PLN - {maximum_price} PLN.", reply_markup=get_markup(user_id))
        return ConversationHandler.END
    except ValueError:
        update.message.reply_text("Please enter a valid number for the maximum price.")
        return MAX_PRICE

def cancel(update: Update, context: CallbackContext) -> int:
    """
    Cancels the conversation.
    """
    if update.message:
        user_id = update.message.from_user.id
        user_name = update.message.from_user.first_name
    else:
        user_id = update.callback_query.from_user.id
        user_name = update.callback_query.from_user.first_name

    context.bot.send_message(user_id, "Operation cancelled.", reply_markup=get_markup(user_id))
    return ConversationHandler.END


MIN_AREA, MAX_AREA = range(2)

def set_area_start(update: Update, context: CallbackContext) -> int:
    """
    Initiates the conversation for setting the area range.
    """
    if update.message:
        user_id = update.message.from_user.id
        user_name = update.message.from_user.first_name
    else:
        user_id = update.callback_query.from_user.id
        user_name = update.callback_query.from_user.first_name

    context.bot.send_message(user_id, "Please enter the minimum area in square meters.", reply_markup=cancel_markup)
    return MIN_AREA

def set_min_area(update: Update, context: CallbackContext) -> int:
    """
    Stores the minimum area and asks for the maximum area.
    """
    try:
        minimum_area = int(update.message.text)
        context.user_data['minimum_area'] = minimum_area
        update.message.reply_text("Now, please enter the maximum area in square meters.")
        return MAX_AREA
    except ValueError:
        update.message.reply_text("Please enter a valid number for the minimum area.")
        return MIN_AREA

def set_max_area(update: Update, context: CallbackContext) -> int:
    """
    Stores the maximum area and ends the conversation.
    """
    
    try:
        maximum_area = int(update.message.text)
        minimum_area = context.user_data['minimum_area']

        if maximum_area < minimum_area:
            update.message.reply_text("Maximum area should be greater than or equal to minimum area. Please enter the maximum area again.")
            return MAX_AREA

        user_id = update.message.from_user.id
        user_data[user_id]['area_min'] = minimum_area
        user_data[user_id]['area_max'] = maximum_area

        update.message.reply_text(f"Area range set to {minimum_area} m² - {maximum_area} m².", reply_markup=get_markup(user_id))
        return ConversationHandler.END
    except ValueError:
        update.message.reply_text("Please enter a valid number for the maximum area.")
        return MAX_AREA

def cancel_area(update: Update, context: CallbackContext) -> int:
    """
    Cancels the area-setting conversation.
    """
    if update.message:
        user_id = update.message.from_user.id
        user_name = update.message.from_user.first_name
    else:
        user_id = update.callback_query.from_user.id
        user_name = update.callback_query.from_user.first_name


    context.bot.send_message(user_id, "Operation cancelled.", reply_markup=get_markup(user_id))
    return ConversationHandler.END

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


    minimum_price = user_data[user_id]['minimum_price']
    maximum_price = user_data[user_id]['maximum_price']
    area_min = user_data[user_id]['area_min']
    area_max = user_data[user_id]['area_max']
    selected_rooms = user_data[user_id].get('selected_rooms', [])

    print(f'User {user_name} requested the filters')

    context.bot.send_message(
        user_id,
        f"Current filters:\n"
        f"Price range: {minimum_price} PLN - {maximum_price} PLN\n"
        f"Area range: {area_min} m² - {area_max} m²\n"
        f"Rooms: {', '.join(f'{room}' for room in sorted(selected_rooms))}",
        
    )

def check_new_offers(context: CallbackContext):
    """This function is run periodically to check for new offers."""
    job = context.job
    user_id = job.context['user_id']
    user_name = context.bot.get_chat(user_id).first_name

    # Extract user-specific filter parameters
    filters = {
        'min_price': user_data[user_id]['minimum_price'],
        'max_price': user_data[user_id]['maximum_price'],
        'owner_type': user_data[user_id]['owner_type'],
        'view_type': user_data[user_id]['view_type'],
        'limit': user_data[user_id]['limit'],
        'area_min': user_data[user_id]['area_min'],
        'area_max': user_data[user_id]['area_max'],
        'rooms_number': user_data[user_id]['rooms_number'],
        'by': user_data[user_id]['by'],
        'direction': user_data[user_id]['direction'],
        'days': user_data[user_id]['days']
    }

    # Initialize the sites and corresponding scraping functions
    sites = {
        'otodom': scrape_otodom,
        'olx': scrape_olx,
        # Add other sites and their respective scraping functions here
        # 'other_site': scrape_other_site_function,
    }

    print(f'Checking for new offers for user {user_id}...')

    # Loop through each site and scrape offers
    for site, scrape_function in sites.items():
        print(f'Checking {site} for new offers for user {user_name}...')
        
        offers = scrape_function(filters)

        if offers:
            new_offers = []
            last_seen_offer = user_data[user_id].get(f'last_seen_offer_{site}')

            for offer in offers:
                # Compare with the last seen offer for this specific site
                if last_seen_offer is None or offer['link'] != last_seen_offer:
                    new_offers.append(offer)
                else:
                    break  # Stop as we've reached offers we've seen before

            if new_offers:
                if not last_seen_offer: 
                    new_offers = new_offers[:5]  # Limit to the 5 most recent offers
                for offer in new_offers:
                    if site == 'otodom':
                        context.bot.send_message(
                            user_id,
                            f"New offer found on {site}!\n"
                            f"Title: {offer['title']}\n"
                            f"Price: {offer['price']}\n"
                            f"Location: {offer['location']}\n"
                            f"Area: {offer['area']}\n"
                            f"Rooms: {offer['room_count']}\n"
                            f"Floor: {offer['floor']}\n"
                            f"Link: {offer['link']}\n"
                        )
                    elif site == 'olx':
                        context.bot.send_message(
                            user_id,
                            f"New offer found on {site}!\n"
                            f"Title: {offer['title']}\n"
                            f"Price: {offer['price']}\n"
                            f"Location: {offer['location']}\n"
                            f"Updated: {offer['updated_date']}\n"
                            f"Area: {offer['area']}\n"
                            f"Link: {offer['link']}\n"
                        )
                # Update the last seen offer for this site
                user_data[user_id][f'last_seen_offer_{site}'] = new_offers[0]['link']
            else:
                print(f"No new offers found on {site}.")

    print("Finished checking all sites.")


def start_periodic_check(update: Update, context: CallbackContext) -> None:
    """Starts the periodic job for checking new offers."""
    
    if update.message:
        user_id = update.message.from_user.id
        user_name = update.message.from_user.first_name
    else:
        user_id = update.callback_query.from_user.id
        user_name = update.callback_query.from_user.first_name


    #check if the user already started the periodic check
    current_jobs = context.job_queue.get_jobs_by_name(str(user_id))
    if current_jobs:
        context.bot.send_message(user_id, "I'm already checking for new offers.")
        return
    context.bot.send_message(user_id, "I'll start checking for new offers every 10 minutes.", reply_markup=stop_monitoring_markup)

    print("Starting periodic check for user", user_name)
    # Start a job that checks for new offers every 10 minutes
    job_queue = context.job_queue
    # Function to execute immediately
    def run_now(context: CallbackContext):
        check_new_offers(context)

    # Start a job that checks for new offers immediately
    job_queue = context.job_queue
    job_queue.run_once(run_now, when=0, context={'user_id': user_id})
    # Run the job every 10 minutes (including right now)
    job_queue.run_repeating(check_new_offers, interval=600, first=0, context={'user_id': user_id}, name=str(user_id))

def stop_periodic_check(update: Update, context: CallbackContext) -> None:
    """Stops the periodic job for checking new offers."""
    if update.message:
        user_id = update.message.from_user.id
        user_name = update.message.from_user.first_name
    else:
        user_id = update.callback_query.from_user.id
        user_name = update.callback_query.from_user.first_name

    context.bot.send_message(user_id, "I've stopped checking for new offers.", reply_markup=start_menu_markup)

    # Remove the job associated with this user_id
    current_jobs = context.job_queue.get_jobs_by_name(str(user_id))

    # Remove last seen offers
    user_data[user_id]['last_seen_offer_olx'] = None
    user_data[user_id]['last_seen_offer_otodom'] = None


    for job in current_jobs:
        print(f'Removing job {job}')
        job.schedule_removal()

def room_selection_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    chat_id = query.message.chat_id if query else update.message.chat_id
    user_id = query.from_user.id if query else update.message.from_user.id

    # Retrieve selected rooms or initialize
    selected_rooms = user_data[user_id]['selected_rooms']

    # Create the inline keyboard
    keyboard = [
        [InlineKeyboardButton(f"1 Room {'✅' if 1 in selected_rooms else '❌'}", callback_data='room_1')],
        [InlineKeyboardButton(f"2 Rooms {'✅' if 2 in selected_rooms else '❌'}", callback_data='room_2')],
        [InlineKeyboardButton(f"3 Rooms {'✅' if 3 in selected_rooms else '❌'}", callback_data='room_3')],
        [InlineKeyboardButton(f"4+ Rooms {'✅' if 4 in selected_rooms else '❌'}", callback_data='room_4')],
        [InlineKeyboardButton("Confirm", callback_data='confirm_rooms')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        query.edit_message_text("Select the number of rooms you want:", reply_markup=reply_markup)
    else:
        context.bot.send_message(chat_id, "Select the number of rooms you want:", reply_markup=reply_markup)

def room_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    room_number = int(query.data.split('_')[1])  # Extract the room number from callback data
    user_id = query.from_user.id
    selected_rooms = user_data[user_id]['selected_rooms']
    print(f'User {user_id} selected {room_number} rooms.')
    # Toggle selection
    if room_number in selected_rooms:
        selected_rooms.remove(room_number)
    else:
        selected_rooms.append(room_number)

    user_data[user_id]['selected_rooms'] = selected_rooms
    room_selection_menu(update, context)

def confirm_room_selection(update: Update, context: CallbackContext):
    user_id = update.callback_query.from_user.id
    selected_rooms = user_data[user_id]['selected_rooms']
    room_list = ', '.join(f'{room} room(s)' for room in sorted(selected_rooms))
    context.bot.send_message(update.effective_chat.id, f"You have selected: {room_list}.")

def start_room_selection(update: Update, context: CallbackContext):
    room_selection_menu(update, context)

def main() -> None:
    load_dotenv()
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    updater = Updater(token)
    print(f'Bot started with token {token}')
    job_queue = updater.job_queue

    # Get the dispatcher to register handlers
    # Then, we register each handler and the conditions the update must meet to trigger it
    dispatcher = updater.dispatcher

        # Register handler for inline buttons

    price_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex(f'^{BTN_PRICE_RANGE}$'), set_price_start)],
        states={
            MIN_PRICE: [MessageHandler(Filters.text & ~Filters.command & ~Filters.regex(f'^{BTN_CANCEL}$'), set_min_price)],
            MAX_PRICE: [MessageHandler(Filters.text & ~Filters.command & ~Filters.regex(f'^{BTN_CANCEL}$'), set_max_price)],
        },
        fallbacks=[CommandHandler('cancel', cancel), MessageHandler(Filters.regex(f'^{BTN_CANCEL}$'), cancel)]
    )

    area_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex(f'^{BTN_AREA_RANGE}$'), set_area_start)],
        states={
            MIN_AREA: [MessageHandler(Filters.text & ~Filters.command & ~Filters.regex(f'^{BTN_CANCEL}$'), set_min_area)],
            MAX_AREA: [MessageHandler(Filters.text & ~Filters.command & ~Filters.regex(f'^{BTN_CANCEL}$'), set_max_area)],
        },
        fallbacks=[CommandHandler('cancel', cancel_area), MessageHandler(Filters.regex(f'^{BTN_CANCEL}$'), cancel)]
    )



    dispatcher.add_handler(CommandHandler('rooms', room_selection_menu))
    dispatcher.add_handler(CallbackQueryHandler(room_selection, pattern='^room_\\d$'))
    dispatcher.add_handler(CallbackQueryHandler(confirm_room_selection, pattern='^confirm_rooms$'))

    # Register commands
    # start - The /start command
    # menu - Show the menu
    # list - List available offer sources
    # set_price - Set the price range
    # set_area - Set the area range
    # get_filters - Get the current filters
    # get_offers - Get the latest offers
    # Register conversation handler
    dispatcher.add_handler(price_conv_handler)
    dispatcher.add_handler(area_conv_handler)
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("menu", start))
    dispatcher.add_handler(MessageHandler(Filters.regex(f'^{BTN_PRICE_RANGE}$'), set_price_start))
    dispatcher.add_handler(MessageHandler(Filters.regex(f'^{BTN_AREA_RANGE}$'), set_area_start))
    dispatcher.add_handler(MessageHandler(Filters.regex(f'^{BTN_OFFER_SOURCES}$'), site_list))
    dispatcher.add_handler(MessageHandler(Filters.regex(f'^{BTN_FILTERS}$'), get_filters))
    dispatcher.add_handler(MessageHandler(Filters.regex(f'^{BTN_START_MONITORING}$'), start_periodic_check))
    dispatcher.add_handler(MessageHandler(Filters.regex(f'^{BTN_STOP_MONITORING}$'), stop_periodic_check))
    dispatcher.add_handler(MessageHandler(Filters.regex(f'^{BTN_ROOMS}$'), start_room_selection))


    # # Echo any message that is not a command
    dispatcher.add_handler(MessageHandler(~Filters.command, echo))

    # dispatcher.add_handler(CommandHandler("start_check", start_periodic_check))
    # dispatcher.add_handler(CommandHandler("stop_check", stop_periodic_check))


        # Register conversation handler
    dispatcher.add_handler(price_conv_handler)
    dispatcher.add_handler(area_conv_handler)

    
    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()


if __name__ == '__main__':
    main()
