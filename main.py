"""
KaggleBoost — Autonomous Kaggle Profile Enhancement System
Entry point: orchestrates scraping, cleaning, packaging, and uploading.

Usage:
    python main.py              # Full run (scrape + upload)
    python main.py --dry-run   # Scrape + package only (no upload)
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Windows UTF-8 fix: prevent UnicodeEncodeError for emoji in cp1252 terminals
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Load .env file
env_file = Path(".env")
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from scrapers.world_bank import WorldBankScraper
from scrapers.nasa_data import NASAScraper
from scrapers.india_gov import IndiaGovScraper
from scrapers.owid import OWIDScraper
from scrapers.stock_market import StockMarketScraper
from scrapers.crypto_market import CryptoMarketScraper
from scrapers.open_meteo import OpenMeteoScraper
from scrapers.trending import TrendingTopicsScraper
from processors.cleaner import DataCleaner
from processors.packager import DatasetPackager
from uploader.kaggle_api import KaggleUploader

console = Console(highlight=False)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/kaggleboost.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("kaggleboost")

HISTORY_FILE = Path("logs/upload_history.json")
RAW_DIR = Path("tmp/raw")
PACKAGED_DIR = Path("tmp/packaged")


def load_history() -> dict:
    """Load upload history to avoid duplicates."""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return {}


def save_history(history: dict):
    """Save upload history."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def get_active_scrapers(run_mode: str = "auto") -> list:
    """
    Return scrapers based on trending topics and rotation strategy.
    Prioritizes high-demand, legal, public data.
    """
    all_scrapers = [
        WorldBankScraper(),     # Global economic & social data — very high Kaggle demand
        IndiaGovScraper(),      # India-specific — niche but growing, less competition
        NASAScraper(),          # Space/climate — always trending
        OWIDScraper(),          # Health, environment — popular for analysis
        StockMarketScraper(),   # Finance — extremely high demand
        CryptoMarketScraper(),  # Crypto — extremely high demand
        OpenMeteoScraper(),     # Weather — essential ML dataset
    ]
    return all_scrapers


def run_pipeline(dry_run: bool = False):
    """Main pipeline: scrape → clean → package → upload."""
    mode_label = "[yellow]DRY RUN[/yellow] — no uploads" if dry_run else "[green]LIVE[/green]"
    console.print(Panel.fit(
        "[bold cyan]🚀 KaggleBoost Automation Starting[/bold cyan]\n"
        f"[dim]Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]\n"
        f"Mode: {mode_label}",
        border_style="cyan"
    ))

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PACKAGED_DIR.mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(exist_ok=True)

    history = load_history()
    uploader = KaggleUploader()
    cleaner = DataCleaner()
    packager = DatasetPackager()

    results = []
    scrapers = get_active_scrapers()

    for scraper in scrapers:
        console.print(f"\n[bold yellow]📡 Running scraper:[/bold yellow] {scraper.name}")
        try:
            datasets = scraper.scrape()
            for dataset_info in datasets:
                dataset_id = dataset_info.get("id")

                # Skip if already uploaded recently
                if dataset_id in history:
                    last_upload = history[dataset_id].get("last_upload", "")
                    console.print(f"  [dim]⏭ Skipping '{dataset_id}' (already uploaded: {last_upload})[/dim]")
                    continue

                console.print(f"  [green]✓ Got dataset:[/green] {dataset_info['title']}")

                # Clean the data
                cleaned_df = cleaner.clean(dataset_info["dataframe"], dataset_info.get("config", {}))
                dataset_info["dataframe"] = cleaned_df

                # Package into uploadable format
                package_path = packager.package(dataset_info, PACKAGED_DIR)

                if package_path:
                    if dry_run:
                        # Dry run — skip actual upload
                        kaggle_url = f"https://www.kaggle.com/datasets/{os.environ.get('KAGGLE_USERNAME','user')}/{dataset_id.replace('_','-')}"
                        console.print(f"  [dim yellow]🔍 DRY RUN — would upload to: {kaggle_url}[/dim yellow]")
                        results.append({
                            "status": "🔍 DRY RUN",
                            "dataset": dataset_info["title"],
                            "url": kaggle_url
                        })
                    else:
                        # Upload to Kaggle
                        success, kaggle_url = uploader.upload(package_path, dataset_info)
                        if success:
                            history[dataset_id] = {
                                "title": dataset_info["title"],
                                "last_upload": datetime.now().isoformat(),
                                "kaggle_url": kaggle_url,
                                "source": scraper.name
                            }
                            results.append({
                                "status": "✅ SUCCESS",
                                "dataset": dataset_info["title"],
                                "url": kaggle_url
                            })
                            console.print(f"  [bold green]🎉 Uploaded:[/bold green] {kaggle_url}")
                        else:
                            results.append({
                                "status": "❌ FAILED",
                                "dataset": dataset_info["title"],
                                "url": ""
                            })
        except Exception as e:
            logger.error(f"Scraper {scraper.name} failed: {e}", exc_info=True)
            results.append({
                "status": "❌ ERROR",
                "dataset": scraper.name,
                "url": str(e)
            })

    save_history(history)

    # Print summary table
    table = Table(title="📊 KaggleBoost Run Summary", border_style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Dataset")
    table.add_column("Kaggle URL")

    for r in results:
        table.add_row(r["status"], r["dataset"][:50], r["url"])

    console.print("\n")
    console.print(table)
    console.print(Panel.fit(
        f"[bold green]Run complete! {sum(1 for r in results if 'SUCCESS' in r['status'])} datasets uploaded.[/bold green]",
        border_style="green"
    ))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KaggleBoost — Autonomous Kaggle Dataset Uploader")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=os.environ.get("DRY_RUN", "false").lower() == "true",
        help="Scrape and package data but do not upload to Kaggle"
    )
    args = parser.parse_args()
    run_pipeline(dry_run=args.dry_run)
