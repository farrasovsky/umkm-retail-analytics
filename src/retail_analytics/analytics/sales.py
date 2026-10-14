"""Sales overview and revenue trend analytics."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import pandas as pd


@dataclass
class SalesSummary:
    """Core high-level sales KPIs for the analyzed period."""

    total_gross_sales: float = 0.0
    total_discount: float = 0.0
    total_net_sales: float = 0.0
    unique_transactions: int = 0
    total_units_sold: int = 0
    average_transaction_value: float = 0.0
    average_items_per_transaction: float = 0.0
    period_start: str = ""
    period_end: str = ""
    total_days: int = 0

    def to_dict(self) -> dict[str, object]:
        """Convert sales summary to dictionary."""
        return asdict(self)


def compute_sales_summary(df: pd.DataFrame) -> SalesSummary:
    """Calculate overall retail sales KPIs from clean transactions.

    Parameters
    ----------
    df : pd.DataFrame
        Clean transactional records.

    Returns
    -------
    SalesSummary
        Aggregated KPI metrics.
    """
    if df.empty:
        return SalesSummary()

    gross = float(df["gross_sales"].sum())
    disc = float(df["discount_amount"].sum())
    net = float(df["net_sales"].sum())
    txns = int(df["transaction_id"].nunique())
    units = int(df["quantity"].sum())

    atv = round(net / txns, 2) if txns > 0 else 0.0
    items_per_txn = round(units / txns, 2) if txns > 0 else 0.0

    # Date range
    date_dt = pd.to_datetime(df["transaction_date"])
    min_date = date_dt.min()
    max_date = date_dt.max()
    days = (max_date - min_date).days + 1 if pd.notna(min_date) and pd.notna(max_date) else 0

    return SalesSummary(
        total_gross_sales=round(gross, 2),
        total_discount=round(disc, 2),
        total_net_sales=round(net, 2),
        unique_transactions=txns,
        total_units_sold=units,
        average_transaction_value=atv,
        average_items_per_transaction=items_per_txn,
        period_start=min_date.strftime("%Y-%m-%d") if pd.notna(min_date) else "",
        period_end=max_date.strftime("%Y-%m-%d") if pd.notna(max_date) else "",
        total_days=max(days, 1),
    )


def compute_monthly_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate revenue, transactions, and ATV month-by-month.

    Parameters
    ----------
    df : pd.DataFrame
        Clean transactional records.

    Returns
    -------
    pd.DataFrame
        Monthly breakdown sorted chronologically with MoM net sales growth.
    """
    if df.empty:
        return pd.DataFrame(
            columns=[
                "year_month",
                "gross_sales",
                "discount_amount",
                "net_sales",
                "transaction_count",
                "units_sold",
                "atv",
                "mom_growth_pct",
            ]
        )

    working = df.copy()
    working["year_month"] = pd.to_datetime(working["transaction_date"]).dt.strftime("%Y-%m")

    grouped = (
        working.groupby("year_month")
        .agg(
            gross_sales=("gross_sales", "sum"),
            discount_amount=("discount_amount", "sum"),
            net_sales=("net_sales", "sum"),
            transaction_count=("transaction_id", "nunique"),
            units_sold=("quantity", "sum"),
        )
        .reset_index()
        .sort_values("year_month")
    )

    grouped["atv"] = (grouped["net_sales"] / grouped["transaction_count"]).round(2)

    # MoM percentage growth of net_sales
    grouped["mom_growth_pct"] = (
        grouped["net_sales"].pct_change().mul(100).round(2).fillna(0.0)
    )

    return grouped


def compute_channel_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Analyze sales distribution across retail channels.

    Parameters
    ----------
    df : pd.DataFrame
        Clean transactional records.

    Returns
    -------
    pd.DataFrame
        Channel summary with net sales, order counts, and share percentage.
    """
    if df.empty:
        return pd.DataFrame(
            columns=["sales_channel", "net_sales", "transaction_count", "units_sold", "share_of_sales_pct"]
        )

    grouped = (
        df.groupby("sales_channel")
        .agg(
            net_sales=("net_sales", "sum"),
            transaction_count=("transaction_id", "nunique"),
            units_sold=("quantity", "sum"),
        )
        .reset_index()
        .sort_values("net_sales", ascending=False)
    )

    total_net = grouped["net_sales"].sum()
    if total_net > 0:
        grouped["share_of_sales_pct"] = (grouped["net_sales"] / total_net * 100).round(2)
    else:
        grouped["share_of_sales_pct"] = 0.0

    return grouped


def compute_category_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Analyze sales contribution by product category.

    Parameters
    ----------
    df : pd.DataFrame
        Clean transactional records.

    Returns
    -------
    pd.DataFrame
        Category performance sorted by net revenue.
    """
    if df.empty:
        return pd.DataFrame(
            columns=["category", "net_sales", "units_sold", "transaction_count", "share_of_sales_pct"]
        )

    grouped = (
        df.groupby("category")
        .agg(
            net_sales=("net_sales", "sum"),
            units_sold=("quantity", "sum"),
            transaction_count=("transaction_id", "nunique"),
        )
        .reset_index()
        .sort_values("net_sales", ascending=False)
    )

    total_net = grouped["net_sales"].sum()
    if total_net > 0:
        grouped["share_of_sales_pct"] = (grouped["net_sales"] / total_net * 100).round(2)
    else:
        grouped["share_of_sales_pct"] = 0.0

    return grouped

