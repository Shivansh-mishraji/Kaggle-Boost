"""Cryptocurrency market data collector using yfinance — high demand on Kaggle."""

import yfinance as yf
import pandas as pd
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# High-interest crypto universes
CRYPTO_COLLECTIONS = [
    {
        "id": "top10_crypto_historical_prices",
        "title": "Top 10 Crypto 5 Year Historical OHLCV",
        "description": (
            "Complete 5-year daily OHLCV (Open, High, Low, Close, Volume) data for the top 10 "
            "cryptocurrencies by market cap: BTC, ETH, BNB, XRP, SOL, ADA, DOGE, TRX, DOT, MATIC. "
            "Data from Yahoo Finance. Perfect for crypto algorithmic trading and time-series ML."
        ),
        "tags": ["cryptocurrency", "finance", "time-series", "trading", "machine-learning"],
        "license": "Yahoo Finance Terms (for research/educational use)",
        "tickers": [
            "BTC-USD", "ETH-USD", "BNB-USD", "XRP-USD", "SOL-USD",
            "ADA-USD", "DOGE-USD", "TRX-USD", "DOT-USD", "MATIC-USD",
        ],
        "period": "5y",
        "interval": "1d",
    },
]


class CryptoMarketScraper:
    name = "Yahoo Finance (Crypto Market)"

    def _fetch_tickers(self, tickers: list, period: str, interval: str) -> pd.DataFrame:
        all_frames = []
        for ticker in tickers:
            try:
                t = yf.Ticker(ticker)
                hist = t.history(period=period, interval=interval)
                if hist.empty:
                    continue
                hist = hist.reset_index()
                # Clean up timezone if present
                if "Date" in hist.columns and hasattr(hist["Date"].dt, "tz_localize"):
                    hist["Date"] = hist["Date"].dt.tz_localize(None)
                    
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
        for collection in CRYPTO_COLLECTIONS:
            try:
                logger.info(f"Fetching crypto collection: {collection['id']}")
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
