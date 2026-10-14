"""Tests for data ingestion, loaders, and schema validation."""

import pytest
import pandas as pd
from pathlib import Path

from retail_analytics.ingestion.loaders import (
    load_inventory_csv,
    load_product_master_csv,
    load_transactions_csv,
)
from retail_analytics.ingestion.schemas import (
    SchemaValidationError,
    validate_inventory_schema,
    validate_product_master_schema,
    validate_transaction_schema,
)


def test_load_valid_transactions_csv(tmp_path: Path):
    csv_file = tmp_path / "valid_txns.csv"
    csv_file.write_text(
        "transaction_id,transaction_date,sku,quantity,unit_price\n"
        "TXN-001,2026-05-01,SKU-001,2,15000\n"
        "TXN-002,2026-05-02,SKU-002,1,25000\n"
    )
    df = load_transactions_csv(csv_file)
    assert len(df) == 2
    assert "transaction_id" in df.columns
    assert "customer_id" in df.columns  # Optional column auto-filled
    assert "discount_amount" in df.columns


def test_missing_transaction_file():
    with pytest.raises(FileNotFoundError):
        load_transactions_csv("non_existent_file.csv")


def test_empty_transaction_file(tmp_path: Path):
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("")
    with pytest.raises(SchemaValidationError, match="completely empty"):
        load_transactions_csv(empty_csv)


def test_missing_mandatory_transaction_columns(tmp_path: Path):
    bad_csv = tmp_path / "missing_cols.csv"
    bad_csv.write_text(
        "transaction_id,sku\n"
        "TXN-001,SKU-001\n"
    )
    with pytest.raises(SchemaValidationError, match="Missing mandatory column"):
        load_transactions_csv(bad_csv)


def test_inventory_and_master_loaders(tmp_path: Path):
    inv_csv = tmp_path / "inv.csv"
    inv_csv.write_text(
        "sku,stock_on_hand,reorder_point\n"
        "SKU-001,50,20\n"
    )
    inv_df = load_inventory_csv(inv_csv)
    assert len(inv_df) == 1
    assert "stock_on_hand" in inv_df.columns

    pm_csv = tmp_path / "pm.csv"
    pm_csv.write_text(
        "sku,product_name,category\n"
        "SKU-001,Test Item,Food\n"
    )
    pm_df = load_product_master_csv(pm_csv)
    assert len(pm_df) == 1
    assert pm_df.iloc[0]["product_name"] == "Test Item"

