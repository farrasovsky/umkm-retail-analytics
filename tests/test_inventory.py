"""Tests for inventory velocity, days of stock remaining, and reorder alerts."""

import pandas as pd
from retail_analytics.analytics.inventory import compute_inventory_health


def test_inventory_health_calculations():
    # 30-day period
    # SKU-1: sold 60 units -> daily rate = 2.0. Stock = 10, Reorder = 20 -> Stock <= Reorder -> REORDER_NOW. Days = 10 / 2 = 5.0
    # SKU-2: sold 30 units -> daily rate = 1.0. Stock = 25, Reorder = 20 -> Stock <= 20 * 1.5 (30) -> LOW_STOCK_WARNING. Days = 25.0
    # SKU-3: sold 0 units -> daily rate = 0.0. Stock = 100, Reorder = 10 -> No movement.
    txns = pd.DataFrame([
        {"sku": "SKU-1", "quantity": 60, "transaction_date": "2026-05-01"},
        {"sku": "SKU-2", "quantity": 30, "transaction_date": "2026-05-01"},
    ])
    inv = pd.DataFrame([
        {"sku": "SKU-1", "product_name": "Item 1", "category": "Food", "stock_on_hand": 10, "reorder_point": 20},
        {"sku": "SKU-2", "product_name": "Item 2", "category": "Food", "stock_on_hand": 25, "reorder_point": 20},
        {"sku": "SKU-3", "product_name": "Item 3", "category": "Food", "stock_on_hand": 100, "reorder_point": 10},
    ])

    report = compute_inventory_health(txns, inv, days_in_period=30, reorder_warning_multiplier=1.5)
    assert report.total_inventory_items == 3
    assert report.reorder_alerts_count == 1
    assert report.warning_alerts_count == 1

    df = report.inventory_df.set_index("sku")
    assert df.loc["SKU-1"]["daily_sales_rate"] == 2.0
    assert df.loc["SKU-1"]["estimated_days_of_stock"] == 5.0
    assert df.loc["SKU-1"]["stock_status"] == "REORDER_NOW"

    assert df.loc["SKU-2"]["daily_sales_rate"] == 1.0
    assert df.loc["SKU-2"]["estimated_days_of_stock"] == 25.0
    assert df.loc["SKU-2"]["stock_status"] == "LOW_STOCK_WARNING"

    assert df.loc["SKU-3"]["daily_sales_rate"] == 0.0
    assert df.loc["SKU-3"]["movement_velocity"] == "No Movement"


def test_inventory_empty_data():
    empty_txns = pd.DataFrame(columns=["sku", "quantity", "transaction_date"])
    empty_inv = pd.DataFrame(columns=["sku", "stock_on_hand", "reorder_point"])
    report = compute_inventory_health(empty_txns, empty_inv)
    assert report.total_inventory_items == 0
    assert report.reorder_alerts_count == 0

