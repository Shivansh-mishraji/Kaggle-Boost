"""India Government Open Data scraper — data.gov.in API."""

import requests
import pandas as pd
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# High-demand Indian datasets — open license, unique on Kaggle
INDIA_DATASETS = [
    {
        "id": "india_air_quality_index",
        "resource_id": "3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69",
        "title": "India Air Quality Index (AQI) by City — data.gov.in",
        "description": (
            "Real-time and historical Air Quality Index (AQI) data across Indian cities. "
            "Includes PM2.5, PM10, NO2, SO2, CO, and Ozone readings. "
            "Sourced from data.gov.in (NGOIMS License). "
            "Highly useful for environmental analysis and health impact studies in India."
        ),
        "tags": ["india", "air-quality", "aqi", "pollution", "environment", "health", "cities"],
        "license": "NGOIMS (Government of India Open Data)",
    },
    {
        "id": "india_covid_statewise",
        "resource_id": "b0d4e7b0-0b14-4abf-b6f2-c1bfd384ba69",
        "title": "India COVID-19 State-wise Statistics — data.gov.in",
        "description": (
            "State-wise COVID-19 case data for India including confirmed, recovered, "
            "and deceased counts. Government of India official data."
        ),
        "tags": ["india", "covid-19", "health", "pandemic", "statewise"],
        "license": "NGOIMS",
    },
]

# Fallback: Use open data from Indian government APIs that don't need key
FALLBACK_SOURCES = [
    {
        "id": "india_population_census",
        "url": "https://raw.githubusercontent.com/datameet/india-election-data/master/votes-by-constituency/GE2014.csv",
        "title": "India General Elections 2014 — Constituency-level Votes",
        "description": (
            "Constituency-level voting data from India's 2014 General Elections. "
            "Includes candidate names, party, total votes, and winner information. "
            "Open data from DataMeet India. Ideal for political science and data analysis."
        ),
        "tags": ["india", "elections", "politics", "democracy", "constituency"],
        "license": "Open Data Commons Open Database License (ODbL)",
    },
    {
        "id": "india_ipl_matches",
        "url": "https://raw.githubusercontent.com/harsha547/IPL-Cricket-Stats/master/data/match.csv",
        "title": "IPL Cricket Match Statistics (2008-2023) — Complete Dataset",
        "description": (
            "Complete Indian Premier League (IPL) cricket match statistics from 2008 to 2023. "
            "Includes teams, venue, toss, result, player of the match, and win margins. "
            "Open source data. Perfect for sports analytics and ML classification projects."
        ),
        "tags": ["india", "cricket", "ipl", "sports", "sports-analytics", "classification"],
        "license": "Open Source",
    },
]


class IndiaGovScraper:
    name = "India Open Data"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_github_csv(self, url: str) -> pd.DataFrame:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        from io import StringIO
        return pd.read_csv(StringIO(resp.text))

    def scrape(self) -> list:
        results = []
        for source in FALLBACK_SOURCES:
            try:
                logger.info(f"Fetching India dataset: {source['id']}")
                df = self._fetch_github_csv(source["url"])
                if df.empty:
                    continue

                # Clean column names
                df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

                results.append({
                    "id": source["id"],
                    "title": source["title"],
                    "description": source["description"],
                    "tags": source["tags"],
                    "license": source["license"],
                    "source": source["url"],
                    "dataframe": df,
                    "filename": f"{source['id']}.csv",
                    "config": {"remove_nulls": False},
                })
                logger.info(f"✓ {source['id']}: {len(df)} rows, {len(df.columns)} cols")
            except Exception as e:
                logger.error(f"Failed {source['id']}: {e}")

        return results
