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
        Fetch news for a specific ticker using yfinance.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            max_articles: Maximum number of articles to fetch (default: 25)
            
        Returns:
            List of dictionaries with keys: {'title': str, 'date': str, 'link': str}
        """
        articles = []
        
        try:
            stock = yf.Ticker(ticker)
            news_data = stock.news
            
            if news_data:
                for item in news_data[:max_articles]:
                    article = {
                        'title': item.get('title', ''),
                        'date': self._parse_date(item.get('providerPublishTime', 0)),
                        'link': item.get('link', '')
                    }
                    articles.append(article)
                    
        except Exception as e:
            print(f"Error fetching news for {ticker}: {e}")
            
        return articles
    
    def fetch_sector_news(self, sector: str, max_articles: int = 25) -> List[Dict]:
        """
        Fetch sector-related news using GoogleNews.
        
        Args:
            sector: Sector name or keyword (e.g., 'Semiconductors')
            max_articles: Maximum number of articles to fetch (default: 25)
            
        Returns:
            List of dictionaries with keys: {'title': str, 'date': str, 'link': str}
        """
        articles = []
        
        try:
            googlenews = GoogleNews()
            googlenews.search(f"{sector} finance stock market")
            googlenews.setlang('en')
            googlenews.setencode('utf-8')
            
            results = googlenews.result()
            
            for item in results[:max_articles]:
                article = {
                    'title': item.get('title', ''),
                    'date': self._parse_date_google(item.get('date', '')),
                    'link': item.get('link', '')
                }
                articles.append(article)
            
            googlenews.clear()
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error fetching sector news for {sector}: {e}")
            
        return articles
    
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

