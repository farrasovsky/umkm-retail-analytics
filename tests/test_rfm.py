"""Tests for customer RFM segmentation and scoring."""

from datetime import datetime
import pandas as pd
from retail_analytics.analytics.rfm import compute_rfm_segmentation


def test_rfm_calculation_and_unregistered_separation():
    df = pd.DataFrame([
        # CUST-01: 2 orders, recent, spend = 100k
        {"transaction_id": "T1", "transaction_date": "2026-05-10 10:00:00", "customer_id": "CUST-01", "net_sales": 60000},
        {"transaction_id": "T2", "transaction_date": "2026-05-15 10:00:00", "customer_id": "CUST-01", "net_sales": 40000},
        # CUST-02: 1 order, old, spend = 20k
        {"transaction_id": "T3", "transaction_date": "2026-04-01 10:00:00", "customer_id": "CUST-02", "net_sales": 20000},
        # Unregistered walk-in order
        {"transaction_id": "T4", "transaction_date": "2026-05-12 10:00:00", "customer_id": None, "net_sales": 30000},
    ])

    ref_date = datetime(2026, 5, 20)
    report = compute_rfm_segmentation(df, reference_date=ref_date)

    assert report.identified_customers_count == 2
    assert report.unregistered_transactions_count == 1
    assert report.unregistered_revenue == 30000.0
    assert report.identified_revenue == 120000.0

    cust_df = report.customer_rfm_df.set_index("customer_id")
    # CUST-01 last date 2026-05-15 -> 5 days recency
    assert cust_df.loc["CUST-01"]["recency_days"] == 5
    assert cust_df.loc["CUST-01"]["frequency"] == 2
    assert cust_df.loc["CUST-01"]["monetary"] == 100000.0

    # CUST-02 last date 2026-04-01 -> 49 days recency
    assert cust_df.loc["CUST-02"]["recency_days"] == 49
    assert cust_df.loc["CUST-02"]["frequency"] == 1
    assert cust_df.loc["CUST-02"]["monetary"] == 20000.0


def test_rfm_all_unregistered():
    df = pd.DataFrame([
        {"transaction_id": "T1", "transaction_date": "2026-05-01 10:00:00", "customer_id": None, "net_sales": 50000},
    ])
    report = compute_rfm_segmentation(df)
    assert report.identified_customers_count == 0
    assert report.unregistered_transactions_count == 1
    assert report.customer_rfm_df.empty


def test_rfm_empty_data():
    empty_df = pd.DataFrame(columns=["transaction_id", "transaction_date", "customer_id", "net_sales"])
    report = compute_rfm_segmentation(empty_df)
    assert report.identified_customers_count == 0
    assert report.total_revenue == 0.0

