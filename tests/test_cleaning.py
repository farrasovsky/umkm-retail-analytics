"""Tests for data cleaning, normalization, and quality validation."""

import pandas as pd
from retail_analytics.cleaning.cleaning import clean_transactions


def test_sku_formatting_normalization():
    raw_df = pd.DataFrame([
        {"transaction_id": "TXN-1", "transaction_date": "2026-05-01", "sku": "  sku-001  ", "quantity": 1, "unit_price": 10000},
        {"transaction_id": "TXN-2", "transaction_date": "2026-05-01", "sku": "SKU-002", "quantity": 2, "unit_price": 15000},
    ])
    clean_df, _, dq = clean_transactions(raw_df)
    assert clean_df.iloc[0]["sku"] == "SKU-001"
    assert dq.corrected_sku_formatting_count == 1
    assert dq.output_rows == 2


def test_product_master_alias_resolution():
    master_df = pd.DataFrame([
        {"sku": "SKU-0005", "product_name": "Mi Goreng", "category": "Makanan", "sku_aliases": "MIGORENG;SKU0005"},
    ])
    raw_df = pd.DataFrame([
        {"transaction_id": "TXN-1", "transaction_date": "2026-05-01", "sku": "MIGORENG", "quantity": 2, "unit_price": 3500},
    ])
    clean_df, _, _ = clean_transactions(raw_df, product_master_df=master_df)
    assert clean_df.iloc[0]["sku"] == "SKU-0005"
    assert clean_df.iloc[0]["product_name"] == "Mi Goreng"
    assert clean_df.iloc[0]["category"] == "Makanan"


def test_exact_duplicates_vs_valid_multiline_orders():
    raw_df = pd.DataFrame([
        # Valid multi-line order: TXN-1 has 2 distinct SKUs
        {"transaction_id": "TXN-1", "transaction_date": "2026-05-01", "sku": "SKU-001", "quantity": 1, "unit_price": 10000, "customer_id": "C-1"},
        {"transaction_id": "TXN-1", "transaction_date": "2026-05-01", "sku": "SKU-002", "quantity": 2, "unit_price": 20000, "customer_id": "C-1"},
        # Exact duplicate of the second row
        {"transaction_id": "TXN-1", "transaction_date": "2026-05-01", "sku": "SKU-002", "quantity": 2, "unit_price": 20000, "customer_id": "C-1"},
    ])
    clean_df, _, dq = clean_transactions(raw_df)
    assert len(clean_df) == 2  # One duplicate dropped
    assert dq.exact_duplicates_count == 1
    assert dq.clean_unique_transactions == 1


def test_invalid_records_quarantine():
    raw_df = pd.DataFrame([
        {"transaction_id": "TXN-VALID", "transaction_date": "2026-05-01", "sku": "SKU-001", "quantity": 1, "unit_price": 10000},
        {"transaction_id": "TXN-BAD-DATE", "transaction_date": "INVALID_DATE", "sku": "SKU-001", "quantity": 1, "unit_price": 10000},
        {"transaction_id": "TXN-BAD-QTY", "transaction_date": "2026-05-01", "sku": "SKU-001", "quantity": -5, "unit_price": 10000},
        {"transaction_id": "", "transaction_date": "2026-05-01", "sku": "SKU-001", "quantity": 1, "unit_price": 10000},
    ])
    clean_df, quarantine_df, dq = clean_transactions(raw_df)
    assert len(clean_df) == 1
    assert len(quarantine_df) == 3
    assert dq.quarantined_rows_count == 3
    assert dq.invalid_date_count == 1
    assert dq.invalid_quantity_price_count == 1
    assert dq.missing_required_fields_count == 1


def test_customer_id_anonymity_preservation():
    raw_df = pd.DataFrame([
        {"transaction_id": "TXN-1", "transaction_date": "2026-05-01", "sku": "SKU-001", "quantity": 1, "unit_price": 10000, "customer_id": ""},
        {"transaction_id": "TXN-2", "transaction_date": "2026-05-01", "sku": "SKU-001", "quantity": 1, "unit_price": 10000, "customer_id": "nan"},
        {"transaction_id": "TXN-3", "transaction_date": "2026-05-01", "sku": "SKU-001", "quantity": 1, "unit_price": 10000, "customer_id": "CUST-001"},
    ])
    clean_df, _, _ = clean_transactions(raw_df)
    assert pd.isna(clean_df.iloc[0]["customer_id"])
    assert pd.isna(clean_df.iloc[1]["customer_id"])
    assert clean_df.iloc[2]["customer_id"] == "CUST-001"
