"""Dataset packager — creates upload-ready folders with metadata and README."""

import os
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
from jinja2 import Template

logger = logging.getLogger(__name__)

README_TEMPLATE = """# {{ title }}

## 📋 Dataset Overview
{{ description }}

## 📊 Dataset Info
| Property | Value |
|----------|-------|
| **Rows** | {{ row_count }} |
| **Columns** | {{ col_count }} |
| **File Size** | {{ file_size }} |
| **License** | {{ license }} |
| **Source** | {{ source }} |
| **Last Updated** | {{ last_updated }} |
| **Uploaded by** | [KaggleBoost](https://github.com/Shivansh-mishraji/Kaggle-Boost) |

## 📁 Column Descriptions
| Column | Data Type | Description |
|--------|-----------|-------------|
{% for col in columns %}| `{{ col.name }}` | {{ col.dtype }} | {{ col.description }} |
{% endfor %}

## 🔍 Sample Data (First 5 Rows)
```
{{ sample_data }}
```

## 📈 Summary Statistics
```
{{ stats }}
```

## 🏷️ Tags
{{ tags | join(', ') }}

## ⚖️ License
This dataset is licensed under **{{ license }}**.  
Original source: {{ source }}

## 🔗 How to Use
```python
import pandas as pd
df = pd.read_csv('/kaggle/input/{{ dataset_slug }}/{{ filename }}')
df.head()
```

---
*Dataset automatically collected, cleaned, and uploaded by [KaggleBoost](https://github.com/Shivansh-mishraji/Kaggle-Boost) — an open-source Kaggle profile automation tool.*
"""

METADATA_TEMPLATE = {
    "title": "",
    "id": "",
    "licenses": [{"name": "CC0-1.0"}],
    "keywords": [],
    "collaborators": [],
    "data": []
}

LICENSE_MAP = {
    "CC BY 4.0": "CC BY 4.0",
    "Public Domain (NASA)": "other",
    "NGOIMS": "other",
    "CC0": "CC0-1.0",
    "Open Source": "other",
    "Yahoo Finance Terms (for research/educational use)": "other",
    "Open Data Commons Open Database License (ODbL)": "ODbL-1.0",
}

KAGGLE_LICENSE_MAP = {
    "CC BY 4.0": "CC BY 4.0",
    "Public Domain (NASA)": "CC0-1.0",
    "NGOIMS": "other",
    "CC0": "CC0-1.0",
    "Open Source": "other",
    "Yahoo Finance Terms (for research/educational use)": "other",
    "Open Data Commons Open Database License (ODbL)": "ODbL-1.0",
}


class DatasetPackager:
    def package(self, dataset_info: dict, output_dir: Path) -> Path | None:
        """
        Package a dataset into a Kaggle-uploadable folder.
        Returns the path to the package folder, or None on failure.
        """
        dataset_id = dataset_info["id"]
        package_path = output_dir / dataset_id
        package_path.mkdir(parents=True, exist_ok=True)

        try:
            df: pd.DataFrame = dataset_info["dataframe"]
            filename = dataset_info.get("filename", f"{dataset_id}.csv")
            csv_path = package_path / filename

            # Save CSV
            df.to_csv(csv_path, index=False)
            file_size_kb = csv_path.stat().st_size / 1024
            file_size_str = f"{file_size_kb:.1f} KB" if file_size_kb < 1024 else f"{file_size_kb/1024:.2f} MB"

            # Generate column descriptions
            columns = []
            for col in df.columns:
                dtype = str(df[col].dtype)
                null_pct = round(df[col].isnull().mean() * 100, 1)
                columns.append({
                    "name": col,
                    "dtype": dtype,
                    "description": f"{null_pct}% null" if null_pct > 0 else "Complete"
                })

            # Generate README
            try:
                sample_data = df.head(5).to_string(index=False, max_cols=8)
            except Exception:
                sample_data = "See CSV file"

            try:
                stats = df.describe(include="all").to_string()
            except Exception:
                stats = "See CSV file"

            dataset_slug = dataset_id.replace("_", "-")
            tmpl = Template(README_TEMPLATE)
            readme_content = tmpl.render(
                title=dataset_info["title"],
                description=dataset_info["description"],
                row_count=f"{len(df):,}",
                col_count=len(df.columns),
                file_size=file_size_str,
                license=dataset_info.get("license", "See source"),
                source=dataset_info.get("source", ""),
                last_updated=datetime.now().strftime("%Y-%m-%d"),
                columns=columns,
                sample_data=sample_data,
                stats=stats,
                tags=dataset_info.get("tags", []),
                dataset_slug=dataset_slug,
                filename=filename,
            )

            with open(package_path / "README.md", "w", encoding="utf-8") as f:
                f.write(readme_content)

            # Generate dataset-metadata.json for Kaggle
            kaggle_username = os.environ.get("KAGGLE_USERNAME", "your-username")
            kaggle_license = KAGGLE_LICENSE_MAP.get(dataset_info.get("license", ""), "other")
            metadata = {
                "title": dataset_info["title"][:80],  # Kaggle title limit
                "id": f"{kaggle_username}/{dataset_slug}",
                "licenses": [{"name": kaggle_license}],
                "keywords": dataset_info.get("tags", [])[:10],  # Kaggle allows max 10 tags
                "collaborators": [],
                "data": [{"description": f"Main dataset file", "name": filename}],
            }
            with open(package_path / "dataset-metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Packaged: {dataset_id} → {package_path} ({file_size_str})")
            return package_path

        except Exception as e:
            logger.error(f"Packaging failed for {dataset_id}: {e}", exc_info=True)
            shutil.rmtree(package_path, ignore_errors=True)
            return None
