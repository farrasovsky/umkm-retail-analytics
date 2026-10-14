"""Inventory velocity, stock-on-hand health, and replenishment alert analytics."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass
class InventoryReport:
    """Inventory health analytics report container."""

    inventory_df: pd.DataFrame
    reorder_alerts_count: int
    warning_alerts_count: int
    fast_moving_count: int
    slow_moving_count: int
    overstocked_count: int
    total_inventory_items: int


def compute_inventory_health(
    transactions_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
    days_in_period: int | None = None,
    reorder_warning_multiplier: float = 1.5,
) -> InventoryReport:
    """Analyze stock movement, daily sales run-rate, and reorder urgency.

    Parameters
    ----------
    transactions_df : pd.DataFrame
        Clean transactional records.
    inventory_df : pd.DataFrame
        Current stock snapshot with stock_on_hand and reorder_point.
    days_in_period : int | None, optional
        Duration of the historical period in days. If None, derived from transactions.
    reorder_warning_multiplier : float, default 1.5
        Stock level threshold relative to reorder point to trigger a warning.

    Returns
    -------
    InventoryReport
        Detailed stock health table and summary counts.
    """
    empty_df = pd.DataFrame(
        columns=[
            "sku", "product_name", "category", "stock_on_hand", "reorder_point",
            "units_sold_period", "daily_sales_rate", "estimated_days_of_stock",
            "stock_status", "movement_velocity",
        ]
    )

    if inventory_df.empty:
        return InventoryReport(
            inventory_df=empty_df,
            reorder_alerts_count=0,
            warning_alerts_count=0,
            fast_moving_count=0,
            slow_moving_count=0,
            overstocked_count=0,
            total_inventory_items=0,
        )

    # Determine period days
    if days_in_period is None or days_in_period <= 0:
        if not transactions_df.empty:
            dates = pd.to_datetime(transactions_df["transaction_date"])
            days = (dates.max() - dates.min()).days + 1
            period_days = max(days, 1)
        else:
            period_days = 30
    else:
        period_days = days_in_period

    # Aggregate sales units by SKU
    if not transactions_df.empty:
        sales_by_sku = (
            transactions_df.groupby("sku")["quantity"]
            .sum()
            .reset_index()
            .rename(columns={"quantity": "units_sold_period"})
        )
    else:
        sales_by_sku = pd.DataFrame(columns=["sku", "units_sold_period"])

    inv = inventory_df.copy()
    inv["sku"] = inv["sku"].astype(str).str.strip().str.upper()
    inv["stock_on_hand"] = pd.to_numeric(inv["stock_on_hand"], errors="coerce").fillna(0).astype(int)
    inv["reorder_point"] = pd.to_numeric(inv["reorder_point"], errors="coerce").fillna(0).astype(int)

    # Merge sales into inventory snapshot
    merged = pd.merge(inv, sales_by_sku, on="sku", how="left")
    merged["units_sold_period"] = merged["units_sold_period"].fillna(0).astype(int)

    # Calculate run rate and days of stock
    merged["daily_sales_rate"] = (merged["units_sold_period"] / period_days).round(2)

    # Safe days of stock calculation
    def _calc_days(row: pd.Series) -> float | None:
        rate = row["daily_sales_rate"]
        stock = row["stock_on_hand"]
        if rate <= 0:
            return 999.0 if stock > 0 else 0.0
        return round(stock / rate, 1)

    merged["estimated_days_of_stock"] = merged.apply(_calc_days, axis=1)

    # Determine Stock Status
    # 1. REORDER NOW: stock <= reorder_point
    # 2. LOW STOCK WARNING: stock <= reorder_point * multiplier
    # 3. OVERSTOCKED: days_of_stock >= 90 and units_sold > 0
    # 4. OUT OF STOCK: stock <= 0
    # 5. ADEQUATE: normal range
    def _classify_status(row: pd.Series) -> str:
        stock = row["stock_on_hand"]
        reorder = row["reorder_point"]
        days = row["estimated_days_of_stock"]

        if stock <= 0:
            return "OUT_OF_STOCK"
        if stock <= reorder:
            return "REORDER_NOW"
        if stock <= (reorder * reorder_warning_multiplier):
            return "LOW_STOCK_WARNING"
        if days is not None and days >= 90 and row["units_sold_period"] > 0:
            return "OVERSTOCKED"
        return "ADEQUATE"

    merged["stock_status"] = merged.apply(_classify_status, axis=1)

    # Movement velocity classification
    # Based on daily sales velocity percentiles or thresholds
    positive_rates = merged[merged["daily_sales_rate"] > 0]["daily_sales_rate"]
    p75 = float(positive_rates.quantile(0.75)) if len(positive_rates) > 2 else 2.0
    p25 = float(positive_rates.quantile(0.25)) if len(positive_rates) > 2 else 0.5

    def _classify_movement(row: pd.Series) -> str:
        rate = row["daily_sales_rate"]
        if rate == 0:
            return "No Movement"
        if rate >= p75:
            return "Fast-Moving"
        if rate <= p25:
            return "Slow-Moving"
        return "Steady-Moving"

    merged["movement_velocity"] = merged.apply(_classify_movement, axis=1)

    # Ensure required fields in presentation table
    for field in ["product_name", "category"]:
        if field not in merged.columns:
            merged[field] = "N/A"

    cols_order = [
        "sku",
        "product_name",
        "category",
        "stock_on_hand",
        "reorder_point",
        "units_sold_period",
        "daily_sales_rate",
        "estimated_days_of_stock",
        "stock_status",
        "movement_velocity",
    ]
    merged = merged[cols_order].sort_values(
        by=["stock_status", "estimated_days_of_stock"],
        ascending=[True, True]
    ).reset_index(drop=True)

    reorder_cnt = int((merged["stock_status"].isin(["REORDER_NOW", "OUT_OF_STOCK"])).sum())
    warning_cnt = int((merged["stock_status"] == "LOW_STOCK_WARNING").sum())
    fast_cnt = int((merged["movement_velocity"] == "Fast-Moving").sum())
    slow_cnt = int((merged["movement_velocity"].isin(["Slow-Moving", "No Movement"])).sum())
    over_cnt = int((merged["stock_status"] == "OVERSTOCKED").sum())

    return InventoryReport(
        inventory_df=merged,
        reorder_alerts_count=reorder_cnt,
        warning_alerts_count=warning_cnt,
        fast_moving_count=fast_cnt,
        slow_moving_count=slow_cnt,
        overstocked_count=over_cnt,
        total_inventory_items=len(merged),
    )

