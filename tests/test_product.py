"""Tests for product performance analytics and volume vs revenue ranking."""

import pandas as pd
from retail_analytics.analytics.product import compute_product_performance


def test_product_performance_rankings():
    # Product A: 1 unit at 100,000 -> High Revenue, Low Volume
    # Product B: 50 units at 1,000 -> Low Revenue, High Volume
    df = pd.DataFrame([
        {"transaction_id": "T1", "sku": "SKU-A", "product_name": "Premium Rice", "category": "Food", "quantity": 1, "unit_price": 100000, "gross_sales": 100000, "net_sales": 100000},
        {"transaction_id": "T2", "sku": "SKU-B", "product_name": "Candy Stick", "category": "Snacks", "quantity": 50, "unit_price": 1000, "gross_sales": 50000, "net_sales": 50000},
    ])
    perf = compute_product_performance(df, top_n=5)
    assert perf.total_products_count == 2

    # Top by revenue should be SKU-A
    top_rev = perf.top_by_revenue_df
    assert top_rev.iloc[0]["sku"] == "SKU-A"
    assert top_rev.iloc[0]["rank_by_revenue"] == 1
    assert top_rev.iloc[0]["rank_by_quantity"] == 2

    # Top by volume should be SKU-B
    top_vol = perf.top_by_quantity_df
    assert top_vol.iloc[0]["sku"] == "SKU-B"
    assert top_vol.iloc[0]["rank_by_quantity"] == 1
    assert top_vol.iloc[0]["rank_by_revenue"] == 2

    # Cumulative share: SKU-A is 100k / 150k = 66.67%
    assert top_rev.iloc[0]["revenue_share_pct"] == 66.67


def test_product_performance_empty():
    empty_df = pd.DataFrame(columns=["sku", "product_name", "category", "quantity", "gross_sales", "net_sales", "transaction_id"])
    perf = compute_product_performance(empty_df)
    assert perf.total_products_count == 0
    assert perf.top_by_revenue_df.empty

