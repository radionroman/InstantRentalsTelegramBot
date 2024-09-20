from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, MessageHandler, Filters
from src.utils.markups import cancel_markup, get_markup
from src.utils.constants import BTN_PRICE_RANGE, BTN_CANCEL
import db_placeholder as db


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

    print(f'user {user_name} started setting the price range') if db.user_data["verbose"] > 0 else None

    context.bot.send_message(user_id, "Please enter the minimum price in PLN.", reply_markup=cancel_markup)
    return MIN_PRICE

def set_min_price(update: Update, context: CallbackContext) -> int:
    """
    Stores the minimum price and asks for the maximum price.
    """
    try:
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

        
        db.user_data[user_id]['minimum_price'] = minimum_price
        db.user_data[user_id]['maximum_price'] = maximum_price

        context.bot.send_message(user_id, f"Price range set to {minimum_price} PLN - {maximum_price} PLN.", reply_markup=get_markup(db.user_data,user_id))
        db.user_data[user_id]['displayed_offers'] = set()
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

    context.bot.send_message(user_id, "Operation cancelled.", reply_markup=get_markup(db.user_data,user_id))
    return ConversationHandler.END

price_conv_handler = ConversationHandler(
    entry_points=[MessageHandler(Filters.regex(f'^{BTN_PRICE_RANGE}$'), set_price_start)],
    states={
        MIN_PRICE: [MessageHandler(Filters.text & ~Filters.command & ~Filters.regex(f'^{BTN_CANCEL}$'), set_min_price)],
        MAX_PRICE: [MessageHandler(Filters.text & ~Filters.command & ~Filters.regex(f'^{BTN_CANCEL}$'), set_max_price)],
    },
    fallbacks=[CommandHandler('cancel', cancel), MessageHandler(Filters.regex(f'^{BTN_CANCEL}$'), cancel)]
)
