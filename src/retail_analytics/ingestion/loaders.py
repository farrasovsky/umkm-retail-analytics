"""Robust CSV loaders for transactions, inventory snapshots, and product masters."""

from __future__ import annotations

from pathlib import Path
import pandas as pd

from .schemas import (
    INVENTORY_OPTIONAL_COLUMNS,
    PRODUCT_MASTER_OPTIONAL_COLUMNS,
    SchemaValidationError,
    TRANSACTION_OPTIONAL_COLUMNS,
    validate_inventory_schema,
    validate_product_master_schema,
    validate_transaction_schema,
)


def _read_csv_safe(path: Path | str, dataset_name: str) -> pd.DataFrame:
    """Read a CSV file safely handling common encodings and validating existence."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"{dataset_name} file not found at: {file_path}")

    if file_path.stat().st_size == 0:
        raise SchemaValidationError(f"{dataset_name} file is completely empty: {file_path}")

    # Attempt UTF-8 with BOM handling first, fallback to latin-1
    encodings = ["utf-8-sig", "utf-8", "latin-1"]
    last_err: Exception | None = None

    for enc in encodings:
        try:
            df = pd.read_csv(file_path, encoding=enc, dtype=str)
            # Strip whitespace from column names
            df.columns = df.columns.str.strip().str.lower()
            return df
        except UnicodeDecodeError as err:
            last_err = err
            continue

    raise SchemaValidationError(
        f"Unable to decode {dataset_name} at {file_path}. Error: {last_err}"
    )


def load_transactions_csv(path: Path | str) -> pd.DataFrame:
    """Load and validate raw retail transactions CSV.

    Parameters
    ----------
    path : Path | str
        Path to the transactions CSV file.

    Returns
    -------
    pd.DataFrame
        DataFrame with standardized column names and filled optional columns.
    """
    df = _read_csv_safe(path, "Transactions")
    validate_transaction_schema(df)

    # Ensure all optional columns exist
    for col, default_val in TRANSACTION_OPTIONAL_COLUMNS.items():
        if col not in df.columns:
            df[col] = default_val

    return df


def load_inventory_csv(path: Path | str) -> pd.DataFrame:
    """Load and validate retail inventory snapshot CSV.

    Parameters
    ----------
    path : Path | str
        Path to the inventory snapshot CSV file.

    Returns
    -------
    pd.DataFrame
        DataFrame with standardized column names and validated inventory columns.
    """
    df = _read_csv_safe(path, "Inventory Snapshot")
    validate_inventory_schema(df)

    for col, default_val in INVENTORY_OPTIONAL_COLUMNS.items():
        if col not in df.columns:
            df[col] = default_val

    return df


def load_product_master_csv(path: Path | str) -> pd.DataFrame:
    """Load and validate product master catalog CSV.

    Parameters
    ----------
    path : Path | str
        Path to the product master CSV file.

    Returns
    -------
    pd.DataFrame
        DataFrame with standardized column names and validated product master columns.
    """
    df = _read_csv_safe(path, "Product Master")
    validate_product_master_schema(df)

    for col, default_val in PRODUCT_MASTER_OPTIONAL_COLUMNS.items():
        if col not in df.columns:
            df[col] = default_val

    return df

