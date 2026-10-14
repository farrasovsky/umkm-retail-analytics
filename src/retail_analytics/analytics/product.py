"""Product ranking, sales velocity, and category contribution analytics."""

from __future__ import annotations

from dataclasses import dataclass
import pandas as pd


@dataclass
class ProductPerformance:
    """Product performance analytics container."""

    product_summary_df: pd.DataFrame
    top_by_revenue_df: pd.DataFrame
    top_by_quantity_df: pd.DataFrame
    bottom_by_revenue_df: pd.DataFrame
    total_products_count: int
    top_5_revenue_share_pct: float


def compute_product_performance(df: pd.DataFrame, top_n: int = 10) -> ProductPerformance:
    """Analyze product level performance, revenue concentration, and volume rankings.

    Parameters
    ----------
    df : pd.DataFrame
        Clean transactional records.
    top_n : int, default 10
        Number of items to extract for top/bottom cohorts.

    Returns
    -------
    ProductPerformance
        Container with complete product metrics and top/bottom rankings.
    """
    empty_df = pd.DataFrame(
        columns=[
            "sku", "product_name", "category", "units_sold", "gross_sales",
            "net_sales", "transaction_count", "average_selling_price",
            "revenue_share_pct", "cumulative_revenue_pct", "rank_by_revenue", "rank_by_quantity",
        ]
    )

    if df.empty:
        return ProductPerformance(
            product_summary_df=empty_df,
            top_by_revenue_df=empty_df,
            top_by_quantity_df=empty_df,
            bottom_by_revenue_df=empty_df,
            total_products_count=0,
            top_5_revenue_share_pct=0.0,
        )

    # Group by SKU, product_name, category
    agg_df = (
        df.groupby(["sku", "product_name", "category"])
        .agg(
            units_sold=("quantity", "sum"),
            gross_sales=("gross_sales", "sum"),
            net_sales=("net_sales", "sum"),
            transaction_count=("transaction_id", "nunique"),
        )
        .reset_index()
    )

    total_net = agg_df["net_sales"].sum()

    # Ranks
    agg_df["rank_by_revenue"] = agg_df["net_sales"].rank(ascending=False, method="min").astype(int)
    agg_df["rank_by_quantity"] = agg_df["units_sold"].rank(ascending=False, method="min").astype(int)

    # Sort by revenue descending
    agg_df = agg_df.sort_values("net_sales", ascending=False).reset_index(drop=True)

    if total_net > 0:
        agg_df["revenue_share_pct"] = (agg_df["net_sales"] / total_net * 100).round(2)
        agg_df["cumulative_revenue_pct"] = agg_df["revenue_share_pct"].cumsum().round(2)
    else:
        agg_df["revenue_share_pct"] = 0.0
        agg_df["cumulative_revenue_pct"] = 0.0

    agg_df["average_selling_price"] = (
        (agg_df["net_sales"] / agg_df["units_sold"]).round(2).where(agg_df["units_sold"] > 0, 0.0)
    )

    top_rev = agg_df.head(top_n).copy()
    top_qty = agg_df.sort_values("units_sold", ascending=False).head(top_n).copy()
    bottom_rev = agg_df.tail(top_n).sort_values("net_sales", ascending=True).copy()

    top_5_share = float(agg_df.head(5)["revenue_share_pct"].sum()) if not agg_df.empty else 0.0

    return ProductPerformance(
        product_summary_df=agg_df,
        top_by_revenue_df=top_rev,
        top_by_quantity_df=top_qty,
        bottom_by_revenue_df=bottom_rev,
        total_products_count=len(agg_df),
        top_5_revenue_share_pct=round(top_5_share, 2),
    )

