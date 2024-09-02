import db_placeholder as db
from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from src.utils.constants import offer_sources


def get_offer_sources(update: Update, context: CallbackContext) -> None:
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
