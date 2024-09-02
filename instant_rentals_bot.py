import logging
import os
import requests
from bs4 import BeautifulSoup

from src.commands.set_area import area_conv_handler, set_area_start
from src.commands.set_price import price_conv_handler, set_price_start
from src.commands.room_selection import room_selection, start_room_selection, confirm_room_selection
from src.commands.get_filters import get_filters
from src.commands.get_offer_sources import get_offer_sources
from src.commands.monitoring import start_periodic_check, stop_periodic_check

from dotenv import load_dotenv
from collections import defaultdict
from telegram import Update, ForceReply, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler, ConversationHandler, JobQueue
from datetime import datetime, timedelta
from src.utils.constants import *
from src.utils.markups import cancel_markup, get_markup, start_menu_markup, stop_monitoring_markup
import db_placeholder as db

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

def echo(update: Update, context: CallbackContext) -> None:
    """
    This function would be added to the dispatcher as a handler for messages coming from the Bot API
    """
    # Print to console
    print(f'{update.message.from_user.first_name} wrote {update.message.text}')
    update.message.reply_text("I'm sorry, I'm not sure what you mean. Please use the /menu command to see the available options.")


def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text( "Please choose an action", reply_markup=get_markup(db.user_data, update.message.from_user.id))


def offer_type_switch(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    db.user_data[user_id]['offer_type'] = 'rent' if db.user_data[user_id]['offer_type'] == 'sale' else 'sale'
    context.bot.send_message(user_id, f"Offer type switched to {db.user_data[user_id]['offer_type']}.", reply_markup=get_markup(db.user_data,user_id))



def main() -> None:
    load_dotenv()
    token = os.getenv('TELEGRAM_BOT_TOKEN')


    updater = Updater(token)
    print(f'Bot started with token {token}')
    job_queue = updater.job_queue

    # Get the dispatcher to register handlers
    # Then, we register each handler and the conditions the update must meet to trigger it
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(room_selection, pattern='^room_\\d$'))
    dispatcher.add_handler(CallbackQueryHandler(confirm_room_selection, pattern='^confirm_rooms$'))
    dispatcher.add_handler(price_conv_handler)
    dispatcher.add_handler(area_conv_handler)
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("menu", start))
    dispatcher.add_handler(MessageHandler(Filters.regex(f'^{BTN_PRICE_RANGE}$'), set_price_start))
    dispatcher.add_handler(MessageHandler(Filters.regex(f'^{BTN_AREA_RANGE}$'), set_area_start))
    dispatcher.add_handler(MessageHandler(Filters.regex(f'^{BTN_OFFER_SOURCES}$'), get_offer_sources))
    dispatcher.add_handler(MessageHandler(Filters.regex(f'^{BTN_FILTERS}$'), get_filters))
    dispatcher.add_handler(MessageHandler(Filters.regex(f'^{BTN_START_MONITORING}$'), start_periodic_check))
    dispatcher.add_handler(MessageHandler(Filters.regex(f'^{BTN_STOP_MONITORING}$'), stop_periodic_check))
    dispatcher.add_handler(MessageHandler(Filters.regex(f'^{BTN_ROOMS}$'), start_room_selection))
    dispatcher.add_handler(MessageHandler(Filters.regex(f'^{BTN_OFFER_TYPE}$'), offer_type_switch))
    dispatcher.add_handler(MessageHandler(~Filters.command, echo))
    
    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()


if __name__ == '__main__':
    db.init()
    main()
