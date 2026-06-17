"""World Bank Open Data scraper — fetches high-demand development indicators."""

import requests
import pandas as pd
import logging
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# High-demand indicators on Kaggle — verified free & open (CC-BY 4.0)
INDICATORS = [
    {
        "id": "worldbank_gdp_growth",
        "indicator_code": "NY.GDP.MKTP.KD.ZG",
        "title": "World GDP Growth Rate by Country (1960-2024) | World Bank",
        "description": "Annual GDP growth rate (%) for all countries from 1960 to 2024. "
                      "Sourced from the World Bank Open Data under CC-BY 4.0. "
                      "Ideal for macroeconomic analysis, forecasting, and global trend studies.",
        "tags": ["economics", "gdp", "world-bank", "macroeconomics", "finance", "global"],
        "license": "CC BY 4.0",
    },
    {
        "id": "worldbank_population",
        "indicator_code": "SP.POP.TOTL",
        "title": "World Population by Country (1960-2024) | World Bank",
        "description": "Total population for all countries and regions from 1960 to 2024. "
                      "World Bank Open Data, CC-BY 4.0. Perfect for demographic studies and ML features.",
        "tags": ["demographics", "population", "world-bank", "sociology", "global"],
        "license": "CC BY 4.0",
    },
    {
        "id": "worldbank_co2_emissions",
        "indicator_code": "EN.ATM.CO2E.PC",
        "title": "CO2 Emissions Per Capita by Country | World Bank",
        "description": "CO2 emissions in metric tons per capita by country. "
                      "World Bank Open Data, CC-BY 4.0. Essential for climate change analysis.",
        "tags": ["climate", "co2", "environment", "world-bank", "sustainability"],
        "license": "CC BY 4.0",
    },
    {
        "id": "worldbank_internet_users",
        "indicator_code": "IT.NET.USER.ZS",
        "title": "Internet Users (% of Population) by Country | World Bank",
        "description": "Percentage of individuals using the Internet for all countries. "
                      "World Bank Open Data, CC-BY 4.0. Great for digital divide and tech adoption studies.",
        "tags": ["internet", "technology", "digital", "world-bank", "global"],
        "license": "CC BY 4.0",
    },
]


class WorldBankScraper:
    name = "World Bank Open Data"
    BASE_URL = "https://api.worldbank.org/v2"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_indicator(self, indicator_code: str) -> list:
        """Fetch indicator data for all countries."""
        all_data = []
        page = 1
        while True:
            url = (
                f"{self.BASE_URL}/country/all/indicator/{indicator_code}"
                f"?format=json&per_page=1000&page={page}&mrv=60"
            )
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            if not data or len(data) < 2 or not data[1]:
                break

            all_data.extend(data[1])
            total_pages = data[0].get("pages", 1)
            if page >= total_pages:
                break
            page += 1

        return all_data

    def _to_dataframe(self, raw_data: list) -> pd.DataFrame:
        """Convert World Bank API response to clean DataFrame."""
        rows = []
        for item in raw_data:
            if item.get("value") is None:
                continue
            rows.append({
                "country_code": item.get("countryiso3code", ""),
                "country_name": item.get("country", {}).get("value", ""),
                "year": int(item.get("date", 0)),
                "value": float(item.get("value", 0)),
                "indicator": item.get("indicator", {}).get("value", ""),
            })
        df = pd.DataFrame(rows)
        df = df[df["country_code"].str.len() == 3]  # Remove aggregates, keep countries
        return df.sort_values(["country_name", "year"]).reset_index(drop=True)

    def scrape(self) -> list:
        """Scrape all configured World Bank indicators."""
        results = []
        for config in INDICATORS:
            try:
                logger.info(f"Fetching World Bank indicator: {config['indicator_code']}")
                raw = self._fetch_indicator(config["indicator_code"])
                df = self._to_dataframe(raw)

                if df.empty:
                    logger.warning(f"No data for indicator {config['indicator_code']}")
                    continue

                results.append({
                    "id": config["id"],
                    "title": config["title"],
                    "description": config["description"],
                    "tags": config["tags"],
                    "license": config["license"],
                    "source": "World Bank Open Data (https://data.worldbank.org)",
                    "dataframe": df,
                    "filename": f"{config['id']}.csv",
                    "config": {
                        "date_columns": ["year"],
                        "numeric_columns": ["value"],
                        "remove_nulls": True,
                    }
                })
                logger.info(f"✓ Fetched {len(df)} rows for {config['id']}")
            except Exception as e:
                logger.error(f"Failed to fetch {config['id']}: {e}")

        return results
