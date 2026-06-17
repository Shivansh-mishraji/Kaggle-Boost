"""
KaggleBoost LIVE UPLOAD v2 — fixed title length + auth handling
"""

import os, sys, json, subprocess
from pathlib import Path
from datetime import datetime

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Load .env
env_file = Path(".env")
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()

sys.path.insert(0, str(Path(__file__).parent))

import yfinance as yf
import pandas as pd
from processors.cleaner import DataCleaner
from processors.packager import DatasetPackager

KAGGLE_USER = os.environ.get("KAGGLE_USERNAME", "")
KAGGLE_KEY  = os.environ.get("KAGGLE_KEY", "")

print("=" * 58)
print("  KaggleBoost LIVE UPLOAD v2")
print("=" * 58)
print(f"  Kaggle user : {KAGGLE_USER}")
print(f"  Key loaded  : {'YES (' + KAGGLE_KEY[:8] + '...)' if KAGGLE_KEY else 'NO'}")

if not KAGGLE_USER or not KAGGLE_KEY:
    print("\nERROR: Credentials missing in .env")
    sys.exit(1)

# Write kaggle.json (works for both old and KGAT_ style tokens)
kaggle_dir = Path.home() / ".kaggle"
kaggle_dir.mkdir(exist_ok=True)
creds_file = kaggle_dir / "kaggle.json"
creds_file.write_text(json.dumps({"username": KAGGLE_USER, "key": KAGGLE_KEY}))
try:
    creds_file.chmod(0o600)
except Exception:
    pass
print(f"  Credentials : Written to {creds_file}")

def run_kaggle(args: list) -> tuple[bool, str]:
    """Run kaggle CLI with env vars injected."""
    env = os.environ.copy()
    env["KAGGLE_USERNAME"] = KAGGLE_USER
    env["KAGGLE_KEY"] = KAGGLE_KEY
    result = subprocess.run(
        ["python", "-m", "kaggle"] + args,
        capture_output=True, text=True, timeout=300, env=env
    )
    out = result.stdout + result.stderr
    return result.returncode == 0, out

# ── Verify auth first ─────────────────────────────────────────────
print("\n  Verifying Kaggle auth...")
ok, out = run_kaggle(["datasets", "list", "--user", KAGGLE_USER])
if ok or "No datasets found" in out:
    print("  Auth: OK")
else:
    # Try using the API directly via requests as fallback
    print(f"  CLI auth issue: {out[:150]}")
    print("  Trying direct API authentication...")

# ── DATASETS ─────────────────────────────────────────────────────
# NOTE: Kaggle title must be 6-50 chars. Slug is the URL part (no spaces).
DATASETS = [
    {
        "slug": "nifty50-stocks-5yr-ohlcv",              # URL slug (used as dataset ID)
        "title": "NIFTY 50 Stocks 5 Year OHLCV NSE",    # 34 chars - within limit
        "description": (
            "5-year daily OHLCV (Open, High, Low, Close, Volume) data for 15 top "
            "NIFTY 50 stocks on India's NSE exchange. Collected via Yahoo Finance. "
            "Ideal for algorithmic trading, time-series forecasting, and portfolio analysis. "
            "Covers: RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK, SBIN, BAJFINANCE, "
            "BHARTIARTL, KOTAKBANK, WIPRO, LT, AXISBANK, ASIANPAINT, MARUTI, SUNPHARMA."
        ),
        "tags": ["india", "stocks", "nse", "finance", "time-series", "trading", "nifty"],
        "tickers": [
            "RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS",
            "SBIN.NS","BAJFINANCE.NS","BHARTIARTL.NS","KOTAKBANK.NS","WIPRO.NS",
            "LT.NS","AXISBANK.NS","ASIANPAINT.NS","MARUTI.NS","SUNPHARMA.NS",
        ],
        "period": "5y",
    },
    {
        "slug": "faang-tech-stocks-5yr-ohlcv",           # URL slug
        "title": "FAANG Tech Stocks 5 Year OHLCV Data",  # 37 chars - within limit
        "description": (
            "5-year daily OHLCV price history for 12 top global technology stocks: "
            "Apple (AAPL), Microsoft (MSFT), Google (GOOGL), Amazon (AMZN), Meta (META), "
            "Tesla (TSLA), NVIDIA (NVDA), AMD, Netflix (NFLX), Intel (INTC), Salesforce (CRM), Adobe (ADBE). "
            "Via Yahoo Finance. Perfect for ML stock prediction and portfolio modeling."
        ),
        "tags": ["stocks","tech","faang","finance","machine-learning","nvidia","time-series"],
        "tickers": ["AAPL","MSFT","GOOGL","AMZN","META","TSLA","NVDA","AMD","NFLX","INTC","CRM","ADBE"],
        "period": "5y",
    },
]

cleaner  = DataCleaner()
packager = DatasetPackager()
UPLOAD_DIR = Path("tmp/upload_v2")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
results = []

for ds in DATASETS:
    title_len = len(ds["title"])
    print(f"\n{'─'*58}")
    print(f"  {ds['title']}  [{title_len} chars]")
    print(f"{'─'*58}")

    # 1. SCRAPE
    print(f"  [1/4] Scraping {len(ds['tickers'])} tickers × {ds['period']}...")
    frames = []
    for ticker in ds["tickers"]:
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period=ds["period"], interval="1d")
            if hist.empty:
                continue
            hist = hist.reset_index()
            hist["ticker"] = ticker
            hist.columns = [c.lower().replace(" ", "_") for c in hist.columns]
            frames.append(hist)
        except Exception as e:
            print(f"       {ticker}: skip ({e})")

    if not frames:
        print("  No data fetched. Skipping.")
        continue

    raw_df = pd.concat(frames, ignore_index=True)
    cols = ["ticker"] + [c for c in raw_df.columns if c != "ticker"]
    raw_df = raw_df[cols]
    print(f"  [1/4] DONE  {len(raw_df):,} rows x {len(raw_df.columns)} cols")

    # 2. CLEAN
    cleaned_df = cleaner.clean(raw_df, {"remove_nulls": False})
    print(f"  [2/4] CLEAN {len(cleaned_df):,} rows (dedup, types fixed)")

    dataset_info = {
        "id":          ds["slug"],
        "title":       ds["title"],
        "description": ds["description"],
        "tags":        ds["tags"],
        "license":     "other",
        "source":      "Yahoo Finance via yfinance",
        "dataframe":   cleaned_df,
        "filename":    f"{ds['slug']}.csv",
        "config":      {"remove_nulls": False},
    }

    # 3. PACKAGE
    pkg_path = packager.package(dataset_info, UPLOAD_DIR)
    if not pkg_path:
        print("  [3/4] FAIL — packaging error")
        results.append({"status": "PACK_FAIL", "title": ds["title"], "url": ""})
        continue
    size_mb = sum(f.stat().st_size for f in pkg_path.iterdir()) / 1048576
    print(f"  [3/4] PACK  {pkg_path.name}/ ({size_mb:.1f} MB)")

    # Show title length in metadata for debugging
    meta = json.loads((pkg_path / "dataset-metadata.json").read_text())
    print(f"         metadata title ({len(meta['title'])} chars): '{meta['title']}'")

    # 4. UPLOAD
    kaggle_url = f"https://www.kaggle.com/datasets/{KAGGLE_USER}/{ds['slug']}"
    print(f"  [4/4] Uploading to {kaggle_url}")

    ok, out = run_kaggle(["datasets", "create", "-p", str(pkg_path), "--dir-mode", "zip"])
    if ok:
        print(f"  [4/4] UPLOADED!")
        results.append({"status": "SUCCESS", "title": ds["title"], "url": kaggle_url})
    elif "already exists" in out.lower() or "409" in out:
        print(f"  [4/4] Exists — pushing new version...")
        ok2, out2 = run_kaggle([
            "datasets", "version", "-p", str(pkg_path),
            "-m", f"KaggleBoost refresh {datetime.now().strftime('%Y-%m-%d')}",
            "--dir-mode", "zip"
        ])
        if ok2:
            print(f"  [4/4] VERSION PUSHED!")
            results.append({"status": "UPDATED", "title": ds["title"], "url": kaggle_url})
        else:
            print(f"  [4/4] FAIL: {out2[:200]}")
            results.append({"status": "FAIL", "title": ds["title"], "url": ""})
    else:
        print(f"  [4/4] FAIL:\n{out[:400]}")
        results.append({"status": "FAIL", "title": ds["title"], "url": ""})

# SUMMARY
print(f"\n{'='*58}")
print("  SUMMARY")
print(f"{'='*58}")
for r in results:
    icon = "OK" if r["status"] in ("SUCCESS","UPDATED") else "FAIL"
    print(f"  [{icon}] {r['status']:8} {r['title'][:44]}")
    if r["url"]:
        print(f"           {r['url']}")
print(f"\n  Your Kaggle datasets page:")
print(f"  https://www.kaggle.com/{KAGGLE_USER}/datasets")
