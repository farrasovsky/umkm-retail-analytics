"""Regression tests for date parsing and reporting period calculations."""

from datetime import datetime
import pandas as pd
from retail_analytics.cleaning.dates import parse_date_series, parse_single_date
from retail_analytics.cleaning.cleaning import clean_transactions
from retail_analytics.analytics.sales import compute_monthly_sales, compute_sales_summary


def test_indonesian_slash_date_dayfirst():
    # 01/05/2026 must be May 1, 2026 (not January 5)
    parsed = parse_single_date("01/05/2026", dayfirst=True)
    assert parsed is not None
    assert parsed.year == 2026
    assert parsed.month == 5
    assert parsed.day == 1

    # 04/05/2026 must be May 4, 2026 (not April 5)
    parsed_04 = parse_single_date("04/05/2026", dayfirst=True)
    assert parsed_04 is not None
    assert parsed_04.year == 2026
    assert parsed_04.month == 5
    assert parsed_04.day == 4


def test_iso_date_parsing_precedence():
    # ISO date 2026-05-01 must always be May 1, 2026 even when dayfirst=True
    parsed_iso = parse_single_date("2026-05-01", dayfirst=True)
    assert parsed_iso is not None
    assert parsed_iso.year == 2026
    assert parsed_iso.month == 5
    assert parsed_iso.day == 1

    # Datetime with time component
    parsed_iso_dt = parse_single_date("2026-04-15 14:30:00", dayfirst=True)
    assert parsed_iso_dt is not None
    assert parsed_iso_dt.year == 2026
    assert parsed_iso_dt.month == 4
    assert parsed_iso_dt.day == 15
    assert parsed_iso_dt.hour == 14
    assert parsed_iso_dt.minute == 30


def test_invalid_dates_quarantine():
    assert parse_single_date("2026-02-30") is None
    assert parse_single_date("INVALID_DATE") is None
    assert parse_single_date("") is None
    assert parse_single_date(None) is None
    assert parse_single_date("1995-01-01") is None  # Out of range (< 2000)
    assert parse_single_date("2065-01-01") is None  # Out of range (> 2050)


def test_mixed_dates_in_clean_transactions():
    raw_df = pd.DataFrame([
        {"transaction_id": "T1", "transaction_date": "01/05/2026", "sku": "SKU-1", "quantity": 1, "unit_price": 10000},
        {"transaction_id": "T2", "transaction_date": "2026-05-02", "sku": "SKU-1", "quantity": 1, "unit_price": 10000},
        {"transaction_id": "T3", "transaction_date": "15/06/2026 10:00:00", "sku": "SKU-1", "quantity": 1, "unit_price": 10000},
        {"transaction_id": "T4", "transaction_date": "INVALID_DATE", "sku": "SKU-1", "quantity": 1, "unit_price": 10000},
    ])
    clean_df, quarantine_df, dq = clean_transactions(raw_df, dayfirst=True)
    assert len(clean_df) == 3
    assert len(quarantine_df) == 1
    assert dq.invalid_date_count == 1

    # T1 must be in May 2026
    row_t1 = clean_df[clean_df["transaction_id"] == "T1"].iloc[0]
    assert row_t1["transaction_date"].startswith("2026-05-01")

    # Monthly aggregation must show May and June
    monthly = compute_monthly_sales(clean_df)
    assert list(monthly["year_month"]) == ["2026-05", "2026-06"]


def test_reporting_period_derived_from_accepted_data():
    raw_df = pd.DataFrame([
        {"transaction_id": "T1", "transaction_date": "01/04/2026", "sku": "SKU-1", "quantity": 1, "unit_price": 10000},
        {"transaction_id": "T2", "transaction_date": "30/09/2026", "sku": "SKU-1", "quantity": 1, "unit_price": 10000},
    ])
    clean_df, _, _ = clean_transactions(raw_df, dayfirst=True)
    summary = compute_sales_summary(clean_df)
    assert summary.period_start == "2026-04-01"
    assert summary.period_end == "2026-09-30"
    assert summary.total_days == 183

