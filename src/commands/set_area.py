from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, MessageHandler, Filters
from src.utils.markups import cancel_markup, get_markup
from src.utils.constants import BTN_AREA_RANGE, BTN_CANCEL
import db_placeholder as db

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
        db.user_data[user_id]['area_min'] = minimum_area
        db.user_data[user_id]['area_max'] = maximum_area

        update.message.reply_text(f"Area range set to {minimum_area} m² - {maximum_area} m².", reply_markup=get_markup(db.user_data,user_id))
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

    context.bot.send_message(user_id, "Operation cancelled.", reply_markup=get_markup(db.user_data,user_id))
    return ConversationHandler.END

area_conv_handler = ConversationHandler(
    entry_points=[MessageHandler(Filters.regex(f'^{BTN_AREA_RANGE}$'), set_area_start)],
    states={
        MIN_AREA: [MessageHandler(Filters.text & ~Filters.command & ~Filters.regex(f'^{BTN_CANCEL}$'), set_min_area)],
        MAX_AREA: [MessageHandler(Filters.text & ~Filters.command & ~Filters.regex(f'^{BTN_CANCEL}$'), set_max_area)],
    },
    fallbacks=[CommandHandler('cancel', cancel_area), MessageHandler(Filters.regex(f'^{BTN_CANCEL}$'), cancel_area)]
)