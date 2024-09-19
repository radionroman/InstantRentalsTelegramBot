import db_placeholder as db
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext




def room_selection_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    chat_id = query.message.chat_id if query else update.message.chat_id
    user_id = query.from_user.id if query else update.message.from_user.id

    # Retrieve selected rooms or initialize
    selected_rooms = db.user_data[user_id]['selected_rooms']

    # Create the inline keyboard
    keyboard = [
        [InlineKeyboardButton(f"1 Room {'✅' if 1 in selected_rooms else '❌'}", callback_data='room_1')],
        [InlineKeyboardButton(f"2 Rooms {'✅' if 2 in selected_rooms else '❌'}", callback_data='room_2')],
        [InlineKeyboardButton(f"3 Rooms {'✅' if 3 in selected_rooms else '❌'}", callback_data='room_3')],
        [InlineKeyboardButton(f"4+ Rooms {'✅' if 4 in selected_rooms else '❌'}", callback_data='room_4')],
        # [InlineKeyboardButton("Confirm", callback_data='confirm_rooms')],
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
    user_name = query.from_user.first_name
    selected_rooms = db.user_data[user_id]['selected_rooms']
    print(f'User {user_name} selected {room_number} rooms.') if db.user_data["verbose"] > 0 else None
    # Toggle selection
    if room_number in selected_rooms:
        selected_rooms.remove(room_number)
    else:
        selected_rooms.append(room_number)

    db.user_data[user_id]['selected_rooms'] = selected_rooms
    room_selection_menu(update, context)

def confirm_room_selection(update: Update, context: CallbackContext):
    user_id = update.callback_query.from_user.id
    selected_rooms = db.user_data[user_id]['selected_rooms']
    room_list = ', '.join(f'{room} room(s)' for room in sorted(selected_rooms))
    context.bot.send_message(update.effective_chat.id, f"You have selected: {room_list}.")

def start_room_selection(update: Update, context: CallbackContext):
    room_selection_menu(update, context)

