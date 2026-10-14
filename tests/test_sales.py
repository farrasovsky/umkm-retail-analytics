"""Tests for sales KPIs and revenue analytics."""

import pandas as pd
from retail_analytics.analytics.sales import (
    compute_category_sales,
    compute_channel_sales,
    compute_monthly_sales,
    compute_sales_summary,
)


def test_sales_kpis_known_calculation():
    df = pd.DataFrame([
        {"transaction_id": "T1", "transaction_date": "2026-05-01 10:00:00", "quantity": 2, "unit_price": 10000, "discount_amount": 1000, "gross_sales": 20000, "net_sales": 19000, "sales_channel": "Store", "category": "Food"},
        {"transaction_id": "T1", "transaction_date": "2026-05-01 10:00:00", "quantity": 1, "unit_price": 5000, "discount_amount": 0, "gross_sales": 5000, "net_sales": 5000, "sales_channel": "Store", "category": "Food"},
        {"transaction_id": "T2", "transaction_date": "2026-05-02 11:00:00", "quantity": 3, "unit_price": 20000, "discount_amount": 0, "gross_sales": 60000, "net_sales": 60000, "sales_channel": "Online", "category": "Drinks"},
    ])
    summary = compute_sales_summary(df)
    assert summary.total_gross_sales == 85000.0
    assert summary.total_discount == 1000.0
    assert summary.total_net_sales == 84000.0
    assert summary.unique_transactions == 2
    assert summary.total_units_sold == 6
    assert summary.average_transaction_value == 42000.0  # 84000 / 2
    assert summary.average_items_per_transaction == 3.0   # 6 / 2


def test_monthly_sales_aggregation():
    df = pd.DataFrame([
        {"transaction_id": "T1", "transaction_date": "2026-05-10 10:00:00", "quantity": 1, "unit_price": 10000, "discount_amount": 0, "gross_sales": 10000, "net_sales": 10000},
        {"transaction_id": "T2", "transaction_date": "2026-06-15 11:00:00", "quantity": 2, "unit_price": 10000, "discount_amount": 0, "gross_sales": 20000, "net_sales": 20000},
    ])
    monthly = compute_monthly_sales(df)
    assert len(monthly) == 2
    assert list(monthly["year_month"]) == ["2026-05", "2026-06"]
    assert monthly.iloc[0]["net_sales"] == 10000
    assert monthly.iloc[1]["net_sales"] == 20000
    # MoM growth from 10k to 20k is 100%
    assert monthly.iloc[1]["mom_growth_pct"] == 100.0


def test_sales_empty_dataframe():
    empty_df = pd.DataFrame(columns=["transaction_id", "transaction_date", "quantity", "unit_price", "discount_amount", "gross_sales", "net_sales", "sales_channel", "category"])
    summary = compute_sales_summary(empty_df)
    assert summary.total_net_sales == 0.0
    assert summary.unique_transactions == 0
    assert summary.average_transaction_value == 0.0

    monthly = compute_monthly_sales(empty_df)
    assert monthly.empty

