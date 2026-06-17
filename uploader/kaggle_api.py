"""Kaggle API uploader — handles create vs version logic."""

import os
import json
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class KaggleUploader:
    """
    Wraps the Kaggle CLI to upload datasets.
    Requires KAGGLE_USERNAME and KAGGLE_KEY environment variables.
    """

    def __init__(self):
        self.username = os.environ.get("KAGGLE_USERNAME", "")
        self.key = os.environ.get("KAGGLE_KEY", "")

        if not self.username or not self.key:
            logger.warning(
                "KAGGLE_USERNAME or KAGGLE_KEY not set. "
                "Upload will fail. Set these as GitHub Secrets."
            )

        # Write kaggle.json if credentials are provided via env vars
        self._setup_credentials()

    def _setup_credentials(self):
        """Create ~/.kaggle/kaggle.json from environment variables."""
        if not self.username or not self.key:
            return

        kaggle_dir = Path.home() / ".kaggle"
        kaggle_dir.mkdir(exist_ok=True)
        creds_file = kaggle_dir / "kaggle.json"

        creds = {"username": self.username, "key": self.key}
        with open(creds_file, "w") as f:
            json.dump(creds, f)
        creds_file.chmod(0o600)
        logger.info("Kaggle credentials configured.")

    def _dataset_exists(self, dataset_slug: str) -> bool:
        """Check if a dataset already exists on Kaggle."""
        full_ref = f"{self.username}/{dataset_slug}"
        result = subprocess.run(
            ["python", "-m", "kaggle", "datasets", "status", full_ref],
            capture_output=True, text=True
        )
        return result.returncode == 0

    def upload(self, package_path: Path, dataset_info: dict) -> tuple[bool, str]:
        """
        Upload dataset to Kaggle. Creates new dataset or adds a new version.
        Returns (success: bool, kaggle_url: str)
        """
        dataset_id = dataset_info["id"]
        dataset_slug = dataset_id.replace("_", "-")
        kaggle_ref = f"{self.username}/{dataset_slug}"
        kaggle_url = f"https://www.kaggle.com/datasets/{kaggle_ref}"

        if not self.username:
            logger.error("Cannot upload: KAGGLE_USERNAME not configured.")
            return False, ""

        exists = self._dataset_exists(dataset_slug)

        if exists:
            # Create a new version
            logger.info(f"Dataset {dataset_slug} exists. Creating new version...")
            cmd = [
                "python", "-m", "kaggle", "datasets", "version",
                "-p", str(package_path),
                "-m", f"Auto-updated by KaggleBoost — fresh data pull",
                "--dir-mode", "zip"
            ]
        else:
            # Create new dataset
            logger.info(f"Creating new dataset: {dataset_slug}")
            cmd = [
                "python", "-m", "kaggle", "datasets", "create",
                "-p", str(package_path),
                "--dir-mode", "zip"
            ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                logger.info(f"✅ Upload successful: {kaggle_url}")
                logger.debug(f"Kaggle CLI output: {result.stdout}")
                return True, kaggle_url
            else:
                logger.error(f"❌ Upload failed for {dataset_slug}:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
                return False, ""

        except subprocess.TimeoutExpired:
            logger.error(f"Upload timed out for {dataset_slug}")
            return False, ""
        except Exception as e:
            logger.error(f"Upload error for {dataset_slug}: {e}")
            return False, ""
