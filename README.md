
# Real Estate Scraper Telegram Bot

## Overview

This Telegram bot allows users to monitor real estate offers from popular websites like Otodom, OLX, and Nieruchomosci Online. Users can set specific filters for price range, area, and number of rooms, and the bot will periodically scrape these websites for new listings that match the criteria. The bot also provides a menu for users to interactively manage their filters, start or stop monitoring, and view available offer sources.

## Features

- **Start Monitoring:** Initiate periodic checks for new real estate offers based on the user's filters.
- **Stop Monitoring:** Halt the periodic checks.
- **Set Filters:** Users can set price ranges, area ranges, and the number of rooms for the offers they want to monitor.
- **View Offer Sources:** Display the list of websites from which the bot scrapes real estate offers.
- **Room Selection:** Interactive menu to select the number of rooms.
- **Scraping:** Gather real estate offers from Otodom, OLX, and Nieruchomosci Online.

## Installation

### Prerequisites

- Python 3.8+
- Telegram Bot API Token

### Setup

1. **Clone the Repository**
    ```bash
    git clone https://github.com/yourusername/real-estate-scraper-bot.git
    cd real-estate-scraper-bot
    ```

2. **Create a Virtual Environment**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4. **Set Up Environment Variables**
    - Create a `.env` file in the project root directory.
    - Add your Telegram bot token in the `.env` file:
    ```plaintext
    TELEGRAM_BOT_TOKEN=your-telegram-bot-token
    ```

5. **Run the Bot**
    ```bash
    python bot.py
    ```

## Usage

- **/start**: Start interacting with the bot and receive the main menu.
- **Set Filters**: Set price range, area, and the number of rooms using interactive menus.
- **Start Monitoring**: Begin receiving updates about new real estate offers that match your filters.
- **Stop Monitoring**: Stop receiving updates about new offers.
- **View Offer Sources**: See a list of real estate websites the bot scrapes.

## Project Structure

The project is structured as follows:

- **`instant_rentals_bot.py`**: Main script to run the Telegram bot.



## Contact

For any issues or questions, please open an issue in this repository or contact [radionroman@gmail.com](mailto:radionroman@gmail.com).

