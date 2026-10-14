"""Schema definitions and contract validation for retail datasets."""

from __future__ import annotations

from typing import Iterable
import pandas as pd


class SchemaValidationError(ValueError):
    """Raised when an ingested file violates the mandatory data contract."""


TRANSACTION_REQUIRED_COLUMNS: tuple[str, ...] = (
    "transaction_id",
    "transaction_date",
    "sku",
    "quantity",
    "unit_price",
)

TRANSACTION_OPTIONAL_COLUMNS: dict[str, object] = {
    "customer_id": None,
    "product_id": None,
    "product_name": "Unknown Product",
    "category": "Uncategorized",
    "discount_amount": 0.0,
    "sales_channel": "Store",
    "payment_method": "Cash",
}

INVENTORY_REQUIRED_COLUMNS: tuple[str, ...] = (
    "sku",
    "stock_on_hand",
    "reorder_point",
)

INVENTORY_OPTIONAL_COLUMNS: dict[str, object] = {
    "product_id": None,
    "product_name": "Unknown Product",
    "category": "Uncategorized",
    "unit_cost": 0.0,
}

PRODUCT_MASTER_REQUIRED_COLUMNS: tuple[str, ...] = (
    "sku",
    "product_name",
    "category",
)

PRODUCT_MASTER_OPTIONAL_COLUMNS: dict[str, object] = {
    "product_id": None,
    "default_unit_price": 0.0,
    "sku_aliases": "",
}


def _check_missing_columns(
    df: pd.DataFrame,
    required: Iterable[str],
    dataset_name: str,
) -> None:
    """Validate that all required columns exist in the DataFrame."""
    missing = [col for col in required if col not in df.columns]
    if missing:
        missing_str = ", ".join(f"'{c}'" for c in missing)
        available_str = ", ".join(f"'{c}'" for c in df.columns)
        raise SchemaValidationError(
            f"Missing mandatory column(s) in {dataset_name}: [{missing_str}]. "
            f"Available columns: [{available_str}]."
        )


def validate_transaction_schema(df: pd.DataFrame) -> None:
    """Validate the raw transaction DataFrame against required columns."""
    _check_missing_columns(df, TRANSACTION_REQUIRED_COLUMNS, "Transactions")


def validate_inventory_schema(df: pd.DataFrame) -> None:
    """Validate the inventory snapshot DataFrame against required columns."""
    _check_missing_columns(df, INVENTORY_REQUIRED_COLUMNS, "Inventory Snapshot")


def validate_product_master_schema(df: pd.DataFrame) -> None:
    """Validate the product master DataFrame against required columns."""
    _check_missing_columns(df, PRODUCT_MASTER_REQUIRED_COLUMNS, "Product Master")

