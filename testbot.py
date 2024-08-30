import logging
import os
import requests
from bs4 import BeautifulSoup
from otodom_scrapper import scrape_otodom

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
    'last_seen_offer': None
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


def get_offers(update: Update, context: CallbackContext) -> None:
    """
    This function fetches the latest rental offers within the price range and sends them to the user.
    """

    user_id = update.message.from_user.id  
    minimum_price = user_data[user_id]['minimum_price']
    maximum_price = user_data[user_id]['maximum_price']
    owner_type = user_data[user_id]['owner_type']
    view_type = user_data[user_id]['view_type']
    limit = user_data[user_id]['limit']
    area_min = user_data[user_id]['area_min']
    area_max = user_data[user_id]['area_max']
    rooms_number = user_data[user_id]['rooms_number']
    by = user_data[user_id]['by']
    direction = user_data[user_id]['direction']
    days = user_data[user_id]['days']


    offers = scrape_otodom({'min_price': minimum_price, 'max_price': maximum_price, 'owner_type': owner_type, 'view_type': view_type, 'limit': limit, 'area_min': area_min, 'area_max': area_max, 'rooms_number': rooms_number, 'by': by, 'direction': direction, 'days': days})

    update.message.reply_text("Fetching the latest offers... with filters:\n min_price: " + str(minimum_price) + "\n max_price: " + str(maximum_price) + "\n owner_type: " + owner_type + "\n view_type: " + view_type + "\n limit: " + limit + "\n area_min: " + area_min + "\n area_max: " + area_max + "\n rooms_number: " + rooms_number + "\n by: " + by + "\n direction: " + direction + "\n days: " + days)

    if not offers:
        update.message.reply_text("No offers found within your price range.")
    else:
        i = 10
        for offer in offers:
            update.message.reply_text(
                f"{offer['title']}\n"
                f"Price: {offer['price']}\n"
                f"Location: {offer['location']}\n"
                f"Room count: {offer['room_count']}\n"
                f"Area: {offer['area']}\n"
                f"Floor: {offer['floor']}\n"
                f"Link: {offer['link']}\n"
            )
            i -= 1
            if i == 0:
                break


def start(update: Update, context: CallbackContext) -> None:
    """
    This function handles the /start command
    """

    settings = user_data[update.message.from_user.id]
    context.bot.send_message(
        update.message.chat_id,
        "Hello! I'm a bot that will notify you of new rental offers in your location. \n"
        "Use /set_price to set the price range of offers you are interested in, and /get_price to check current price range.\n"
        "Use /list to see the available offer sources.\n"
        "Use /set_location to set your location (For now only Warsaw).\n"
        "Use /get_offers to get the latest offers within your price range.\n"
    )

def echo(update: Update, context: CallbackContext) -> None:
    """
    This function would be added to the dispatcher as a handler for messages coming from the Bot API
    """

    # Print to console
    print(f'{update.message.from_user.first_name} wrote {update.message.text}')
    update.message.copy(update.message.chat_id)


def site_list(update: Update, context: CallbackContext) -> None:
    """
    This function shows a list of available offer sources
    """
    print(f'user {update.message.from_user.first_name} requested the list of offer sources')
    context.bot.send_message(
        update.message.chat_id,
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
    user_id = update.message.from_user.id

    minimum_price = user_data[user_id]['minimum_price']
    maximum_price = user_data[user_id]['maximum_price']

    print(f'User {update.message.from_user.id} requested the price range')

    context.bot.send_message(
        update.message.chat_id,
        f"Current price range: {minimum_price} pln - {maximum_price} pln."
    )

def menu(update: Update, context: CallbackContext) -> None:
    """
    This handler sends a menu with the inline buttons we pre-assigned above
    """

    context.bot.send_message(
        update.message.from_user.id,
        FIRST_MENU,
        parse_mode=ParseMode.HTML,
        reply_markup=FIRST_MENU_MARKUP
    )


def button_tap(update: Update, context: CallbackContext) -> None:
    """
    This handler processes the inline buttons on the menu
    """

    data = update.callback_query.data
    text = ''
    markup = None

    if data == NEXT_BUTTON:
        text = SECOND_MENU
        markup = SECOND_MENU_MARKUP
    elif data == BACK_BUTTON:
        text = FIRST_MENU
        markup = FIRST_MENU_MARKUP

    # Close the query to end the client-side loading animation
    update.callback_query.answer()

    # Update message content with corresponding menu section
    update.callback_query.message.edit_text(
        text,
        ParseMode.HTML,
        reply_markup=markup
    )



MIN_PRICE, MAX_PRICE = range(2)

def set_price_start(update: Update, context: CallbackContext) -> int:
    """
    Initiates the conversation for setting the price range.
    """
    update.message.reply_text("Please enter the minimum price in PLN.")
    return MIN_PRICE

def set_min_price(update: Update, context: CallbackContext) -> int:
    """
    Stores the minimum price and asks for the maximum price.
    """
    try:
        minimum_price = int(update.message.text)
        context.user_data['minimum_price'] = minimum_price
        update.message.reply_text("Now, please enter the maximum price in PLN.")
        return MAX_PRICE
    except ValueError:
        update.message.reply_text("Please enter a valid number for the minimum price.")
        return MIN_PRICE

def set_max_price(update: Update, context: CallbackContext) -> int:
    """
    Stores the maximum price and ends the conversation.
    """
    try:
        maximum_price = int(update.message.text)
        minimum_price = context.user_data['minimum_price']

        if maximum_price < minimum_price:
            update.message.reply_text("Maximum price should be greater than or equal to minimum price. Please enter the maximum price again.")
            return MAX_PRICE

        user_id = update.message.from_user.id
        user_data[user_id]['minimum_price'] = minimum_price
        user_data[user_id]['maximum_price'] = maximum_price

        update.message.reply_text(f"Price range set to {minimum_price} PLN - {maximum_price} PLN.")
        return ConversationHandler.END
    except ValueError:
        update.message.reply_text("Please enter a valid number for the maximum price.")
        return MAX_PRICE

def cancel(update: Update, context: CallbackContext) -> int:
    """
    Cancels the conversation.
    """
    update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END


MIN_AREA, MAX_AREA = range(2)

def set_area_start(update: Update, context: CallbackContext) -> int:
    """
    Initiates the conversation for setting the area range.
    """
    update.message.reply_text("Please enter the minimum area in square meters.")
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
    update.message.reply_text("Area setting cancelled.")
    return ConversationHandler.END

def get_filters(update: Update, context: CallbackContext) -> None:
    """
    This function shows the current filters set by the user
    """
    user_id = update.message.from_user.id

    minimum_price = user_data[user_id]['minimum_price']
    maximum_price = user_data[user_id]['maximum_price']
    area_min = user_data[user_id]['area_min']
    area_max = user_data[user_id]['area_max']

    print(f'User {update.message.from_user.id} requested the filters')

    context.bot.send_message(
        update.message.chat_id,
        f"Current filters:\n"
        f"Price range: {minimum_price} PLN - {maximum_price} PLN\n"
        f"Area range: {area_min} m² - {area_max} m²"
        
    )

def main() -> None:
    load_dotenv()
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    updater = Updater(token)
    print(f'Bot started with token {token}')
    # Get the dispatcher to register handlers
    # Then, we register each handler and the conditions the update must meet to trigger it
    dispatcher = updater.dispatcher

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

    

    # Register conversation handler
    dispatcher.add_handler(price_conv_handler)
    dispatcher.add_handler(area_conv_handler)

    # Register commands
    # start - The /start command
    # menu - Show the menu
    # list - List available offer sources
    # set_price - Set the price range
    # set_area - Set the area range
    # get_filters - Get the current filters
    # get_offers - Get the latest offers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("menu", menu))
    dispatcher.add_handler(CommandHandler("list", site_list))
    # dispatcher.add_handler(CommandHandler("set_price", set_price_range))
    dispatcher.add_handler(CommandHandler("get_filters", get_filters))
    dispatcher.add_handler(CommandHandler("get_offers", get_offers))

    # Register handler for inline buttons
    dispatcher.add_handler(CallbackQueryHandler(button_tap))

    # Echo any message that is not a command
    dispatcher.add_handler(MessageHandler(~Filters.command, echo))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()


if __name__ == '__main__':
    main()
