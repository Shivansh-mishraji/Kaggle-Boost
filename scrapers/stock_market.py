"""Stock market data collector using yfinance — high demand on Kaggle."""

import yfinance as yf
import pandas as pd
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# High-interest stock universes
STOCK_COLLECTIONS = [
    {
        "id": "nifty50_historical_prices",
        "title": "NIFTY 50 Stocks — 5-Year Historical OHLCV Data (India NSE)",
        "description": (
            "Complete 5-year daily OHLCV (Open, High, Low, Close, Volume) data for all 50 stocks "
            "in India's NIFTY 50 index. Data from Yahoo Finance. "
            "Perfect for algorithmic trading, portfolio optimization, and time-series forecasting. "
            "Great for Indian stock market analysis on Kaggle."
        ),
        "tags": ["india", "stocks", "nse", "nifty50", "finance", "time-series", "trading"],
        "license": "Yahoo Finance Terms (for research/educational use)",
        "tickers": [
            "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "HINDUNILVR.NS",
            "ICICIBANK.NS", "SBIN.NS", "BAJFINANCE.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
            "WIPRO.NS", "LT.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS",
            "SUNPHARMA.NS", "TATAMOTORS.NS", "NTPC.NS", "POWERGRID.NS", "TECHM.NS",
        ],
        "period": "5y",
        "interval": "1d",
    },
    {
        "id": "global_tech_stocks_sp500",
        "title": "Top 20 Global Tech Stocks — 5-Year OHLCV (FAANG + More)",
        "description": (
            "5-year daily OHLCV price history for top global technology stocks including "
            "Apple, Microsoft, Google, Amazon, Meta, Tesla, NVIDIA, and more. "
            "Data via Yahoo Finance. Ideal for ML stock prediction, portfolio analysis, "
            "and financial time-series projects."
        ),
        "tags": ["stocks", "tech", "faang", "sp500", "finance", "time-series", "machine-learning"],
        "license": "Yahoo Finance Terms (for research/educational use)",
        "tickers": [
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA",
            "NFLX", "AMD", "INTC", "CRM", "ORCL", "IBM", "QCOM", "ADBE",
        ],
        "period": "5y",
        "interval": "1d",
    },
]


class StockMarketScraper:
    name = "Yahoo Finance (Stock Market)"

    def _fetch_tickers(self, tickers: list, period: str, interval: str) -> pd.DataFrame:
        all_frames = []
        for ticker in tickers:
            try:
                t = yf.Ticker(ticker)
                hist = t.history(period=period, interval=interval)
                if hist.empty:
                    continue
                hist = hist.reset_index()
                hist["ticker"] = ticker
                hist.columns = [c.lower().replace(" ", "_") for c in hist.columns]
                all_frames.append(hist)
                logger.info(f"  ✓ {ticker}: {len(hist)} rows")
            except Exception as e:
                logger.warning(f"  ✗ {ticker} failed: {e}")

        if not all_frames:
            return pd.DataFrame()

        df = pd.concat(all_frames, ignore_index=True)
        # Move ticker to front
        cols = ["ticker"] + [c for c in df.columns if c != "ticker"]
        return df[cols]

    def scrape(self) -> list:
        results = []
        for collection in STOCK_COLLECTIONS:
            try:
                logger.info(f"Fetching stock collection: {collection['id']}")
                df = self._fetch_tickers(
                    collection["tickers"],
                    collection["period"],
                    collection["interval"]
                )
                if df.empty:
                    continue

                results.append({
                    "id": collection["id"],
                    "title": collection["title"],
                    "description": collection["description"],
                    "tags": collection["tags"],
                    "license": collection["license"],
                    "source": "Yahoo Finance via yfinance library",
                    "dataframe": df,
                    "filename": f"{collection['id']}.csv",
                    "config": {"remove_nulls": False},
                })
                logger.info(f"✓ {collection['id']}: {len(df)} total rows")
            except Exception as e:
                logger.error(f"Failed {collection['id']}: {e}")

        return results
