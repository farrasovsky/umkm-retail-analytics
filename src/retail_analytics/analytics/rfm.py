"""Recency, Frequency, Monetary (RFM) customer behavioral segmentation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import numpy as np
import pandas as pd


@dataclass
class RFMReport:
    """Customer RFM analytics and cohort distribution report."""

    customer_rfm_df: pd.DataFrame
    segment_summary_df: pd.DataFrame
    identified_customers_count: int
    identified_revenue: float
    unregistered_transactions_count: int
    unregistered_revenue: float
    total_revenue: float


def _assign_rfm_scores(series: pd.Series, ascending: bool = True) -> pd.Series:
    """Score a series into 1-5 integer bins using percentiles.

    Parameters
    ----------
    series : pd.Series
        Numerical metric series.
    ascending : bool, default True
        If True, higher raw values get higher scores (1 to 5).
        If False (e.g. recency days), lower raw values get higher scores.
    """
    if len(series) == 0:
        return pd.Series(dtype=int)

    # Use percentile ranks for deterministic scoring even with tied values
    ranks = series.rank(pct=True, method="average", ascending=ascending)
    scores = pd.cut(
        ranks,
        bins=[-np.inf, 0.2, 0.4, 0.6, 0.8, np.inf],
        labels=[1, 2, 3, 4, 5],
    ).astype(int)
    return scores


def _classify_rfm_segment(r: int, f: int, m: int) -> str:
    """Rule-based segmentation map based on R, F, M quintile scores."""
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    if f >= 3 and m >= 3 and r >= 3:
        return "Loyal Customers"
    if r >= 4 and f in (1, 2):
        return "Potential Loyalists"
    if r <= 2 and (f >= 3 or m >= 3):
        return "At Risk"
    if r <= 2 and f <= 2:
        return "Lost / Inactive"
    if r in (2, 3) and f in (2, 3):
        return "Needs Attention"
    return "Needs Attention"


def compute_rfm_segmentation(
    df: pd.DataFrame,
    reference_date: datetime | str | None = None,
) -> RFMReport:
    """Perform RFM segmentation on identified customer transactions.

    Parameters
    ----------
    df : pd.DataFrame
        Clean transactional records.
    reference_date : datetime | str | None, optional
        Target point-in-time date for recency calculation.
        Defaults to max transaction date in dataset if None.

    Returns
    -------
    RFMReport
        Customer scores, assigned segments, and cohort aggregate summary.
    """
    empty_cust = pd.DataFrame(
        columns=[
            "customer_id", "recency_days", "frequency", "monetary",
            "r_score", "f_score", "m_score", "rfm_score", "segment",
        ]
    )
    empty_summary = pd.DataFrame(
        columns=[
            "segment", "customer_count", "total_revenue", "avg_monetary",
            "avg_frequency", "avg_recency_days", "revenue_share_pct",
        ]
    )

    if df.empty:
        return RFMReport(
            customer_rfm_df=empty_cust,
            segment_summary_df=empty_summary,
            identified_customers_count=0,
            identified_revenue=0.0,
            unregistered_transactions_count=0,
            unregistered_revenue=0.0,
            total_revenue=0.0,
        )

    working = df.copy()
    working["dt"] = pd.to_datetime(working["transaction_date"])

    total_rev = float(working["net_sales"].sum())

    # Separate identified from anonymous/unregistered
    identified_mask = working["customer_id"].notna() & (working["customer_id"].astype(str).str.strip() != "")
    unregistered_df = working[~identified_mask]
    identified_df = working[identified_mask]

    unreg_txns = int(unregistered_df["transaction_id"].nunique())
    unreg_rev = float(unregistered_df["net_sales"].sum())
    ident_rev = float(identified_df["net_sales"].sum())

    if identified_df.empty:
        return RFMReport(
            customer_rfm_df=empty_cust,
            segment_summary_df=empty_summary,
            identified_customers_count=0,
            identified_revenue=0.0,
            unregistered_transactions_count=unreg_txns,
            unregistered_revenue=round(unreg_rev, 2),
            total_revenue=round(total_rev, 2),
        )

    # Reference point for Recency
    if reference_date is None:
        ref_dt = working["dt"].max()
    elif isinstance(reference_date, str):
        ref_dt = pd.to_datetime(reference_date)
    else:
        ref_dt = reference_date

    # Customer level aggregation
    rfm_table = (
        identified_df.groupby("customer_id")
        .agg(
            last_date=("dt", "max"),
            frequency=("transaction_id", "nunique"),
            monetary=("net_sales", "sum"),
        )
        .reset_index()
    )

    ref_day = pd.to_datetime(ref_dt).floor("D")
    last_day = rfm_table["last_date"].dt.floor("D")
    rfm_table["recency_days"] = (ref_day - last_day).dt.days.clip(lower=0)

    # Calculate 1-5 scores
    # Recency: lower days = higher score
    rfm_table["r_score"] = _assign_rfm_scores(rfm_table["recency_days"], ascending=False)
    # Frequency: higher count = higher score
    rfm_table["f_score"] = _assign_rfm_scores(rfm_table["frequency"], ascending=True)
    # Monetary: higher value = higher score
    rfm_table["m_score"] = _assign_rfm_scores(rfm_table["monetary"], ascending=True)

    rfm_table["rfm_score"] = (
        rfm_table["r_score"].astype(str)
        + rfm_table["f_score"].astype(str)
        + rfm_table["m_score"].astype(str)
    )

    # Assign segment labels
    rfm_table["segment"] = [
        _classify_rfm_segment(r, f, m)
        for r, f, m in zip(rfm_table["r_score"], rfm_table["f_score"], rfm_table["m_score"])
    ]

    rfm_table["monetary"] = rfm_table["monetary"].round(2)
    rfm_table = rfm_table.sort_values("monetary", ascending=False).reset_index(drop=True)

    # Build cohort summary table
    segment_summary = (
        rfm_table.groupby("segment")
        .agg(
            customer_count=("customer_id", "count"),
            total_revenue=("monetary", "sum"),
            avg_monetary=("monetary", "mean"),
            avg_frequency=("frequency", "mean"),
            avg_recency_days=("recency_days", "mean"),
        )
        .reset_index()
    )

    segment_summary["total_revenue"] = segment_summary["total_revenue"].round(2)
    segment_summary["avg_monetary"] = segment_summary["avg_monetary"].round(2)
    segment_summary["avg_frequency"] = segment_summary["avg_frequency"].round(1)
    segment_summary["avg_recency_days"] = segment_summary["avg_recency_days"].round(1)

    if ident_rev > 0:
        segment_summary["revenue_share_pct"] = (
            (segment_summary["total_revenue"] / ident_rev) * 100
        ).round(2)
    else:
        segment_summary["revenue_share_pct"] = 0.0

    # Ensure all segments exist in summary table even if 0 count
    all_segments = [
        "Champions",
        "Loyal Customers",
        "Potential Loyalists",
        "At Risk",
        "Needs Attention",
        "Lost / Inactive",
    ]
    present_segs = set(segment_summary["segment"])
    missing_rows = []
    for s in all_segments:
        if s not in present_segs:
            missing_rows.append({
                "segment": s,
                "customer_count": 0,
                "total_revenue": 0.0,
                "avg_monetary": 0.0,
                "avg_frequency": 0.0,
                "avg_recency_days": 0.0,
                "revenue_share_pct": 0.0,
            })
    if missing_rows:
        segment_summary = pd.concat([segment_summary, pd.DataFrame(missing_rows)], ignore_index=True)

    # Order by customer count descending
    segment_summary = segment_summary.sort_values("total_revenue", ascending=False).reset_index(drop=True)

    cols_order = [
        "customer_id", "recency_days", "frequency", "monetary",
        "r_score", "f_score", "m_score", "rfm_score", "segment",
    ]
    rfm_table = rfm_table[cols_order]

    return RFMReport(
        customer_rfm_df=rfm_table,
        segment_summary_df=segment_summary,
        identified_customers_count=len(rfm_table),
        identified_revenue=round(ident_rev, 2),
        unregistered_transactions_count=unreg_txns,
        unregistered_revenue=round(unreg_rev, 2),
        total_revenue=round(total_rev, 2),
    )
