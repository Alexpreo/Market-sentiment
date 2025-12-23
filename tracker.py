"""
Background Tracker
Continuously fetches news and analyzes sentiment every 10 minutes.
"""

import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import pandas as pd
import schedule
import time
from datetime import datetime
import json
from src.fetcher import NewsFetcher
from src.analyzer import SentimentEngine

CONFIG_FILE = 'config.json'
CSV_FILE = 'sentiment_data.csv'
TRIGGER_FILE = '.trigger_job'

DEFAULT_CONFIG = {
    "tickers_and_sectors": ["AAPL", "NVDA", "Semiconductors"],
    "sectors": ["Semiconductors"],
    "articles_per_ticker": 25
}

fetcher = NewsFetcher()
analyzer = SentimentEngine()


def load_config():
    """Load configuration from JSON file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            print(f"Error loading config: {e}, using defaults")
            return DEFAULT_CONFIG.copy()
    else:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        return DEFAULT_CONFIG.copy()


def job():
    """Main job function that runs every 10 minutes."""
    config = load_config()
    tickers_and_sectors = config.get("tickers_and_sectors", DEFAULT_CONFIG["tickers_and_sectors"])
    sectors = config.get("sectors", DEFAULT_CONFIG["sectors"])
    articles_per_ticker = config.get("articles_per_ticker", DEFAULT_CONFIG["articles_per_ticker"])
    
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting sentiment analysis cycle...")
    print(f"Tracking: {tickers_and_sectors}")
    
    existing_headlines = set()
    
    if os.path.exists(CSV_FILE):
        try:
            df_existing = pd.read_csv(CSV_FILE)
            if 'Headline' in df_existing.columns:
                existing_headlines = set(df_existing['Headline'].astype(str))
            print(f"Loaded {len(existing_headlines)} existing headlines from CSV")
        except Exception as e:
            print(f"Error reading existing CSV: {e}")
    
    all_new_results = []
    
    for ticker_or_sector in tickers_and_sectors:
        print(f"\nProcessing {ticker_or_sector}...")
        
        try:
            if ticker_or_sector in sectors:
                articles = fetcher.fetch_sector_news(ticker_or_sector, max_articles=articles_per_ticker)
            else:
                articles = fetcher.fetch_ticker_news(ticker_or_sector, max_articles=articles_per_ticker)
            
            print(f"Fetched {len(articles)} articles for {ticker_or_sector} (requested {articles_per_ticker})")
            
            new_articles = [a for a in articles if a['title'] not in existing_headlines]
            
            if not new_articles:
                print(f"No new articles for {ticker_or_sector}")
                continue
            
            print(f"Found {len(new_articles)} new articles for {ticker_or_sector}")
            
            headlines = [article['title'] for article in new_articles]
            sentiment_df = analyzer.analyze(headlines)
            
            for idx, article in enumerate(new_articles):
                if idx < len(sentiment_df):
                    result = {
                        'Timestamp': datetime.now().isoformat(),
                        'Ticker': ticker_or_sector,
                        'Headline': article['title'],
                        'Sentiment_Score': sentiment_df.iloc[idx]['sentiment_score'],
                        'Label': sentiment_df.iloc[idx]['sentiment_label']
                    }
                    all_new_results.append(result)
                    existing_headlines.add(article['title'])
            
        except Exception as e:
            print(f"Error processing {ticker_or_sector}: {e}")
    
    if all_new_results:
        new_df = pd.DataFrame(all_new_results)
        
        if os.path.exists(CSV_FILE):
            try:
                existing_df = pd.read_csv(CSV_FILE)
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                combined_df.to_csv(CSV_FILE, index=False)
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Saved {len(all_new_results)} new sentiment analyses to {CSV_FILE}")
            except Exception as e:
                print(f"Error appending to CSV: {e}")
                backup_file = f"{CSV_FILE}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                try:
                    new_df.to_csv(backup_file, index=False)
                    print(f"Saved new data to backup file: {backup_file}")
                    print("WARNING: Existing CSV could not be updated. Historical data preserved in original file.")
                except Exception as backup_error:
                    print(f"CRITICAL: Failed to save backup file: {backup_error}")
                    print("New data was not saved. Historical data remains intact.")
        else:
            new_df.to_csv(CSV_FILE, index=False)
            print(f"Created new CSV file: {CSV_FILE}")
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Saved {len(all_new_results)} new sentiment analyses to {CSV_FILE}")
    else:
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No new articles to analyze")


def main():
    """Main loop that runs the scheduler."""
    config = load_config()
    print("Starting Market Sentiment Tracker...")
    print(f"Configuration:")
    print(f"  - Tickers/Sectors: {config.get('tickers_and_sectors', [])}")
    print(f"  - Sectors (use sector news): {config.get('sectors', [])}")
    print(f"  - Articles per ticker: {config.get('articles_per_ticker', 25)}")
    print(f"  - Analysis interval: 10 minutes")
    print(f"  - CSV file: {CSV_FILE}")
    print(f"  - Config file: {CONFIG_FILE}")
    print("\nPress Ctrl+C to stop\n")
    
    schedule.every(10).minutes.do(job)
    
    job()
    
    while True:
        schedule.run_pending()
        
        # Check for trigger file to run job immediately
        if os.path.exists(TRIGGER_FILE):
            try:
                os.remove(TRIGGER_FILE)
                print("\n[TRIGGER] New ticker/sector added - running job immediately...")
                job()
            except Exception as e:
                print(f"Error handling trigger: {e}")
        
        time.sleep(60)


if __name__ == "__main__":
    main()
