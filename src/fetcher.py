"""
News Fetcher Module
Fetches financial news from various sources for sentiment analysis.
"""

import yfinance as yf
from GoogleNews import GoogleNews
from datetime import datetime
from typing import List, Dict
import time


class NewsFetcher:
    """Fetches news articles for tickers and sectors."""
    
    def __init__(self):
        """Initialize the NewsFetcher."""
        pass
    
    def fetch_ticker_news(self, ticker: str, max_articles: int = 25) -> List[Dict]:
        """
        Fetch news for a specific ticker using yfinance, with GoogleNews fallback.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            max_articles: Maximum number of articles to fetch (default: 25)
            
        Returns:
            List of dictionaries with keys: {'title': str, 'date': str, 'link': str}
        """
        articles = []
        
        max_retries = 2
        for attempt in range(max_retries):
            try:
                stock = yf.Ticker(ticker)
                time.sleep(0.5)
                
                try:
                    news_data = stock.news
                    if news_data and isinstance(news_data, list) and len(news_data) > 0:
                        for item in news_data[:max_articles]:
                            if isinstance(item, dict):
                                title = item.get('title', '') or item.get('headline', '') or item.get('summary', '')
                                if title and title.strip():
                                    article = {
                                        'title': title.strip(),
                                        'date': self._parse_date(item.get('providerPublishTime', item.get('pubDate', item.get('datetime', 0)))),
                                        'link': item.get('link', item.get('url', item.get('guid', '')))
                                    }
                                    articles.append(article)
                        if articles:
                            return articles
                except Exception as e:
                    if attempt == 0:
                        print(f"yfinance news failed for {ticker}: {e}")
                    pass
                        
            except Exception as e:
                if attempt == 0:
                    print(f"Error with yfinance for {ticker}: {e}")
                pass
        
        if not articles:
            print(f"Falling back to GoogleNews for {ticker}...")
            articles = self._fetch_googlenews_paginated(f"{ticker} stock news", max_articles)
            
        return articles
    
    def _fetch_googlenews_paginated(self, query: str, max_articles: int) -> List[Dict]:
        """Fetch articles from GoogleNews with pagination to get more than 10 articles."""
        articles = []
        try:
            googlenews = GoogleNews()
            googlenews.setlang('en')
            googlenews.setencode('utf-8')
            googlenews.search(query)
            
            page = 1
            seen_titles = set()
            
            while len(articles) < max_articles:
                try:
                    if page == 1:
                        results = googlenews.result()
                    else:
                        googlenews.get_page(page)
                        results = googlenews.result()
                    
                    if not results or len(results) == 0:
                        break
                    
                    new_count = 0
                    for item in results:
                        if len(articles) >= max_articles:
                            break
                        
                        title = item.get('title', '')
                        if title and title not in seen_titles:
                            seen_titles.add(title)
                            article = {
                                'title': title,
                                'date': self._parse_date_google(item.get('date', '')),
                                'link': item.get('link', '')
                            }
                            articles.append(article)
                            new_count += 1
                    
                    if new_count == 0:
                        break
                    
                    page += 1
                    time.sleep(1)
                    
                    if page > 10:
                        break
                        
                except Exception as e:
                    if page == 1:
                        print(f"Error fetching GoogleNews page {page}: {e}")
                    break
            
            googlenews.clear()
            time.sleep(1)
        except Exception as e:
            print(f"Error with GoogleNews pagination: {e}")
        
        return articles
    
    def fetch_sector_news(self, sector: str, max_articles: int = 25) -> List[Dict]:
        """
        Fetch sector-related news using GoogleNews with pagination.
        
        Args:
            sector: Sector name or keyword (e.g., 'Semiconductors')
            max_articles: Maximum number of articles to fetch (default: 25)
            
        Returns:
            List of dictionaries with keys: {'title': str, 'date': str, 'link': str}
        """
        return self._fetch_googlenews_paginated(f"{sector} finance stock market", max_articles)
    
    def _parse_date(self, timestamp) -> str:
        """
        Parse timestamp to ISO format string.
        
        Args:
            timestamp: Unix timestamp in seconds or milliseconds
            
        Returns:
            ISO format date string
        """
        try:
            if timestamp:
                if timestamp > 1e10:
                    timestamp = timestamp / 1000
                dt = datetime.fromtimestamp(timestamp)
                return dt.isoformat()
        except Exception:
            pass
        return datetime.now().isoformat()
    
    def _parse_date_google(self, date_str: str) -> str:
        """
        Parse Google News date string to ISO format.
        
        Args:
            date_str: Date string from GoogleNews
            
        Returns:
            ISO format date string
        """
        try:
            if date_str:
                dt = datetime.strptime(date_str, '%m/%d/%Y')
                return dt.isoformat()
        except Exception:
            pass
        return datetime.now().isoformat()

