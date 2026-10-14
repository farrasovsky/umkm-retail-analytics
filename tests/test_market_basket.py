"""Tests for market basket co-occurrence and association rules."""

import pandas as pd
from retail_analytics.analytics.market_basket import compute_market_basket_analysis


def test_market_basket_known_pairs_and_metrics():
    # 4 transactions total:
    # T1: [Bread, Milk]
    # T2: [Bread, Milk]
    # T3: [Bread, Butter]
    # T4: [Diaper, Beer]
    # Total txns = 4
    # Bread count = 3, Milk count = 2
    # Pair (Bread, Milk) count = 2
    # Support(Bread, Milk) = 2/4 = 0.50 (50%)
    # Confidence(Bread -> Milk) = 2 / 3 = 0.6667
    # Confidence(Milk -> Bread) = 2 / 2 = 1.0
    # Lift = 0.50 / ((3/4) * (2/4)) = 0.50 / (0.75 * 0.50) = 0.50 / 0.375 = 1.33
    df = pd.DataFrame([
        {"transaction_id": "T1", "product_name": "Bread"},
        {"transaction_id": "T1", "product_name": "Milk"},
        {"transaction_id": "T2", "product_name": "Bread"},
        {"transaction_id": "T2", "product_name": "Milk"},
        {"transaction_id": "T3", "product_name": "Bread"},
        {"transaction_id": "T3", "product_name": "Butter"},
        {"transaction_id": "T4", "product_name": "Diaper"},
        {"transaction_id": "T4", "product_name": "Beer"},
    ])

    report = compute_market_basket_analysis(df, min_support=0.25, min_confidence=0.50, min_pair_count=2)
    assert report.total_baskets_analyzed == 4
    assert report.multi_item_baskets_count == 4

    top_pairs = report.top_pairs_df
    assert len(top_pairs) >= 1
    bread_milk = top_pairs[(top_pairs["item_a"].isin(["Bread", "Milk"])) & (top_pairs["item_b"].isin(["Bread", "Milk"]))]
    assert not bread_milk.empty
    assert bread_milk.iloc[0]["pair_count"] == 2
    assert bread_milk.iloc[0]["support_pct"] == 50.0
    assert bread_milk.iloc[0]["lift"] == 1.33

    rules = report.rules_df
    # Milk -> Bread should have confidence 1.0 (100%)
    milk_to_bread = rules[(rules["antecedent"] == "Milk") & (rules["consequent"] == "Bread")]
    assert not milk_to_bread.empty
    assert milk_to_bread.iloc[0]["confidence"] == 1.0


def test_market_basket_no_multi_item_baskets():
    df = pd.DataFrame([
        {"transaction_id": "T1", "product_name": "Item A"},
        {"transaction_id": "T2", "product_name": "Item B"},
    ])
    report = compute_market_basket_analysis(df)
    assert report.total_baskets_analyzed == 2
    assert report.multi_item_baskets_count == 0
    assert report.rules_df.empty


def test_market_basket_empty_dataframe():
    empty_df = pd.DataFrame(columns=["transaction_id", "product_name", "sku"])
    report = compute_market_basket_analysis(empty_df)
    assert report.total_baskets_analyzed == 0
    assert report.rules_df.empty

