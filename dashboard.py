"""
Streamlit Dashboard
Displays live sentiment trends and recent bearish headlines.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import os
import json
import tempfile
import shutil

CSV_FILE = 'sentiment_data.csv'
CONFIG_FILE = 'config.json'
TRIGGER_FILE = '.trigger_job'

DEFAULT_CONFIG = {
    "tickers_and_sectors": ["AAPL", "NVDA", "Semiconductors"],
    "sectors": ["Semiconductors"],
    "articles_per_ticker": 25
}


def load_config():
    """Load configuration from JSON file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            st.error(f"Error loading config: {e}")
            return DEFAULT_CONFIG.copy()
    else:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()


def save_config(config):
    """Atomically save configuration to JSON file."""
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, dir=os.path.dirname(CONFIG_FILE) or '.') as tmp_file:
            json.dump(config, tmp_file, indent=2)
            tmp_path = tmp_file.name
        
        shutil.move(tmp_path, CONFIG_FILE)
        return True
    except Exception as e:
        st.error(f"Error saving config: {e}")
        return False


def load_data():
    """Load sentiment data from CSV."""
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(CSV_FILE)
        if df.empty:
            return df
        
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df = df.sort_values('Timestamp')
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()


def create_sentiment_chart(df: pd.DataFrame):
    """Create separate rolling sentiment trend charts for each ticker/sector."""
    if df.empty:
        return None
    
    tickers = sorted(df['Ticker'].unique())
    
    if len(tickers) == 1:
        fig = go.Figure()
        ticker = tickers[0]
        ticker_data = df[df['Ticker'] == ticker].copy()
        ticker_data = ticker_data.sort_values('Timestamp')
        
        ticker_data['Rolling_Avg'] = ticker_data['Sentiment_Score'].rolling(
            window=min(6, len(ticker_data)), 
            min_periods=1
        ).mean()
        
        fig.add_trace(go.Scatter(
            x=ticker_data['Timestamp'],
            y=ticker_data['Rolling_Avg'],
            mode='lines',
            name=ticker,
            line=dict(width=2)
        ))
        
        fig.update_layout(
            title=f'{ticker} - Live Sentiment Trend (Rolling Average)',
            xaxis_title='Time',
            yaxis_title='Sentiment Score',
            hovermode='x unified',
            height=500
        )
        return fig
    else:
        rows = (len(tickers) + 1) // 2
        cols = 2 if len(tickers) > 1 else 1
        
        fig = make_subplots(
            rows=rows, cols=cols,
            subplot_titles=tickers,
            vertical_spacing=0.1,
            horizontal_spacing=0.1
        )
        
        for idx, ticker in enumerate(tickers):
            row = (idx // cols) + 1
            col = (idx % cols) + 1
            
            ticker_data = df[df['Ticker'] == ticker].copy()
            ticker_data = ticker_data.sort_values('Timestamp')
            
            ticker_data['Rolling_Avg'] = ticker_data['Sentiment_Score'].rolling(
                window=min(6, len(ticker_data)), 
                min_periods=1
            ).mean()
            
            fig.add_trace(
                go.Scatter(
                    x=ticker_data['Timestamp'],
                    y=ticker_data['Rolling_Avg'],
                    mode='lines',
                    name=ticker,
                    line=dict(width=2),
                    showlegend=False
                ),
                row=row, col=col
            )
            
            fig.update_xaxes(title_text="Time", row=row, col=col)
            fig.update_yaxes(title_text="Sentiment Score", row=row, col=col)
        
        fig.update_layout(
            title='Live Sentiment Trends by Ticker/Sector (Rolling Average)',
            height=300 * rows
        )
        
        return fig


def get_bearish_headlines(df: pd.DataFrame, limit: int = 10):
    """Get most recent bearish headlines."""
    if df.empty:
        return pd.DataFrame()
    
    bearish = df[(df['Label'] == 'Negative') | (df['Sentiment_Score'] < 0)].copy()
    bearish = bearish.sort_values('Timestamp', ascending=False)
    
    return bearish.head(limit)[['Timestamp', 'Ticker', 'Headline', 'Sentiment_Score']]


def main():
    """Main dashboard function."""
    st.set_page_config(
        page_title="Market Sentiment Dashboard",
        page_icon="📈",
        layout="wide"
    )
    
    config = load_config()
    
    st.title("📈 Market Sentiment Dashboard")
    
    with st.sidebar:
        st.header("📊 Track Management")
        
        st.subheader("Add New Track")
        new_item = st.text_input("Ticker or Sector Name", key="new_item_input")
        item_type = st.radio("Type", ["Ticker", "Sector"], key="item_type")
        
        if st.button("➕ Add Track", type="primary"):
            if new_item and new_item.strip():
                new_item = new_item.strip()
                tickers_and_sectors = config.get("tickers_and_sectors", [])
                sectors = config.get("sectors", [])
                
                if new_item not in tickers_and_sectors:
                    tickers_and_sectors.append(new_item)
                    config["tickers_and_sectors"] = tickers_and_sectors
                    
                    if item_type == "Sector" and new_item not in sectors:
                        sectors.append(new_item)
                        config["sectors"] = sectors
                    elif item_type == "Ticker" and new_item in sectors:
                        sectors.remove(new_item)
                        config["sectors"] = sectors
                    
                    if save_config(config):
                        # Trigger tracker to run immediately
                        try:
                            with open(TRIGGER_FILE, 'w') as f:
                                f.write('')
                        except Exception as e:
                            st.warning(f"Could not trigger tracker: {e}")
                        
                        st.success(f"Added {item_type}: {new_item}")
                        st.info("Tracker will run immediately to fetch news for the new item...")
                        st.rerun()
                    else:
                        st.error("Failed to save configuration")
                else:
                    st.warning(f"{new_item} is already being tracked")
            else:
                st.warning("Please enter a ticker or sector name")
        
        st.markdown("---")
        
        st.subheader("Currently Tracking")
        tickers_and_sectors = config.get("tickers_and_sectors", [])
        sectors = config.get("sectors", [])
        
        if not tickers_and_sectors:
            st.info("No items being tracked")
        else:
            for item in tickers_and_sectors:
                col1, col2 = st.columns([3, 1])
                with col1:
                    item_type_label = "🔷 Sector" if item in sectors else "📈 Ticker"
                    st.write(f"{item_type_label} **{item}**")
                with col2:
                    if st.button("🗑️", key=f"remove_{item}"):
                        tickers_and_sectors.remove(item)
                        if item in sectors:
                            sectors.remove(item)
                        config["tickers_and_sectors"] = tickers_and_sectors
                        config["sectors"] = sectors
                        if save_config(config):
                            # Remove sentiment data for this item from CSV
                            try:
                                if os.path.exists(CSV_FILE):
                                    df_existing = pd.read_csv(CSV_FILE)
                                    df_existing = df_existing[df_existing['Ticker'] != item]
                                    df_existing.to_csv(CSV_FILE, index=False)
                                    st.success(f"Removed {item} and cleared its sentiment data")
                                else:
                                    st.success(f"Removed {item}")
                            except Exception as e:
                                st.warning(f"Removed {item} but couldn't clear CSV: {e}")
                            st.rerun()
        
        st.markdown("---")
        
        st.subheader("⚙️ Settings")
        articles_per_ticker = st.number_input(
            "Articles per Ticker/Sector",
            min_value=1,
            max_value=100,
            value=config.get("articles_per_ticker", 25),
            key="articles_input"
        )
        
        if articles_per_ticker != config.get("articles_per_ticker", 25):
            config["articles_per_ticker"] = int(articles_per_ticker)
            if save_config(config):
                st.success("Settings saved")
                st.rerun()
    
    st.markdown("---")
    
    df = load_data()
    
    if df.empty:
        st.warning("No sentiment data available yet. Make sure tracker.py is running and has collected some data.")
        st.info("The dashboard will auto-refresh every 60 seconds.")
        
        time.sleep(60)
        st.rerun()
        return
    
    # Overall metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Articles", len(df))
    
    with col2:
        avg_sentiment = df['Sentiment_Score'].mean()
        st.metric("Overall Avg Sentiment", f"{avg_sentiment:.3f}")
    
    with col3:
        bearish_count = len(df[(df['Label'] == 'Negative') | (df['Sentiment_Score'] < 0)])
        st.metric("Bearish Headlines", bearish_count)
    
    st.markdown("---")
    
    # Per-ticker/sector metrics
    st.subheader("Sentiment by Ticker/Sector")
    tickers = sorted(df['Ticker'].unique())
    
    if tickers:
        cols = st.columns(min(len(tickers), 4))
        for idx, ticker in enumerate(tickers):
            ticker_df = df[df['Ticker'] == ticker]
            with cols[idx % len(cols)]:
                ticker_avg = ticker_df['Sentiment_Score'].mean()
                ticker_count = len(ticker_df)
                ticker_bearish = len(ticker_df[(ticker_df['Label'] == 'Negative') | (ticker_df['Sentiment_Score'] < 0)])
                
                st.metric(
                    label=f"{ticker}",
                    value=f"{ticker_avg:.3f}",
                    delta=f"{ticker_count} articles, {ticker_bearish} bearish"
                )
    
    st.markdown("---")
    
    st.subheader("Live Sentiment Trend")
    fig = create_sentiment_chart(df)
    if fig:
        st.plotly_chart(fig, config={'displayModeBar': True}, use_container_width=True)
    
    st.markdown("---")
    
    st.subheader("Recent Bearish Headlines")
    bearish_df = get_bearish_headlines(df, limit=10)
    
    if bearish_df.empty:
        st.info("No bearish headlines found in recent data.")
    else:
        bearish_df_display = bearish_df.copy()
        bearish_df_display['Timestamp'] = bearish_df_display['Timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        bearish_df_display['Sentiment_Score'] = bearish_df_display['Sentiment_Score'].round(3)
        bearish_df_display.columns = ['Timestamp', 'Ticker', 'Headline', 'Sentiment Score']
        st.dataframe(bearish_df_display, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.caption("Auto-refreshing every 60 seconds...")
    with col2:
        if st.button("🔄 Refresh Now"):
            st.rerun()
    
    time.sleep(60)
    st.rerun()


if __name__ == "__main__":
    main()
