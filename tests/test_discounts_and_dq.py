"""Regression tests for discount handling and data quality row-count reconciliation."""

import pandas as pd
from retail_analytics.cleaning.cleaning import clean_transactions


def test_missing_discount_column_defaults_to_zero():
    raw_df = pd.DataFrame([
        {"transaction_id": "T1", "transaction_date": "2026-05-01", "sku": "SKU-1", "quantity": 2, "unit_price": 10000},
    ])
    clean_df, _, dq = clean_transactions(raw_df)
    assert len(clean_df) == 1
    assert clean_df.iloc[0]["discount_amount"] == 0.0
    assert clean_df.iloc[0]["gross_sales"] == 20000.0
    assert clean_df.iloc[0]["net_sales"] == 20000.0
    assert dq.invalid_discount_count == 0


def test_blank_discount_cell_defaults_to_zero():
    raw_df = pd.DataFrame([
        {"transaction_id": "T1", "transaction_date": "2026-05-01", "sku": "SKU-1", "quantity": 2, "unit_price": 10000, "discount_amount": ""},
        {"transaction_id": "T2", "transaction_date": "2026-05-01", "sku": "SKU-1", "quantity": 1, "unit_price": 10000, "discount_amount": None},
    ])
    clean_df, _, dq = clean_transactions(raw_df)
    assert len(clean_df) == 2
    assert clean_df.iloc[0]["discount_amount"] == 0.0
    assert clean_df.iloc[1]["discount_amount"] == 0.0
    assert dq.invalid_discount_count == 0


def test_valid_numeric_discount_calculated():
    raw_df = pd.DataFrame([
        {"transaction_id": "T1", "transaction_date": "2026-05-01", "sku": "SKU-1", "quantity": 3, "unit_price": 10000, "discount_amount": 5000},
    ])
    clean_df, _, dq = clean_transactions(raw_df)
    assert len(clean_df) == 1
    assert clean_df.iloc[0]["gross_sales"] == 30000.0
    assert clean_df.iloc[0]["discount_amount"] == 5000.0
    assert clean_df.iloc[0]["net_sales"] == 25000.0
    assert dq.invalid_discount_count == 0


def test_malformed_non_empty_discount_quarantined_not_silent_zero():
    # Value "oops" must NOT be silently accepted as 0.0!
    raw_df = pd.DataFrame([
        {"transaction_id": "T-VALID", "transaction_date": "2026-05-01", "sku": "SKU-1", "quantity": 1, "unit_price": 10000, "discount_amount": 1000},
        {"transaction_id": "T-MALFORMED", "transaction_date": "2026-05-01", "sku": "SKU-1", "quantity": 1, "unit_price": 10000, "discount_amount": "oops"},
        {"transaction_id": "T-NA-TEXT", "transaction_date": "2026-05-01", "sku": "SKU-1", "quantity": 1, "unit_price": 10000, "discount_amount": "N/A"},
    ])
    clean_df, quarantine_df, dq = clean_transactions(raw_df)
    assert len(clean_df) == 1
    assert len(quarantine_df) == 2
    assert dq.invalid_discount_count == 2
    assert dq.quarantined_rows_count == 2

    # Verify quarantine reasons contain descriptive details
    reasons = " ".join(quarantine_df["quarantine_reason"])
    assert "invalid discount" in reasons


def test_negative_discount_quarantined():
    raw_df = pd.DataFrame([
        {"transaction_id": "T-NEG", "transaction_date": "2026-05-01", "sku": "SKU-1", "quantity": 1, "unit_price": 10000, "discount_amount": -1500},
    ])
    clean_df, quarantine_df, dq = clean_transactions(raw_df)
    assert len(clean_df) == 0
    assert len(quarantine_df) == 1
    assert dq.invalid_discount_count == 1
    assert "invalid discount" in quarantine_df.iloc[0]["quarantine_reason"]


def test_data_quality_strict_row_count_reconciliation():
    raw_df = pd.DataFrame([
        # 1. Valid clean row
        {"transaction_id": "T1", "transaction_date": "2026-05-01", "sku": "SKU-1", "quantity": 1, "unit_price": 10000, "discount_amount": 0},
        # 2. Exact duplicate of row 1 (should be dropped in exact_duplicates)
        {"transaction_id": "T1", "transaction_date": "2026-05-01", "sku": "SKU-1", "quantity": 1, "unit_price": 10000, "discount_amount": 0},
        # 3. Missing mandatory field (transaction_id missing)
        {"transaction_id": "", "transaction_date": "2026-05-01", "sku": "SKU-1", "quantity": 1, "unit_price": 10000, "discount_amount": 0},
        # 4. Invalid date
        {"transaction_id": "T2", "transaction_date": "INVALID_DATE", "sku": "SKU-1", "quantity": 1, "unit_price": 10000, "discount_amount": 0},
        # 5. Invalid quantity (negative)
        {"transaction_id": "T3", "transaction_date": "2026-05-01", "sku": "SKU-1", "quantity": -2, "unit_price": 10000, "discount_amount": 0},
        # 6. Invalid discount (malformed text)
        {"transaction_id": "T4", "transaction_date": "2026-05-01", "sku": "SKU-1", "quantity": 1, "unit_price": 10000, "discount_amount": "invalid_num"},
        # 7. Another valid clean row
        {"transaction_id": "T5", "transaction_date": "2026-05-02", "sku": "SKU-2", "quantity": 2, "unit_price": 15000, "discount_amount": 1000},
    ])

    clean_df, quarantine_df, dq = clean_transactions(raw_df)

    # Invariant: input_rows == output_rows + quarantined_rows + exact_duplicates
    assert dq.input_rows == 7
    assert dq.output_rows == 2
    assert dq.exact_duplicates_count == 1
    assert dq.quarantined_rows_count == 4
    assert len(quarantine_df) == 4
    assert dq.input_rows == dq.output_rows + dq.quarantined_rows_count + dq.exact_duplicates_count

