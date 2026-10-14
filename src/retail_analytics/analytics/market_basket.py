"""Market basket co-occurrence and association rule analytics."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import combinations
import pandas as pd


@dataclass
class MarketBasketReport:
    """Market basket analysis report container."""

    rules_df: pd.DataFrame
    top_pairs_df: pd.DataFrame
    total_baskets_analyzed: int
    multi_item_baskets_count: int
    significant_rules_count: int


def compute_market_basket_analysis(
    df: pd.DataFrame,
    min_support: float = 0.01,
    min_confidence: float = 0.05,
    min_pair_count: int = 2,
    max_rules: int = 50,
) -> MarketBasketReport:
    """Calculate pairwise item co-occurrence, support, confidence, and lift.

    Parameters
    ----------
    df : pd.DataFrame
        Clean transactional records.
    min_support : float, default 0.01
        Minimum fraction of total transactions containing the item pair.
    min_confidence : float, default 0.05
        Minimum conditional probability P(B|A).
    min_pair_count : int, default 2
        Absolute minimum co-occurrence frequency to filter noise.
    max_rules : int, default 50
        Maximum number of association rules to return.

    Returns
    -------
    MarketBasketReport
        Association rules, top co-occurring item pairs, and basket metrics.
    """
    empty_rules = pd.DataFrame(
        columns=[
            "antecedent", "consequent", "pair_count", "support",
            "confidence", "lift",
        ]
    )
    empty_pairs = pd.DataFrame(
        columns=[
            "item_a", "item_b", "pair_count", "support_pct", "lift",
        ]
    )

    if df.empty:
        return MarketBasketReport(
            rules_df=empty_rules,
            top_pairs_df=empty_pairs,
            total_baskets_analyzed=0,
            multi_item_baskets_count=0,
            significant_rules_count=0,
        )

    # Use product_name for business readability; fallback to sku if missing
    working = df.copy()
    if "product_name" in working.columns and "sku" in working.columns:
        item_series = working["product_name"].fillna(working["sku"])
    elif "product_name" in working.columns:
        item_series = working["product_name"]
    elif "sku" in working.columns:
        item_series = working["sku"]
    else:
        item_series = working["transaction_id"]
    working["item_label"] = item_series.astype(str).str.strip()

    # Aggregate unique items per transaction
    baskets = working.groupby("transaction_id")["item_label"].apply(lambda s: sorted(set(s))).to_dict()
    total_txns = len(baskets)

    if total_txns < 2:
        return MarketBasketReport(
            rules_df=empty_rules,
            top_pairs_df=empty_pairs,
            total_baskets_analyzed=total_txns,
            multi_item_baskets_count=0,
            significant_rules_count=0,
        )

    # Count single items and multi-item baskets
    item_counts: Counter[str] = Counter()
    pair_counts: Counter[tuple[str, str]] = Counter()
    multi_item_baskets = 0

    for items in baskets.values():
        if len(items) >= 2:
            multi_item_baskets += 1
            for item in items:
                item_counts[item] += 1
            for a, b in combinations(items, 2):
                pair_counts[(a, b)] += 1
        elif len(items) == 1:
            item_counts[items[0]] += 1

    if not pair_counts:
        return MarketBasketReport(
            rules_df=empty_rules,
            top_pairs_df=empty_pairs,
            total_baskets_analyzed=total_txns,
            multi_item_baskets_count=multi_item_baskets,
            significant_rules_count=0,
        )

    rules_list: list[dict[str, object]] = []
    pairs_list: list[dict[str, object]] = []

    for (a, b), count in pair_counts.items():
        if count < min_pair_count:
            continue

        support_ab = count / total_txns
        if support_ab < min_support:
            continue

        supp_a = item_counts[a] / total_txns
        supp_b = item_counts[b] / total_txns

        # Lift = P(A & B) / (P(A) * P(B))
        denominator = supp_a * supp_b
        lift = round(support_ab / denominator, 2) if denominator > 0 else 0.0

        # Symmetrical pair entry for overview table
        pairs_list.append({
            "item_a": a,
            "item_b": b,
            "pair_count": count,
            "support_pct": round(support_ab * 100, 2),
            "lift": lift,
        })

        # Directed rule: A -> B
        conf_a_to_b = count / item_counts[a] if item_counts[a] > 0 else 0.0
        if conf_a_to_b >= min_confidence:
            rules_list.append({
                "antecedent": a,
                "consequent": b,
                "pair_count": count,
                "support": round(support_ab, 4),
                "confidence": round(conf_a_to_b, 4),
                "lift": lift,
            })

        # Directed rule: B -> A
        conf_b_to_a = count / item_counts[b] if item_counts[b] > 0 else 0.0
        if conf_b_to_a >= min_confidence:
            rules_list.append({
                "antecedent": b,
                "consequent": a,
                "pair_count": count,
                "support": round(support_ab, 4),
                "confidence": round(conf_b_to_a, 4),
                "lift": lift,
            })

    rules_df = pd.DataFrame(rules_list)
    pairs_df = pd.DataFrame(pairs_list)

    if not rules_df.empty:
        rules_df = rules_df.sort_values(by=["lift", "confidence"], ascending=[False, False]).head(max_rules).reset_index(drop=True)
    else:
        rules_df = empty_rules

    if not pairs_df.empty:
        pairs_df = pairs_df.sort_values(by=["pair_count", "lift"], ascending=[False, False]).head(max_rules).reset_index(drop=True)
    else:
        pairs_df = empty_pairs

    return MarketBasketReport(
        rules_df=rules_df,
        top_pairs_df=pairs_df,
        total_baskets_analyzed=total_txns,
        multi_item_baskets_count=multi_item_baskets,
        significant_rules_count=len(rules_df),
    )
