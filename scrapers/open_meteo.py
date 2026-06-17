"""Historical weather data collector using Open-Meteo — excellent for ML tasks."""

import requests
import pandas as pd
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Major global cities coordinates
CITIES = [
    {"name": "New York", "lat": 40.7128, "lon": -74.0060},
    {"name": "London", "lat": 51.5074, "lon": -0.1278},
    {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503},
    {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
    {"name": "Sydney", "lat": -33.8688, "lon": 151.2093},
    {"name": "Paris", "lat": 48.8566, "lon": 2.3522},
    {"name": "Moscow", "lat": 55.7558, "lon": 37.6173},
    {"name": "Cape Town", "lat": -33.9249, "lon": 18.4241},
    {"name": "Sao Paulo", "lat": -23.5505, "lon": -46.6333},
    {"name": "Beijing", "lat": 39.9042, "lon": 116.4074},
]

class OpenMeteoScraper:
    name = "Open-Meteo (Global Weather)"

    def _fetch_city_weather(self, city: dict, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch daily historical weather for a specific city."""
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": city["lat"],
            "longitude": city["lon"],
            "start_date": start_date,
            "end_date": end_date,
            "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "rain_sum", "snowfall_sum"],
            "timezone": "UTC"
        }
        
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            daily = data.get("daily", {})
            if not daily or "time" not in daily:
                return pd.DataFrame()
                
            df = pd.DataFrame({
                "date": daily["time"],
                "temp_max_c": daily.get("temperature_2m_max", []),
                "temp_min_c": daily.get("temperature_2m_min", []),
                "precipitation_mm": daily.get("precipitation_sum", []),
                "rain_mm": daily.get("rain_sum", []),
                "snowfall_cm": daily.get("snowfall_sum", []),
            })
            df["city"] = city["name"]
            df["latitude"] = city["lat"]
            df["longitude"] = city["lon"]
            
            # Rearrange columns
            cols = ["date", "city", "latitude", "longitude"] + [c for c in df.columns if c not in ["date", "city", "latitude", "longitude"]]
            return df[cols]
            
        except Exception as e:
            logger.warning(f"  ✗ Failed to fetch weather for {city['name']}: {e}")
            return pd.DataFrame()

    def scrape(self) -> list:
        # Last 5 years
        end_date = datetime.now() - timedelta(days=2) # 2 days ago to ensure data exists
        start_date = end_date - timedelta(days=365 * 5)
        
        str_end = end_date.strftime("%Y-%m-%d")
        str_start = start_date.strftime("%Y-%m-%d")
        
        logger.info(f"Fetching Global Weather data from {str_start} to {str_end}")
        
        all_frames = []
        for city in CITIES:
            df = self._fetch_city_weather(city, str_start, str_end)
            if not df.empty:
                logger.info(f"  ✓ {city['name']}: {len(df)} days")
                all_frames.append(df)
                
        if not all_frames:
            logger.error("Failed to fetch any weather data.")
            return []
            
        final_df = pd.concat(all_frames, ignore_index=True)
        
        return [{
            "id": "global_major_cities_weather_5yr",
            "title": "Global Major Cities Weather 5 Year",
            "description": (
                "5 years of daily historical weather data for 10 major global cities: "
                "New York, London, Tokyo, Mumbai, Sydney, Paris, Moscow, Cape Town, Sao Paulo, Beijing. "
                "Includes max/min temperatures, precipitation, rain, and snowfall. "
                "Sourced from Open-Meteo Historical API."
            ),
            "tags": ["weather", "climate", "cities", "time-series", "environment"],
            "license": "CC-BY 4.0",
            "source": "Open-Meteo Historical Weather API",
            "dataframe": final_df,
            "filename": "global_major_cities_weather_5yr.csv",
            "config": {"remove_nulls": False}, # Keep nulls to maintain time series continuity
        }]
