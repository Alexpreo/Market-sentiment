# Market Sentiment Analysis Bot

A live financial sentiment analysis system that continuously fetches news, analyzes sentiment using FinBERT, and displays real-time trends in a Streamlit dashboard.

## Features

- **Automated News Fetching**: Fetches news for tickers (using yfinance) and sectors (using GoogleNews) every 10 minutes
- **AI-Powered Sentiment Analysis**: Uses ProsusAI/finbert model for accurate financial sentiment analysis
- **Live Dashboard**: Real-time Streamlit dashboard with rolling sentiment trends and bearish headline alerts
- **Deduplication**: Automatically skips already-analyzed articles to save processing time

## Quick Start

### Install Dependencies

```bash
pip3 install -r requirements.txt
```

### Run the Application

Simply run one file to start everything:

```bash
python3 app.py
```

This will:
1. Start the background tracker (fetches and analyzes news every 10 minutes)
2. Launch the Streamlit dashboard in your browser

Press `Ctrl+C` to stop both processes.

## Manual Start (Alternative)

If you prefer to run components separately:

**Terminal 1 - Backend Tracker:**
```bash
python3 tracker.py
```

**Terminal 2 - Dashboard:**
```bash
python3 -m streamlit run dashboard.py
```

## Configuration

Edit `tracker.py` to customize:
- `TICKERS_AND_SECTORS`: List of tickers/sectors to track (default: `['AAPL', 'NVDA', 'Semiconductors']`)
- `ARTICLES_PER_TICKER`: Number of articles to fetch per cycle (default: `25`)
- Analysis interval: Currently set to 10 minutes (change in `schedule.every(10).minutes.do(job)`)

## Files

- `app.py` - Main entry point (starts both tracker and dashboard)
- `tracker.py` - Background process that fetches news and analyzes sentiment
- `dashboard.py` - Streamlit web dashboard
- `src/fetcher.py` - News fetching module
- `src/analyzer.py` - Sentiment analysis module using FinBERT
- `sentiment_data.csv` - Generated data file (created automatically)
