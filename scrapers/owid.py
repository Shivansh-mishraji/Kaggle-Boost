"""Our World in Data (OWID) scraper — health, climate, economics."""

import requests
import pandas as pd
import logging
from io import StringIO
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# OWID provides direct CSV downloads — CC-BY license
OWID_DATASETS = [
    {
        "id": "owid_global_energy_consumption",
        "url": "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv",
        "title": "Global Energy Consumption by Country (OWID) — Coal, Oil, Gas, Renewables",
        "description": (
            "Comprehensive energy consumption dataset covering all countries from 1900 to present. "
            "Includes coal, oil, gas, nuclear, solar, wind, hydro, and total energy data. "
            "Source: Our World in Data (CC-BY). Ideal for energy transition and climate ML projects."
        ),
        "tags": ["energy", "climate", "renewables", "fossil-fuels", "global", "owid", "environment"],
        "license": "CC BY 4.0",
        "max_rows": 50000,
    },
    {
        "id": "owid_covid19_data",
        "url": "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv",
        "title": "COVID-19 Complete Global Dataset — OWID (Cases, Deaths, Vaccines)",
        "description": (
            "The most comprehensive COVID-19 dataset available. Covers cases, deaths, "
            "hospitalizations, testing, and vaccinations for all countries. "
            "Source: Our World in Data (CC-BY). Updated regularly. "
            "A benchmark dataset for pandemic analysis and forecasting."
        ),
        "tags": ["covid-19", "pandemic", "health", "global", "owid", "time-series", "vaccines"],
        "license": "CC BY 4.0",
        "max_rows": 100000,
    },
    {
        "id": "owid_world_happiness",
        "url": "https://raw.githubusercontent.com/owid/owid-datasets/master/datasets/World%20Happiness%20Report%202023/World%20Happiness%20Report%202023.csv",
        "title": "World Happiness Report 2023 — Country Rankings & Scores",
        "description": (
            "World Happiness Report data showing happiness scores and rankings by country. "
            "Includes GDP per capita, social support, health, freedom, and corruption metrics. "
            "Our World in Data, CC-BY. Great for regression and socioeconomic analysis."
        ),
        "tags": ["happiness", "wellbeing", "global", "socioeconomics", "owid", "regression"],
        "license": "CC BY 4.0",
        "max_rows": 5000,
    },
]


class OWIDScraper:
    name = "Our World in Data (OWID)"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_csv(self, url: str, max_rows: int = None) -> pd.DataFrame:
        resp = requests.get(url, timeout=60, stream=True)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text), low_memory=False)
        if max_rows and len(df) > max_rows:
            df = df.tail(max_rows)  # Keep most recent rows
        return df

    def _clean_owid_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize OWID dataframe columns."""
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        # Drop fully empty columns
        df = df.dropna(axis=1, how="all")
        return df.reset_index(drop=True)

    def scrape(self) -> list:
        results = []
        for ds in OWID_DATASETS:
            try:
                logger.info(f"Fetching OWID dataset: {ds['id']}")
                df = self._fetch_csv(ds["url"], ds.get("max_rows"))
                df = self._clean_owid_df(df)

                if df.empty:
                    continue

                results.append({
                    "id": ds["id"],
                    "title": ds["title"],
                    "description": ds["description"],
                    "tags": ds["tags"],
                    "license": ds["license"],
                    "source": f"Our World in Data ({ds['url']})",
                    "dataframe": df,
                    "filename": f"{ds['id']}.csv",
                    "config": {"remove_nulls": False},
                })
                logger.info(f"✓ {ds['id']}: {len(df)} rows, {len(df.columns)} cols")
            except Exception as e:
                logger.error(f"Failed {ds['id']}: {e}")

        return results
