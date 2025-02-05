# bnr-tools

Tools for working with Romanian National Bank (BNR) exchange rates.

![](stonks.gif)

## Features

- **Telegram Notifications**: Send daily exchange rates to a Telegram channel
- **Prometheus Metrics**: Export exchange rates as Prometheus metrics

## Installation

```bash
# Clone the repository
git clone https://github.com/iul1an/bnr-tools.git
cd bnr-tools
```

Install dependencies locally
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

OR

Using docker:
```bash
docker build -t bnr-tools ./
```

## Tools

### bnr2telegram.py

Sends BNR exchange rates to a Telegram channel.

#### Configuration

Set the following environment variables:
```bash
export TELEGRAM_BOT_TOKEN='your_bot_token'
export TELEGRAM_CHANNEL_ID='@your_channel_name' # or channel ID like '-1001234567890'
```

#### Usage

Using Python:
```bash
# Send all rates
python bnr2telegram.py

# Send specific currencies
python bnr2telegram.py --currencies EUR,USD,GBP

# Test mode (prints to console instead of sending to Telegram)
python bnr2telegram.py --dry-run --currencies EUR,USD
```

Using Docker:
```bash
docker run --rm --name bnr2telegram \
  -e TELEGRAM_BOT_TOKEN='your_bot_token' \
  -e TELEGRAM_CHANNEL_ID='@your_channel_name' \
  bnr-tools bnr2telegram.py --currencies USD,EUR,GBP
```

### bnr_exporter.py

Prometheus exporter for BNR exchange rates.

#### Usage

Using Python:
```bash
# Start the exporter on default port 8000
python bnr_exporter.py

# Use custom port
python bnr_exporter.py --port 9100
```

Using Docker:
```bash
docker run -d -p 9100:8000 --name bnr_exporter bnr-tools bnr_exporter.py
```

#### Prometheus Configuration

Add this to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: bnr_exchange_rates
    scrape_interval: 1d # scrape once a day
    scrape_timeout: 10s
    static_configs:
      - targets: ['localhost:9100']
```

#### Available Metrics

```
# Exchange rates
bnr_exchange_rate{currency="EUR"} 4.9766
bnr_exchange_rate{currency="USD"} 4.7728

# Multipliers (some currencies like HUF use different units)
bnr_exchange_rate_multiplier{currency="EUR"} 1.0
bnr_exchange_rate_multiplier{currency="HUF"} 100.0

# Scrape status
bnr_scrape_success 1.0
bnr_last_scrape_timestamp 1707147600.0
bnr_last_update_date 1707147600.0
```


## Data Source

Exchange rates are fetched from BNR's official XML feed: https://www.bnr.ro/nbrfxrates.xml

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
