import logging
import os
import requests
from bs4 import BeautifulSoup
from otodom_scrapper import scrape_otodom
from olx_scrapper import scrape_olx

from dotenv import load_dotenv
from collections import defaultdict
from telegram import Update, ForceReply, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
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
    'last_seen_offer_otodom': None
}

user_data = defaultdict(lambda: DEFAULT_USER_DATA.copy())

# Pre-assign menu text
FIRST_MENU = "<b>Menu 1</b>\n\nA beautiful menu with a shiny inline button."
SECOND_MENU = "<b>Menu 2</b>\n\nA better menu with even more shiny inline buttons."

# Pre-assign button text
NEXT_BUTTON = "Next"
BACK_BUTTON = "Back"
TUTORIAL_BUTTON = "Tutorial"

# Build keyboards
FIRST_MENU_MARKUP = InlineKeyboardMarkup([[
    InlineKeyboardButton(NEXT_BUTTON, callback_data=NEXT_BUTTON)
]])
SECOND_MENU_MARKUP = InlineKeyboardMarkup([
    [InlineKeyboardButton(BACK_BUTTON, callback_data=BACK_BUTTON)],
    [InlineKeyboardButton(TUTORIAL_BUTTON, url="https://core.telegram.org/bots/api")]
])

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


# def get_offers(update: Update, context: CallbackContext) -> None:
#     """
#     This function fetches the latest rental offers within the price range and sends them to the user.
#     """

#     user_id = update.message.from_user.id  
#     minimum_price = user_data[user_id]['minimum_price']
#     maximum_price = user_data[user_id]['maximum_price']
#     owner_type = user_data[user_id]['owner_type']
#     view_type = user_data[user_id]['view_type']
#     limit = user_data[user_id]['limit']
#     area_min = user_data[user_id]['area_min']
#     area_max = user_data[user_id]['area_max']
#     rooms_number = user_data[user_id]['rooms_number']
#     by = user_data[user_id]['by']
#     direction = user_data[user_id]['direction']
#     days = user_data[user_id]['days']


#     offers = scrape_otodom({'min_price': minimum_price, 'max_price': maximum_price, 'owner_type': owner_type, 'view_type': view_type, 'limit': limit, 'area_min': area_min, 'area_max': area_max, 'rooms_number': rooms_number, 'by': by, 'direction': direction, 'days': days})

#     update.message.reply_text("Fetching the latest offers... with filters:\n min_price: " + str(minimum_price) + "\n max_price: " + str(maximum_price) + "\n owner_type: " + owner_type + "\n view_type: " + view_type + "\n limit: " + limit + "\n area_min: " + area_min + "\n area_max: " + area_max + "\n rooms_number: " + rooms_number + "\n by: " + by + "\n direction: " + direction + "\n days: " + days)

#     if not offers:
#         update.message.reply_text("No offers found within your price range.")
#     else:
#         update.message.reply_text(f"Found {len(offers)} offers within your price range.")
#         i = 10
#         for offer in offers:
#             update.message.reply_text(
#                 f"{offer['title']}\n"
#                 f"Price: {offer['price']}\n"
#                 f"Location: {offer['location']}\n"
#                 f"Room count: {offer['room_count']}\n"
#                 f"Area: {offer['area']}\n"
#                 f"Floor: {offer['floor']}\n"
#                 f"Link: {offer['link']}\n"
#             )
#             i -= 1
#             if i == 0:
#                 break


# def start(update: Update, context: CallbackContext) -> None:
#     """
#     This function handles the /start command
#     """

#     settings = user_data[update.message.from_user.id]
#     context.bot.send_message(
#         update.message.chat_id,
#         "Hello! I'm a bot that will notify you of new rental offers in your location. \n"
#         "Use /start_check to start checking for new offers every 10 minutes.\n"
#         "Use /stop_check to stop checking for new offers.\n"
#         "Use /get_offers to get the latest offers within your price range.\n"
#         "Use /set_price to set the price range of offers you are interested in.\n"
#         "Use /set_area to set the area range of offers you are interested in.\n"
#         "Use /get_filters to see the current filters.\n"
#         "Use /list to see the available offer sources.\n"
#     )

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

def set_price_range(update: Update, context: CallbackContext) -> None:
    """
    This function sets the minimum and maximum price for the offers
    """

    user_id = update.message.from_user.id

    # Get the text from the message
    text = update.message.text

    # Split the text into a list of words
    words = text.split()

    # Check if the message has at least 3 words
    if len(words) < 3:
        context.bot.send_message(
            update.message.chat_id,
            "Please provide both the minimum and maximum price in pln: /set_price <minimum_price> <maximum_price>"
        )
        return

    # Try to convert the words to integers
    try:
        minimum_price = int(words[1])
        maximum_price = int(words[2])
    except ValueError:
        context.bot.send_message(
            update.message.chat_id,
            "Please provide valid numbers for the price range in pln: /set_price <minimum_price> <maximum_price>"
        )
        return

    context.bot.send_message(
        update.message.chat_id,
        f"Price range set to {minimum_price} pln - {maximum_price} pln."
        
    )

    user_data[user_id]['minimum_price'] = minimum_price
    user_data[user_id]['maximum_price'] = maximum_price
    print(f'User {update.message.from_user.id} set the price range to {minimum_price} pln - {maximum_price} pln.')

def get_price_range(update: Update, context: CallbackContext) -> None:
    """
    This function shows the current price range
    """
    if update.message:
        user_id = update.message.from_user.id
        user_name = update.message.from_user.first_name
    else:
        user_id = update.callback_query.from_user.id
        user_name = update.callback_query.from_user.first_name


    minimum_price = user_data[user_id]['minimum_price']
    maximum_price = user_data[user_id]['maximum_price']

    print(f'User {user_name} requested the price range')

    context.bot.send_message(
        user_id,
        f"Current price range: {minimum_price} pln - {maximum_price} pln."
    )

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Welcome! Use /menu to see available options.")

def menu(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [
            InlineKeyboardButton("List Offer Sources", callback_data='list'),
            InlineKeyboardButton("Show Filters", callback_data='get_filters'),
            
        ],
        [
            InlineKeyboardButton("Set Price Range", callback_data='set_price'),
            InlineKeyboardButton("Set Area Range", callback_data='set_area'),
            
        ],
        [
            InlineKeyboardButton("Start Monitoring", callback_data='start_check'),
            InlineKeyboardButton("Stop Monitoring", callback_data='stop_check'),
        ],
       
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose an option:', reply_markup=reply_markup)

def button_tap(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if query.data == 'list':
        site_list(update, context)
    elif query.data == 'set_price':
        context.bot.send_message(query.message.chat_id, "Please use the /set_price command to set the price range.")
    elif query.data == 'set_area':
        context.bot.send_message(query.message.chat_id, "Please use the /set_area command to set the area range.")
    elif query.data == 'get_filters':
        get_filters(update, context)
    elif query.data == 'start_check':
        start_periodic_check(update, context)
    elif query.data == 'stop_check':
        stop_periodic_check(update, context)



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

    context.bot.send_message(user_id, "Please enter the minimum price in PLN.")
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

        context.bot.send_message(user_id, f"Price range set to {minimum_price} PLN - {maximum_price} PLN.")
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

    context.bot.send_message(user_id, "Operation cancelled.")
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

    context.bot.send_message(user_id, "Please enter the minimum area in square meters.")
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

        update.message.reply_text(f"Area range set to {minimum_area} m² - {maximum_area} m².")
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


    context.bot.send_message(user_id, "Operation cancelled.")
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

    print(f'User {user_name} requested the filters')

    context.bot.send_message(
        user_id,
        f"Current filters:\n"
        f"Price range: {minimum_price} PLN - {maximum_price} PLN\n"
        f"Area range: {area_min} m² - {area_max} m²"
        
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
    context.bot.send_message(user_id, "I'll start checking for new offers every 10 minutes.")

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

    context.bot.send_message(user_id, "I've stopped checking for new offers.")

    # Remove the job associated with this user_id
    current_jobs = context.job_queue.get_jobs_by_name(str(user_id))

    # Remove last seen offers
    user_data[user_id]['last_seen_offer_olx'] = None
    user_data[user_id]['last_seen_offer_otodom'] = None
    

    for job in current_jobs:
        print(f'Removing job {job}')
        job.schedule_removal()

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
    dispatcher.add_handler(CallbackQueryHandler(button_tap))

    price_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('set_price', set_price_start)],
        states={
            MIN_PRICE: [MessageHandler(Filters.text & ~Filters.command, set_min_price)],
            MAX_PRICE: [MessageHandler(Filters.text & ~Filters.command, set_max_price)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    area_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('set_area', set_area_start)],
        states={
            MIN_AREA: [MessageHandler(Filters.text & ~Filters.command, set_min_area)],
            MAX_AREA: [MessageHandler(Filters.text & ~Filters.command, set_max_area)],
        },
        fallbacks=[CommandHandler('cancel', cancel_area)]
    )

    


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
    dispatcher.add_handler(CommandHandler("menu", menu))
    dispatcher.add_handler(CommandHandler("list", site_list))
    dispatcher.add_handler(CommandHandler("get_filters", get_filters))
    # dispatcher.add_handler(CommandHandler("get_offers", get_offers))



    # Echo any message that is not a command
    dispatcher.add_handler(MessageHandler(~Filters.command, echo))

    dispatcher.add_handler(CommandHandler("start_check", start_periodic_check))
    dispatcher.add_handler(CommandHandler("stop_check", stop_periodic_check))

        # Register conversation handler
    dispatcher.add_handler(price_conv_handler)
    dispatcher.add_handler(area_conv_handler)

    
    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()


if __name__ == '__main__':
    main()
