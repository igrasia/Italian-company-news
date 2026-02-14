# Italian Company News Search

A Python application that automatically searches and aggregates daily news for major Italian companies from multiple sources.

## Features

- **40+ Italian companies** tracked from FTSE MIB and other major firms
- **Multiple news sources**: Google News (IT), ANSA, Il Sole 24 Ore, Reuters Italia
- **Daily scheduler**: automated runs at a configurable time
- **SQLite storage**: persistent storage with deduplication
- **Multi-format reports**: console, HTML, and JSON output
- **Sector filtering**: search by industry sector (Banking, Energy, Automotive, etc.)
- **Configurable**: YAML-based configuration

## Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Run a one-time news search for all companies
python main.py

# Start the daily scheduler (runs at time set in config.yaml)
python main.py --schedule

# List all tracked companies
python main.py --list

# Search a specific sector
python main.py --sector Banking

# Search a specific company
python main.py --company Ferrari

# Show database statistics
python main.py --stats

# View articles from a specific date
python main.py --date 2025-01-15

# Verbose output
python main.py -v
```

## Project Structure

```
Italian-company-news/
├── main.py              # CLI entry point
├── config.yaml          # Configuration file
├── requirements.txt     # Python dependencies
├── src/
│   ├── companies.py     # Italian companies list and sectors
│   ├── news_fetcher.py  # News fetching from RSS feeds
│   ├── storage.py       # SQLite storage and deduplication
│   ├── scheduler.py     # Daily scheduling
│   └── report.py        # Console, HTML, JSON report generation
└── data/                # Generated reports and database
```

## Configuration

Edit `config.yaml` to customize:

- `schedule_time` - daily run time (default: `08:00`)
- `max_articles_per_company` - article limit per company (default: `20`)
- `retention_days` - how long to keep articles (default: `90`)
- `sources` - enable/disable individual news sources
- `output` - enable/disable output formats

## Tracked Sectors

- Banking (Intesa Sanpaolo, UniCredit, Mediobanca, ...)
- Insurance (Generali, Unipol)
- Energy (Eni, Saipem, Tenaris)
- Utilities (Enel, Snam, Terna, A2A, Hera)
- Automotive (Stellantis, Ferrari, Pirelli, Iveco)
- Luxury Fashion (Moncler, Brunello Cucinelli, Ferragamo)
- Technology & Telecom (STMicroelectronics, Telecom Italia, Nexi)
- Food & Beverage (Campari, Barilla, Ferrero, Lavazza)
- Pharmaceuticals (Recordati, DiaSorin, Amplifon)
- Infrastructure (Atlantia, Webuild)
- And more...
