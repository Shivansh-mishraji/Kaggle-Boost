# KaggleBoost — Autonomous Kaggle Profile Enhancement

> 🤖 Automatically scrapes high-demand open data, cleans it, and uploads professional datasets to your Kaggle profile every 3 days — **100% free, runs on GitHub Actions**.

[![KaggleBoost](https://github.com/Shivansh-mishraji/Kaggle-Boost/actions/workflows/scrape_and_upload.yml/badge.svg)](https://github.com/Shivansh-mishraji/Kaggle-Boost/actions)
[![Kaggle Profile](https://img.shields.io/badge/Kaggle-shivansh7275-blue?logo=kaggle)](https://www.kaggle.com/shivansh7275)

---

## 🚀 What It Does

1. **Scrapes** openly licensed data from: World Bank, NASA, Our World in Data, India Open Data, Yahoo Finance
2. **Cleans** the data (removes nulls, fixes types, strips PII, deduplicates)
3. **Packages** it with professional README + metadata
4. **Uploads** to your Kaggle profile automatically every 3 days
5. **Tracks** upload history to avoid duplicates

---

## ⚡ Quick Setup (5 minutes)

### Step 1: Fork this repo
Click **Fork** on GitHub → [github.com/Shivansh-mishraji/Kaggle-Boost](https://github.com/Shivansh-mishraji/Kaggle-Boost)

### Step 2: Add your Kaggle credentials as GitHub Secrets
1. Go to your Kaggle profile → **Settings** → **API** → **Create New Token**
2. Download `kaggle.json` — it contains `username` and `key`
3. In your GitHub repo: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
4. Add two secrets:
   - `KAGGLE_USERNAME` = `shivansh7275`
   - `KAGGLE_KEY` = the key from your `kaggle.json`

### Step 3: Enable GitHub Actions
- Go to **Actions** tab → Click **"I understand my workflows, go ahead and enable them"**

### Step 4: Run it!
- Go to **Actions** → **KaggleBoost** → **Run workflow** (for immediate first run)
- After that, it runs **automatically every 3 days** ☁️

---

## 📊 Data Sources

| Source | Data Type | License |
|--------|-----------|---------|
| 🌍 World Bank | GDP, population, CO2, internet | CC-BY 4.0 |
| 🚀 NASA | APOD archive, Near Earth Objects | Public Domain |
| 🏥 Our World in Data | Energy, COVID-19, happiness | CC-BY 4.0 |
| 🇮🇳 India Open Data | Elections, IPL cricket | ODbL / Open |
| 📈 Yahoo Finance | NIFTY 50, FAANG stocks | ToS (research) |

---

## 🗂️ Project Structure

```
kaggle-boost/
├── .github/workflows/     # GitHub Actions (the magic!)
├── scrapers/              # One scraper per data source
├── processors/            # Clean + package the data
├── uploader/              # Kaggle API wrapper
├── logs/                  # Upload history (auto-updated)
├── main.py                # Entry point
└── requirements.txt
```

---

## 🛠️ Run Locally

```bash
# Clone the repo
git clone https://github.com/Shivansh-mishraji/Kaggle-Boost.git
cd kaggle-boost

# Install dependencies
pip install -r requirements.txt

# Set credentials (Windows PowerShell)
$env:KAGGLE_USERNAME = "shivansh7275"
$env:KAGGLE_KEY      = "your_kaggle_api_key"

# Dry run (no upload — safe for testing)
python main.py --dry-run

# Full run (uploads to Kaggle)
python main.py
```

---

## 📈 Expected Kaggle Growth

| Timeframe | Datasets | Profile Views | Followers |
|-----------|----------|---------------|-----------|
| Month 1 | 4–8 | +200% | 5–20 |
| Month 3 | 15–25 | +500% | 50–100 |
| Month 6 | 30–50 | +1000% | 200+ |

---

## ⚖️ Legal & Ethics

- ✅ Only uses **openly licensed** data (CC-BY, Public Domain, ODbL)
- ✅ Respects API rate limits
- ✅ Automatic PII detection and masking
- ✅ All sources credited in dataset READMEs
- ❌ Never scrapes paywalled content

---

*Built with ❤️ by [Shivansh Mishra](https://www.kaggle.com/shivansh7275) · [GitHub](https://github.com/Shivansh-mishraji/Kaggle-Boost)*
