# Tinkoff Trading Bot

Automated trading bot for Tinkoff Invest (Mosbirzha) that selects the top 20 assets based on technical strategy backtesting and executes trades.

## Features
* Scans all RUB shares periodically (every 2 hours).
* Downloads 1-year historical data.
* Backtests multiple strategies (SMA, RSI) to find the best performing setup.
* Filters out assets where a single lot costs > 500 RUB (unless manually activated).
* Provides a secure web dashboard for real-time monitoring and portfolio control.

## Installation
1. `python3 -m venv venv`
2. `source venv/bin/activate`
3. `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and configure your `TINKOFF_TOKEN` and `WEB_PASSWORD`.

## Running
`python app/main.py`
Access the dashboard at `http://localhost:8000`. Login with your password (default: `admin`).
