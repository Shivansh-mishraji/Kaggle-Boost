"""Data cleaning pipeline — ensures all datasets are clean and high-quality."""

import pandas as pd
import logging
import re

logger = logging.getLogger(__name__)


class DataCleaner:
    """
    Standardizes and cleans raw dataframes before packaging.
    High-quality data = higher Kaggle usability score = more visibility.
    """

    def clean(self, df: pd.DataFrame, config: dict = None) -> pd.DataFrame:
        if config is None:
            config = {}

        logger.info(f"Cleaning dataframe: {df.shape[0]} rows × {df.shape[1]} cols")

        df = self._standardize_columns(df)
        df = self._convert_types(df, config)
        df = self._remove_duplicates(df)
        df = self._handle_nulls(df, config.get("remove_nulls", False))
        df = self._strip_whitespace(df)
        df = self._remove_pii(df)

        logger.info(f"After cleaning: {df.shape[0]} rows × {df.shape[1]} cols")
        return df

    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Lowercase, snake_case column names."""
        df.columns = [
            re.sub(r"[^a-z0-9_]", "_", c.strip().lower().replace(" ", "_")).strip("_")
            for c in df.columns
        ]
        # Remove duplicate columns
        df = df.loc[:, ~df.columns.duplicated()]
        return df

    def _convert_types(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        """Convert date and numeric columns to proper types."""
        for col in config.get("date_columns", []):
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        for col in config.get("numeric_columns", []):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Auto-detect numeric columns stored as strings
        for col in df.select_dtypes(include=["object"]).columns:
            try:
                converted = pd.to_numeric(df[col], errors="coerce")
                if converted.notna().sum() / max(len(df), 1) > 0.8:
                    df[col] = converted
            except Exception:
                pass

        return df

    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Drop exact duplicate rows."""
        before = len(df)
        df = df.drop_duplicates().reset_index(drop=True)
        dropped = before - len(df)
        if dropped:
            logger.info(f"Removed {dropped} duplicate rows")
        return df

    def _handle_nulls(self, df: pd.DataFrame, remove_nulls: bool = False) -> pd.DataFrame:
        """Handle null values based on config."""
        # Drop columns that are more than 90% null
        threshold = 0.9
        null_frac = df.isnull().mean()
        cols_to_drop = null_frac[null_frac > threshold].index.tolist()
        if cols_to_drop:
            logger.info(f"Dropping {len(cols_to_drop)} mostly-null columns: {cols_to_drop[:5]}")
            df = df.drop(columns=cols_to_drop)

        if remove_nulls:
            df = df.dropna().reset_index(drop=True)

        return df

    def _strip_whitespace(self, df: pd.DataFrame) -> pd.DataFrame:
        """Strip leading/trailing whitespace from string columns."""
        str_cols = df.select_dtypes(include=["object"]).columns
        for col in str_cols:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace("nan", pd.NA)
        return df

    def _remove_pii(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect and mask potential PII columns.
        Kaggle has strict rules about PII in datasets.
        """
        pii_patterns = [
            r"email", r"phone", r"mobile", r"ssn", r"passport",
            r"address", r"ip_address", r"credit_card", r"national_id"
        ]
        for col in df.columns:
            for pattern in pii_patterns:
                if re.search(pattern, col, re.IGNORECASE):
                    logger.warning(f"Potential PII column detected and masked: '{col}'")
                    df[col] = "[REDACTED]"
                    break
        return df
