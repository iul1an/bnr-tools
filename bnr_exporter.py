import requests
import xml.etree.ElementTree as ET
from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily
from threading import Lock
from datetime import datetime
import argparse
import time
import logging
import os

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lock for thread safety
fetch_lock = Lock()

class BNRCollector:
    def collect(self):
        with fetch_lock:
            rates, success, scrape_time, update_date = fetch_rates()

        logger.debug("Creating metrics from fetched data")
        # Create metrics
        rate_metric = GaugeMetricFamily('bnr_exchange_rate', 'Exchange rate from BNR', labels=['currency'])
        multiplier_metric = GaugeMetricFamily('bnr_exchange_rate_multiplier', 'Exchange rate multiplier from BNR', labels=['currency'])

        # Add rates to metrics
        for currency, (rate, multiplier) in rates.items():
            rate_metric.add_metric([currency], rate)
            multiplier_metric.add_metric([currency], multiplier)

        # Create and add other metrics
        success_metric = GaugeMetricFamily('bnr_scrape_success', 'Whether the last scrape was successful')
        success_metric.add_metric([], success)

        scrape_metric = GaugeMetricFamily('bnr_last_scrape_timestamp', 'Last scrape timestamp')
        scrape_metric.add_metric([], scrape_time)

        update_metric = GaugeMetricFamily('bnr_last_update_date', 'Last BNR update date as unix timestamp')
        update_metric.add_metric([], update_date)

        return [rate_metric, multiplier_metric, success_metric, scrape_metric, update_metric]

def fetch_rates():
    rates = {}
    success = 0
    scrape_time = time.time()
    update_date = 0

    url = 'https://www.bnr.ro/nbrfxrates.xml'
    try:
        logger.debug("Fetching rates from BNR")
        response = requests.get(url)
        response.raise_for_status()
        xml_data = response.content

        # Remove the namespace to make parsing easier
        xml_data = xml_data.decode('utf-8')
        xml_data = xml_data.replace('xmlns="http://www.bnr.ro/xsd"', '')
        xml_data = xml_data.replace('xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"', '')
        xml_data = xml_data.replace('xsi:schemaLocation="http://www.bnr.ro/xsd nbrfxrates.xsd"', '')

        root = ET.fromstring(xml_data)
        cube = root.find('.//Cube')
        current_date = cube.get('date')

        # Process each rate
        for rate in root.findall('.//Rate'):
            currency = rate.get('currency')
            value = float(rate.text)
            multiplier = rate.get('multiplier')

            if multiplier:
                multiplier = float(multiplier)
                rates[currency] = (value * multiplier, multiplier)
            else:
                rates[currency] = (value, 1)

        success = 1
        update_date = datetime.strptime(current_date, '%Y-%m-%d').timestamp()
        logger.debug(f"Successfully updated rates for date {current_date}")

    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        success = 0

    return rates, success, scrape_time, update_date

def main(port):
    from prometheus_client.core import REGISTRY
    REGISTRY.register(BNRCollector())

    start_http_server(port)
    logger.info(f"Prometheus metrics server started on port {port}")

    # Keep the script running
    import signal
    signal.pause()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='BNR Exchange Rates Prometheus Exporter')
    parser.add_argument('--port', type=int, default=8000, help='Port to serve metrics on')
    args = parser.parse_args()

    main(args.port)
