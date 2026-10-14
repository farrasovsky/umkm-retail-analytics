"""Standardization and quality cleansing pipeline for retail transaction records."""

from __future__ import annotations

import re
import pandas as pd

from .dates import parse_date_series
from .validation import DataQualityReport


def _clean_sku_string(val: object) -> str:
    """Normalize raw SKU string: strip whitespace, remove internal tabs/newlines, uppercase."""
    if pd.isna(val) or val is None:
        return ""
    s = str(val).strip().upper()
    s = re.sub(r"\s+", " ", s)
    return s


def clean_transactions(
    raw_df: pd.DataFrame,
    product_master_df: pd.DataFrame | None = None,
    dayfirst: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, DataQualityReport]:
    """Clean, standardize, and validate raw retail transactions.

    Parameters
    ----------
    raw_df : pd.DataFrame
        Raw transaction DataFrame loaded by ingestion loader.
    product_master_df : pd.DataFrame | None, optional
        Canonical product catalog for SKU resolution and enrichment.
    dayfirst : bool, default True
        If True, slash and dash dates follow Indonesian/Commonwealth convention (DD/MM/YYYY).

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame, DataQualityReport]
        1. Clean DataFrame ready for analytical computation.
        2. Quarantined DataFrame with rejection reasons.
        3. DataQualityReport containing audit metrics.
    """
    dq = DataQualityReport()
    dq.input_rows = len(raw_df)

    if raw_df.empty:
        dq.warnings.append("Input transactions dataset is empty.")
        empty_clean = pd.DataFrame(
            columns=[
                "transaction_id", "transaction_date", "customer_id", "product_id",
                "sku", "product_name", "category", "quantity", "unit_price",
                "discount_amount", "gross_sales", "net_sales", "sales_channel",
                "payment_method",
            ]
        )
        empty_quarantine = pd.DataFrame(columns=list(raw_df.columns) + ["quarantine_reason"])
        return empty_clean, empty_quarantine, dq

    working_df = raw_df.copy()

    # Ensure optional schema columns exist with sensible defaults
    optional_defaults = {
        "customer_id": None,
        "product_id": None,
        "product_name": "Unknown Product",
        "category": "Uncategorized",
        "discount_amount": 0.0,
        "sales_channel": "Store",
        "payment_method": "Cash",
    }
    for col, default_val in optional_defaults.items():
        if col not in working_df.columns:
            working_df[col] = default_val

    # Step 1: Detect and remove exact duplicate rows across all columns
    initial_count = len(working_df)
    working_df = working_df.drop_duplicates()
    dq.exact_duplicates_count = initial_count - len(working_df)

    quarantined_records: list[dict[str, object]] = []

    # Step 2: Check required columns for null / empty strings
    required_cols = ["transaction_id", "sku", "quantity", "unit_price", "transaction_date"]
    missing_req_mask = pd.Series(False, index=working_df.index)

    for col in required_cols:
        col_str = working_df[col].astype(str).str.strip()
        missing_in_col = working_df[col].isna() | (col_str == "") | (col_str == "nan") | (col_str == "none")
        missing_req_mask = missing_req_mask | missing_in_col

    if missing_req_mask.any():
        bad_rows = working_df[missing_req_mask]
        dq.missing_required_fields_count = len(bad_rows)
        for _, row in bad_rows.iterrows():
            rec = row.to_dict()
            rec["quarantine_reason"] = "Missing mandatory transactional field (ID, SKU, Date, Qty, or Price)"
            quarantined_records.append(rec)
        working_df = working_df[~missing_req_mask].copy()

    # Step 3: Date normalization via deterministic parser
    parsed_dates, date_valid_mask = parse_date_series(working_df["transaction_date"], dayfirst=dayfirst)
    invalid_dates = ~date_valid_mask
    if invalid_dates.any():
        dq.invalid_date_count = int(invalid_dates.sum())
        bad_dates = working_df[invalid_dates]
        for _, row in bad_dates.iterrows():
            rec = row.to_dict()
            rec["quarantine_reason"] = f"Unparseable or out-of-range transaction date: '{row.get('transaction_date')}'"
            quarantined_records.append(rec)
        working_df = working_df[date_valid_mask].copy()
        working_df["transaction_date"] = parsed_dates[date_valid_mask]
    else:
        working_df["transaction_date"] = parsed_dates

    # Step 4: Numeric validation and normalization
    raw_qty = working_df["quantity"]
    qty_num = pd.to_numeric(raw_qty, errors="coerce")
    invalid_qty_mask = qty_num.isna() | (qty_num <= 0)

    raw_price = working_df["unit_price"]
    price_num = pd.to_numeric(raw_price, errors="coerce")
    invalid_price_mask = price_num.isna() | (price_num < 0)

    # Discount amount handling:
    # Blank/null is valid and defaults to 0.0 (documented convention).
    # Non-blank must be numeric and non-negative. Malformed values (e.g. "oops") must NOT be silently accepted as 0.0.
    raw_disc = working_df["discount_amount"]
    is_blank_disc = raw_disc.isna() | raw_disc.astype(str).str.strip().isin(["", "nan", "none", "null"])
    disc_num = pd.to_numeric(raw_disc, errors="coerce")
    invalid_disc_mask = (~is_blank_disc) & (disc_num.isna() | (disc_num < 0))

    invalid_numeric_mask = invalid_qty_mask | invalid_price_mask | invalid_disc_mask

    if invalid_numeric_mask.any():
        # Track metrics for data quality reporting
        dq.invalid_quantity_price_count = int((invalid_qty_mask | invalid_price_mask).sum())
        dq.invalid_discount_count = int(invalid_disc_mask.sum())

        bad_nums = working_df[invalid_numeric_mask]
        for _, row in bad_nums.iterrows():
            rec = row.to_dict()
            reasons = []
            if invalid_qty_mask.loc[row.name]:
                reasons.append(f"invalid quantity: '{row.get('quantity')}'")
            if invalid_price_mask.loc[row.name]:
                reasons.append(f"invalid unit price: '{row.get('unit_price')}'")
            if invalid_disc_mask.loc[row.name]:
                reasons.append(f"invalid discount: '{row.get('discount_amount')}'")
            rec["quarantine_reason"] = f"Invalid numerical values ({', '.join(reasons)})"
            quarantined_records.append(rec)

        working_df = working_df[~invalid_numeric_mask].copy()
        working_df["quantity"] = qty_num[~invalid_numeric_mask]
        working_df["unit_price"] = price_num[~invalid_numeric_mask]
        # Valid discount: filled with 0.0 if blank
        working_df["discount_amount"] = disc_num[~invalid_numeric_mask].where(~is_blank_disc[~invalid_numeric_mask], 0.0)
    else:
        working_df["quantity"] = qty_num
        working_df["unit_price"] = price_num
        working_df["discount_amount"] = disc_num.where(~is_blank_disc, 0.0)

    # Step 5: SKU Cleaning & Product Master Mapping
    raw_skus = working_df["sku"].astype(str)
    cleaned_skus = raw_skus.apply(_clean_sku_string)
    diff_mask = raw_skus != cleaned_skus
    dq.corrected_sku_formatting_count = int(diff_mask.sum())
    working_df["sku"] = cleaned_skus

    # Build master mapping dictionaries if product master is provided
    sku_to_canonical: dict[str, str] = {}
    master_info: dict[str, dict[str, str]] = {}

    if product_master_df is not None and not product_master_df.empty:
        for _, m_row in product_master_df.iterrows():
            c_sku = _clean_sku_string(m_row.get("sku", ""))
            if not c_sku:
                continue
            sku_to_canonical[c_sku] = c_sku
            master_info[c_sku] = {
                "product_id": str(m_row.get("product_id", "")).strip(),
                "product_name": str(m_row.get("product_name", "")).strip(),
                "category": str(m_row.get("category", "")).strip(),
            }
            # Check aliases
            aliases = str(m_row.get("sku_aliases", "")).strip()
            if aliases and aliases != "nan":
                for alias in aliases.split(";"):
                    clean_alias = _clean_sku_string(alias)
                    if clean_alias:
                        sku_to_canonical[clean_alias] = c_sku

        # Map SKUs
        canonical_mapped = working_df["sku"].map(sku_to_canonical)
        unknown_skus = canonical_mapped.isna()
        if unknown_skus.any():
            dq.unknown_sku_count = int(unknown_skus.sum())
            dq.warnings.append(
                f"{dq.unknown_sku_count} records contain SKUs not found in Product Master catalog. Preserving raw SKU."
            )
        # Apply canonical mapping where known
        working_df["sku"] = canonical_mapped.fillna(working_df["sku"])

        # Enrich missing or blank product_name / category / product_id from master
        for c_sku, info in master_info.items():
            mask = working_df["sku"] == c_sku
            if mask.any():
                if info["product_id"]:
                    working_df.loc[mask, "product_id"] = working_df.loc[mask, "product_id"].fillna(info["product_id"])
                if info["product_name"]:
                    name_null = working_df.loc[mask, "product_name"].isna() | (working_df.loc[mask, "product_name"] == "") | (working_df.loc[mask, "product_name"] == "Unknown Product")
                    working_df.loc[mask & name_null, "product_name"] = info["product_name"]
                if info["category"]:
                    cat_null = working_df.loc[mask, "category"].isna() | (working_df.loc[mask, "category"] == "") | (working_df.loc[mask, "category"] == "Uncategorized")
                    working_df.loc[mask & cat_null, "category"] = info["category"]

    # Step 6: Text fields hygiene (transaction_id, customer_id, channel, category)
    working_df["transaction_id"] = working_df["transaction_id"].astype(str).str.strip().str.upper()

    # Clean customer ID: if blank or 'nan', set to None
    clean_cust = working_df["customer_id"].astype(str).str.strip().str.upper()
    working_df["customer_id"] = clean_cust.mask(clean_cust.isin(["", "NAN", "NONE", "NULL"]), None)

    # Standardize category text
    working_df["category"] = working_df["category"].fillna("Uncategorized").astype(str).str.strip().str.title()
    working_df["product_name"] = working_df["product_name"].fillna("Unknown Product").astype(str).str.strip()
    working_df["sales_channel"] = working_df["sales_channel"].fillna("Store").astype(str).str.strip().str.title()
    working_df["payment_method"] = working_df["payment_method"].fillna("Cash").astype(str).str.strip().str.title()

    # Step 7: Revenue calculations
    # gross_sales = quantity * unit_price
    # net_sales = gross_sales - discount_amount (cannot be negative; cap discount if necessary with warning)
    working_df["gross_sales"] = (working_df["quantity"] * working_df["unit_price"]).round(2)

    over_discount_mask = working_df["discount_amount"] > working_df["gross_sales"]
    if over_discount_mask.any():
        dq.warnings.append(
            f"{over_discount_mask.sum()} records had discounts exceeding gross sales; discount capped at gross sales."
        )
        working_df.loc[over_discount_mask, "discount_amount"] = working_df.loc[over_discount_mask, "gross_sales"]

    working_df["net_sales"] = (working_df["gross_sales"] - working_df["discount_amount"]).round(2)

    # Format dates as ISO string for clean output DataFrame
    working_df["transaction_date"] = pd.to_datetime(working_df["transaction_date"]).dt.strftime("%Y-%m-%d %H:%M:%S")

    # Final counts and row-count reconciliation
    dq.quarantined_rows_count = len(quarantined_records)
    dq.output_rows = len(working_df)
    dq.clean_unique_transactions = working_df["transaction_id"].nunique()

    # Assemble quarantine DataFrame
    quarantine_df = pd.DataFrame(quarantined_records) if quarantined_records else pd.DataFrame(
        columns=list(raw_df.columns) + ["quarantine_reason"]
    )

    # Standardize output column ordering
    canonical_columns = [
        "transaction_id",
        "transaction_date",
        "customer_id",
        "product_id",
        "sku",
        "product_name",
        "category",
        "quantity",
        "unit_price",
        "discount_amount",
        "gross_sales",
        "net_sales",
        "sales_channel",
        "payment_method",
    ]
    clean_cols = [c for c in canonical_columns if c in working_df.columns] + [
        c for c in working_df.columns if c not in canonical_columns
    ]
    clean_df = working_df[clean_cols].reset_index(drop=True)

    return clean_df, quarantine_df, dq
