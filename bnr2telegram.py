import requests
import xml.etree.ElementTree as ET
from telegram import Bot
import asyncio
import argparse
import os
import logging
from typing import Optional

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
   level=log_level,
   format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get Telegram credentials from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')

async def send_to_telegram(message: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID environment variables must be set")

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    logger.debug("Sending message to Telegram")
    await bot.send_message(
        chat_id=TELEGRAM_CHANNEL_ID,
        text=message,
        parse_mode='HTML'
    )

async def fetch_and_send_rates(dry_run: bool = False, currencies: Optional[str] = None) -> None:
    # Convert currencies to uppercase set for easier lookup
    selected_currencies = {curr.strip().upper() for curr in currencies.split(',')} if currencies else None
    if selected_currencies:
        logger.debug(f"Filtering currencies: {', '.join(selected_currencies)}")

    # Fetch XML data
    url = os.getenv('EXCHANGE_RATES_URL', 'https://www.bnr.ro/nbrfxrates.xml')
    try:
        logger.debug("Fetching rates from BNR")
        response = requests.get(url)
        response.raise_for_status()
        xml_data = response.content
    except requests.RequestException as e:
        logger.error(f"Error fetching data: {e}")
        return

    try:
        # Remove the namespace to make parsing easier
        xml_data = xml_data.decode('utf-8')
        xml_data = xml_data.replace('xmlns="http://www.bnr.ro/xsd"', '')
        xml_data = xml_data.replace('xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"', '')
        xml_data = xml_data.replace('xsi:schemaLocation="http://www.bnr.ro/xsd nbrfxrates.xsd"', '')

        root = ET.fromstring(xml_data)

        # Get the date
        cube = root.find('.//Cube')
        date = cube.get('date')
        logger.debug(f"Processing rates for date {date}")

        # Format message
        message = f"🏦 BNR Exchange Rates - {date}\n\n"

        # Process each rate
        for rate in cube.findall('Rate'):
            currency = rate.get('currency')
            # Skip if we have a currency filter and this currency isn't in it
            if selected_currencies and currency not in selected_currencies:
                continue

            value = rate.text
            multiplier = rate.get('multiplier')

            if multiplier:
                message += f"{currency}: {float(value):,.4f} RON / {multiplier} units\n"
            else:
                message += f"{currency}: {float(value):,.4f} RON\n"

        if not message.strip():
            logger.warning("No matching currencies found")
            logger.info("Available currencies: %s", ' '.join(rate.get('currency') for rate in cube.findall('Rate')))
            return

        if dry_run:
            logger.info("Dry run - message content:\n%s", message)
        else:
            if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
                logger.error("TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID environment variables must be set")
                return
            await send_to_telegram(message)
            logger.info("Exchange rates sent successfully to Telegram channel")

    except Exception as e:
        logger.error(f"Error processing data: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fetch BNR exchange rates and send to Telegram')
    parser.add_argument('--dry-run', action='store_true', help='Print message instead of sending to Telegram')
    parser.add_argument('--currencies', help='Comma-separated list of currencies (e.g., USD,EUR,GBP)')
    args = parser.parse_args()

    asyncio.run(fetch_and_send_rates(dry_run=args.dry_run, currencies=args.currencies))
