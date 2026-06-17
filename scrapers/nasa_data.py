"""NASA & NOAA public data scraper — space, climate, weather datasets."""

import requests
import pandas as pd
import logging
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class NASAScraper:
    name = "NASA / NOAA Open Data"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_apod(self, count: int = 100) -> pd.DataFrame:
        """Fetch NASA Astronomy Picture of the Day archive metadata."""
        api_key = "DEMO_KEY"  # Free, no auth needed for basic use
        url = f"https://api.nasa.gov/planetary/apod?api_key={api_key}&count={count}"
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        rows = []
        for item in data:
            rows.append({
                "date": item.get("date", ""),
                "title": item.get("title", ""),
                "explanation": item.get("explanation", ""),
                "media_type": item.get("media_type", ""),
                "url": item.get("url", ""),
                "hdurl": item.get("hdurl", ""),
                "copyright": item.get("copyright", "Public Domain"),
            })
        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"])
        return df.sort_values("date", ascending=False).reset_index(drop=True)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_neo(self) -> pd.DataFrame:
        """Fetch Near Earth Objects (asteroids) data from NASA."""
        api_key = "DEMO_KEY"
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        url = (
            f"https://api.nasa.gov/neo/rest/v1/feed"
            f"?start_date={start_date}&end_date={end_date}&api_key={api_key}"
        )
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        rows = []
        for date_key, neos in data.get("near_earth_objects", {}).items():
            for neo in neos:
                diameter = neo.get("estimated_diameter", {}).get("meters", {})
                close_approach = neo.get("close_approach_data", [{}])[0]
                rows.append({
                    "date": date_key,
                    "name": neo.get("name", ""),
                    "nasa_jpl_url": neo.get("nasa_jpl_url", ""),
                    "absolute_magnitude": neo.get("absolute_magnitude_h"),
                    "diameter_min_m": diameter.get("estimated_diameter_min"),
                    "diameter_max_m": diameter.get("estimated_diameter_max"),
                    "is_potentially_hazardous": neo.get("is_potentially_hazardous_asteroid"),
                    "close_approach_date": close_approach.get("close_approach_date", ""),
                    "relative_velocity_kmh": close_approach.get("relative_velocity", {}).get("kilometers_per_hour"),
                    "miss_distance_km": close_approach.get("miss_distance", {}).get("kilometers"),
                    "orbiting_body": close_approach.get("orbiting_body", ""),
                })
        df = pd.DataFrame(rows)
        for col in ["relative_velocity_kmh", "miss_distance_km", "diameter_min_m", "diameter_max_m"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df.reset_index(drop=True)

    def scrape(self) -> list:
        results = []

        try:
            logger.info("Fetching NASA APOD archive...")
            apod_df = self._fetch_apod(200)
            results.append({
                "id": "nasa_apod_archive",
                "title": "NASA Astronomy Picture of the Day Archive",
                "description": (
                    "NASA's Astronomy Picture of the Day (APOD) archive with titles, "
                    "explanations, media types, and URLs. Public domain data from NASA. "
                    "Great for NLP, image analysis, and space exploration projects."
                ),
                "tags": ["nasa", "astronomy", "space", "nlp", "science", "image-data"],
                "license": "Public Domain (NASA)",
                "source": "NASA APOD API (https://api.nasa.gov)",
                "dataframe": apod_df,
                "filename": "nasa_apod_archive.csv",
                "config": {"date_columns": ["date"], "remove_nulls": False},
            })
            logger.info(f"✓ APOD: {len(apod_df)} records")
        except Exception as e:
            logger.error(f"APOD fetch failed: {e}")

        try:
            logger.info("Fetching NASA Near Earth Objects...")
            neo_df = self._fetch_neo()
            results.append({
                "id": "nasa_near_earth_objects",
                "title": "NASA Near Earth Objects Asteroids",
                "description": (
                    "Near Earth Objects tracked by NASA's Jet Propulsion Laboratory. "
                    "Includes asteroid size, velocity, miss distance, and hazard classification. "
                    "Public domain NASA data. Updated weekly. Ideal for regression and classification."
                ),
                "tags": ["nasa", "asteroids", "space", "classification", "regression", "science"],
                "license": "Public Domain (NASA)",
                "source": "NASA NeoWs API (https://api.nasa.gov)",
                "dataframe": neo_df,
                "filename": "nasa_near_earth_objects.csv",
                "config": {"date_columns": ["date", "close_approach_date"], "remove_nulls": False},
            })
            logger.info(f"✓ NEO: {len(neo_df)} records")
        except Exception as e:
            logger.error(f"NEO fetch failed: {e}")

        return results
