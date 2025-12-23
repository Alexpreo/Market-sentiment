"""
Background Tracker
Continuously fetches news and analyzes sentiment every 10 minutes.
"""

import pandas as pd
import schedule
import time
from datetime import datetime
import os
from src.fetcher import NewsFetcher
from src.analyzer import SentimentEngine

ARTICLES_PER_TICKER = 25
TICKERS_AND_SECTORS = ['AAPL', 'NVDA', 'Semiconductors']
CSV_FILE = 'sentiment_data.csv'

fetcher = NewsFetcher()
analyzer = SentimentEngine()


def job():
    """Main job function that runs every 10 minutes."""
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting sentiment analysis cycle...")
    
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
    
    for ticker_or_sector in TICKERS_AND_SECTORS:
        print(f"\nProcessing {ticker_or_sector}...")
        
        try:
            if ticker_or_sector in ['Semiconductors']:
                articles = fetcher.fetch_sector_news(ticker_or_sector, max_articles=ARTICLES_PER_TICKER)
            else:
                articles = fetcher.fetch_ticker_news(ticker_or_sector, max_articles=ARTICLES_PER_TICKER)
            
            print(f"Fetched {len(articles)} articles for {ticker_or_sector} (requested {ARTICLES_PER_TICKER})")
            
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
            except Exception as e:
                print(f"Error appending to CSV: {e}")
                new_df.to_csv(CSV_FILE, index=False)
        else:
            new_df.to_csv(CSV_FILE, index=False)
            print(f"Created new CSV file: {CSV_FILE}")
        
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Saved {len(all_new_results)} new sentiment analyses to {CSV_FILE}")
    else:
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No new articles to analyze")


def main():
    """Main loop that runs the scheduler."""
    print("Starting Market Sentiment Tracker...")
    print(f"Configuration:")
    print(f"  - Tickers/Sectors: {TICKERS_AND_SECTORS}")
    print(f"  - Articles per ticker: {ARTICLES_PER_TICKER}")
    print(f"  - Analysis interval: 10 minutes")
    print(f"  - CSV file: {CSV_FILE}")
    print("\nPress Ctrl+C to stop\n")
    
    schedule.every(10).minutes.do(job)
    
    job()
    
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
