import db_placeholder as db
from telegram import Update
from telegram.ext import CallbackContext
from src.utils.markups import start_menu_markup, stop_monitoring_markup
from src.scrappers.nieruchomosci_online_scrapper import scrape_nieruchomosci
from src.scrappers.olx_scrapper import scrape_olx
from src.scrappers.otodom_scrapper import scrape_otodom



def check_new_offers(context: CallbackContext):
    """This function is run periodically to check for new offers."""

    try:
        job = context.job
        user_id = job.context['user_id']
        user_name = context.bot.get_chat(user_id).first_name

        # Extract user-specific filter parameters
        filters = {
            'min_price': db.user_data[user_id]['minimum_price'],
            'max_price': db.user_data[user_id]['maximum_price'],
            'owner_type': db.user_data[user_id]['owner_type'],
            'view_type': db.user_data[user_id]['view_type'],
            'limit': db.user_data[user_id]['limit'],
            'area_min': db.user_data[user_id]['area_min'],
            'area_max': db.user_data[user_id]['area_max'],
            'selected_rooms': db.user_data[user_id]['selected_rooms'],
            'by': db.user_data[user_id]['by'],
            'direction': db.user_data[user_id]['direction'],
            'days': db.user_data[user_id]['days'],
            'offer_type': db.user_data[user_id]['offer_type']

        }

        # Initialize the sites and corresponding scraping functions
        sites = {
            'otodom': scrape_otodom,
            'olx': scrape_olx,
            'nieruchomosci_online': scrape_nieruchomosci,
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
                last_seen_offer = db.user_data[user_id].get(f'last_seen_offer_{site}')

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
                        elif site == 'nieruchomosci_online':
                            print(offer)
                            context.bot.send_message(
                                user_id,
                                f"New offer found on {site}!\n"
                                f"Title: {offer['title']}\n"
                                f"Price: {offer['price']}\n"
                                f"Location: {offer['location']}\n"
                                f"Area: {offer['area']}\n"
                                f"Link: {offer['link']}\n"
                            )
                    # Update the last seen offer for this site
                    db.user_data[user_id][f'last_seen_offer_{site}'] = new_offers[0]['link']
                else:
                    print(f"No new offers found on {site}.")

        print("Finished checking all sites.")
    except Exception as e:
        print(f"An error occurred: {e}")
        


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
    db.user_data[user_id]['last_seen_offer_olx'] = None
    db.user_data[user_id]['last_seen_offer_otodom'] = None
    db.user_data[user_id]['last_seen_offer_nieruchomosci_online'] = None


    for job in current_jobs:
        print(f'Removing job {job}')
        job.schedule_removal()