"""
Streamlit Dashboard
Displays live sentiment trends and recent bearish headlines.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import os

CSV_FILE = 'sentiment_data.csv'


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
    """Create rolling sentiment trend chart."""
    if df.empty:
        return None
    
    fig = go.Figure()
    
    tickers = df['Ticker'].unique()
    
    for ticker in tickers:
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
        title='Live Sentiment Trend (Rolling Average)',
        xaxis_title='Time',
        yaxis_title='Sentiment Score',
        hovermode='x unified',
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
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
    
    st.title("📈 Market Sentiment Dashboard")
    st.markdown("---")
    
    df = load_data()
    
    if df.empty:
        st.warning("No sentiment data available yet. Make sure tracker.py is running and has collected some data.")
        st.info("The dashboard will auto-refresh every 60 seconds.")
        
        time.sleep(60)
        st.rerun()
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Articles", len(df))
    
    with col2:
        avg_sentiment = df['Sentiment_Score'].mean()
        st.metric("Average Sentiment", f"{avg_sentiment:.3f}")
    
    with col3:
        bearish_count = len(df[(df['Label'] == 'Negative') | (df['Sentiment_Score'] < 0)])
        st.metric("Bearish Headlines", bearish_count)
    
    st.markdown("---")
    
    st.subheader("Live Sentiment Trend")
    fig = create_sentiment_chart(df)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    
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
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption("Auto-refreshing every 60 seconds...")
    
    time.sleep(60)
    st.rerun()


if __name__ == "__main__":
    main()
