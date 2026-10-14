"""Portfolio showcase runner and demonstration summary generator.

This module executes a controlled, representative demonstration of retail data engineering
and analytics on the designated synthetic dataset. It demonstrates data hygiene, strict schema
validation, deterministic date parsing, financial integrity, and business metric calculations
without distributing a general-purpose, self-service automated report delivery engine.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from typing import Any

from retail_analytics.analytics.product import compute_product_performance
from retail_analytics.analytics.rfm import compute_rfm_segmentation
from retail_analytics.analytics.sales import compute_monthly_sales, compute_sales_summary
from retail_analytics.cleaning.cleaning import clean_transactions
from retail_analytics.ingestion.loaders import load_product_master_csv, load_transactions_csv
from retail_analytics.ingestion.schemas import SchemaValidationError
from retail_analytics.showcase.fixture_manifest import (
    EXPECTED_FIXTURE_SHA256,
    FIXTURE_DIR_PARTS,
    OUTPUT_DIR_PARTS,
)

TRANSACTIONS_FIXTURE = "raw_transactions.csv"
PRODUCT_MASTER_FIXTURE = "product_master.csv"


class ShowcasePathError(ValueError):
    """Raised when a fixture or output path fails symbolic-link or containment validation."""


class ShowcaseIntegrityError(ValueError):
    """Raised when a designated fixture does not match its source-controlled SHA-256 digest."""


def get_project_root() -> Path:
    """Locate the repository root from this module's location (never from the caller's cwd).

    Walks up from this file until a directory containing ``pyproject.toml`` and the
    designated transaction fixture is found. Raises if no such directory exists.
    """
    file_path = Path(__file__).resolve()
    for candidate in file_path.parents:
        if (candidate / "pyproject.toml").is_file() and candidate.joinpath(
            *FIXTURE_DIR_PARTS, TRANSACTIONS_FIXTURE
        ).exists():
            return candidate
    raise FileNotFoundError(
        "Could not locate the project root containing the designated synthetic fixture "
        f"({'/'.join(FIXTURE_DIR_PARTS)}/{TRANSACTIONS_FIXTURE}) above {file_path}."
    )


def _reject_symlinks_below(root: Path, target: Path) -> None:
    """Reject symbolic links at every path component from ``root`` (exclusive) to ``target``."""
    current = root
    for part in target.relative_to(root).parts:
        current = current / part
        if current.is_symlink():
            raise ShowcasePathError(f"Symbolic link rejected in protected path: {current}")


def _sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validated_fixture(root: Path, filename: str) -> Path:
    """Return the path of a designated fixture after symlink, containment, type and digest checks."""
    fixture_dir = root.joinpath(*FIXTURE_DIR_PARTS)
    candidate = fixture_dir / filename

    _reject_symlinks_below(root, candidate)

    if not candidate.exists():
        label = "transaction" if filename == TRANSACTIONS_FIXTURE else "product master"
        raise FileNotFoundError(
            f"Designated synthetic {label} fixture not found at: {candidate}.\n"
            "The showcase runs strictly against bundled synthetic fixtures and never generates "
            "replacement data. Restore the committed file from version control."
        )

    if not stat.S_ISREG(os.lstat(candidate).st_mode):
        raise ShowcasePathError(f"Designated fixture is not a regular file: {candidate}")

    resolved = candidate.resolve(strict=True)
    if resolved.parent != fixture_dir.resolve(strict=True) or resolved.name != filename:
        raise ShowcasePathError(f"Designated fixture escapes the fixture directory: {resolved}")

    expected = EXPECTED_FIXTURE_SHA256[filename]
    actual = _sha256_of(resolved)
    if actual != expected:
        raise ShowcaseIntegrityError(
            f"Fixture integrity check failed for {filename}: expected SHA-256 {expected}, got {actual}. "
            "The bundled synthetic fixture has been modified or substituted."
        )
    return resolved


def _prepare_output_dir(root: Path) -> Path:
    """Create (if needed) and return the fixed showcase output directory after validation."""
    expected = root.joinpath(*OUTPUT_DIR_PARTS)
    current = root
    for part in OUTPUT_DIR_PARTS:
        current = current / part
        if current.is_symlink():
            raise ShowcasePathError(f"Symbolic link rejected in output path: {current}")
        if current.exists() and not current.is_dir():
            raise ShowcasePathError(f"Output path component is not a directory: {current}")
        current.mkdir(exist_ok=True)
        # Re-check after creation in case the component was swapped concurrently.
        if current.is_symlink():
            raise ShowcasePathError(f"Symbolic link rejected in output path: {current}")

    if expected.resolve(strict=True) != expected:
        raise ShowcasePathError(f"Output directory resolves outside the approved location: {expected}")
    return expected


def _open_output_file(out_dir: Path, filename: str):
    """Open a file inside the validated output directory without following a symlinked target."""
    target = out_dir / filename
    if target.is_symlink():
        raise ShowcasePathError(f"Symbolic link rejected for output file: {target}")
    if target.resolve().parent != out_dir:
        raise ShowcasePathError(f"Output file escapes the approved directory: {target}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(target, flags, 0o644)
    return os.fdopen(fd, "w", encoding="utf-8", newline="")


def run_showcase_demo() -> dict[str, Any]:
    """Execute the controlled portfolio showcase on the designated bundled synthetic fixture.

    This function is parameterless. The input fixtures (``data/sample/raw_transactions.csv`` and
    ``data/sample/product_master.csv``) and the output directory (``output/showcase/``) are fixed
    relative to the project root located from this module, not from the caller's working directory.

    Before reading, each fixture is checked for symbolic links along its path, resolved
    containment, regular-file type, and a source-controlled SHA-256 digest. Before writing,
    the output directory and files are checked for symbolic links and containment.

    Limitations: these checks are reasonable best-effort protections. They are not immune to
    every filesystem race (a path could change between validation and use).

    Raises
    ------
    FileNotFoundError
        If a designated fixture is missing.
    ShowcasePathError
        If a fixture or output path involves a symbolic link or escapes its approved directory.
    ShowcaseIntegrityError
        If a fixture does not match its expected SHA-256 digest.
    """
    repo_root = get_project_root().resolve()

    # 1. Validate both designated fixtures before reading anything.
    txn_file = _validated_fixture(repo_root, TRANSACTIONS_FIXTURE)
    pm_file = _validated_fixture(repo_root, PRODUCT_MASTER_FIXTURE)

    # 2. Load and clean the validated synthetic fixtures.
    raw_df = load_transactions_csv(txn_file)
    pm_df = load_product_master_csv(pm_file)
    clean_df, quarantined_df, dq_report = clean_transactions(
        raw_df=raw_df,
        product_master_df=pm_df,
        dayfirst=True,
    )

    # Invariant assertion: input_rows == output_rows + quarantined_rows + exact_duplicates
    expected_sum = dq_report.output_rows + dq_report.quarantined_rows_count + dq_report.exact_duplicates_count
    if dq_report.input_rows != expected_sum:
        raise AssertionError(
            f"Data reconciliation invariant violated: {dq_report.input_rows} != {expected_sum}"
        )

    # Step 4: Calculate selected business analytics
    sales_kpis = compute_sales_summary(clean_df)
    monthly_sales = compute_monthly_sales(clean_df)
    product_perf = compute_product_performance(clean_df)
    rfm_report = compute_rfm_segmentation(clean_df)

    # Top products by revenue and volume
    top_revenue_skus = (
        product_perf.top_by_revenue_df.head(5)[
            ["sku", "product_name", "category", "net_sales", "revenue_share_pct"]
        ].to_dict(orient="records")
    )
    top_volume_skus = (
        product_perf.top_by_quantity_df.head(5)[
            ["sku", "product_name", "category", "units_sold"]
        ].to_dict(orient="records")
    )

    # RFM segment summary
    rfm_segments = rfm_report.segment_summary_df[
        ["segment", "customer_count", "total_revenue", "revenue_share_pct"]
    ].to_dict(orient="records")

    rel_fixture = str(txn_file.relative_to(repo_root)) if txn_file.is_relative_to(repo_root) else str(txn_file)

    summary_payload: dict[str, Any] = {
        "showcase_name": "UMKM Retail Analytics Technical Showcase",
        "provenance": {
            "source": "Designated Bundled Synthetic Fixture",
            "fixture_path": rel_fixture,
            "date_range": {
                "start": sales_kpis.period_start,
                "end": sales_kpis.period_end,
                "days": sales_kpis.total_days,
            },
        },
        "data_quality_audit": {
            "raw_rows": dq_report.input_rows,
            "accepted_rows": dq_report.output_rows,
            "quarantined_rows": dq_report.quarantined_rows_count,
            "duplicate_rows": dq_report.exact_duplicates_count,
            "retention_rate_pct": dq_report.retention_rate,
            "anomalies": {
                "invalid_dates": dq_report.invalid_date_count,
                "invalid_quantities_or_prices": dq_report.invalid_quantity_price_count,
                "invalid_discounts": dq_report.invalid_discount_count,
                "unknown_skus": dq_report.unknown_sku_count,
                "missing_required_fields": dq_report.missing_required_fields_count,
            },
        },
        "sales_kpis": {
            "gross_sales": sales_kpis.total_gross_sales,
            "discounts": sales_kpis.total_discount,
            "net_sales": sales_kpis.total_net_sales,
            "unique_orders": sales_kpis.unique_transactions,
            "average_transaction_value": round(sales_kpis.average_transaction_value, 2),
            "total_units_sold": sales_kpis.total_units_sold,
        },
        "monthly_trend": monthly_sales.to_dict(orient="records"),
        "top_5_products_by_revenue": top_revenue_skus,
        "top_5_products_by_volume": top_volume_skus,
        "rfm_customer_segments": rfm_segments,
        "unregistered_walk_in": {
            "transaction_count": rfm_report.unregistered_transactions_count,
            "total_revenue": rfm_report.unregistered_revenue,
        },
        "portfolio_deliverables": {
            "committed_report_reference": "examples/sample_report.xlsx",
            "screenshots_gallery": "examples/screenshots/README.md",
        },
    }

    # 3. Save lightweight demonstration artifacts only inside the validated output/showcase/ directory.
    out_path = _prepare_output_dir(repo_root)
    with _open_output_file(out_path, "showcase_summary.json") as f:
        json.dump(summary_payload, f, indent=2, default=str)

    if not quarantined_df.empty:
        with _open_output_file(out_path, "quarantined_sample.csv") as f:
            quarantined_df.to_csv(f, index=False)

    return summary_payload


def print_showcase_terminal_report(summary: dict[str, Any]) -> None:
    """Print an executive, formatted terminal summary of the showcase results."""
    prov = summary["provenance"]
    dqa = summary["data_quality_audit"]
    sales = summary["sales_kpis"]
    period = prov["date_range"]

    print("\n" + "=" * 78)
    print("        UMKM RETAIL ANALYTICS — TECHNICAL PORTFOLIO SHOWCASE")
    print("=" * 78)
    print("  Demonstrating Python-based data quality, retail analytics, and reporting.")
    print(f"  Fixture : {prov['fixture_path']}")
    print(f"  Period  : {period['start']} to {period['end']} ({period['days']} days)")
    print("-" * 78)

    print("\n[1] DATA QUALITY & HYGIENE AUDIT")
    print(f"    Raw Input Records     : {dqa['raw_rows']:,}")
    print(f"    Accepted Valid Records: {dqa['accepted_rows']:,} ({dqa['retention_rate_pct']}% retention)")
    print(f"    Quarantined Records   : {dqa['quarantined_rows']:,} (diverted for audit)")
    print(f"    Exact Duplicates      : {dqa['duplicate_rows']:,} (deduplicated)")
    print(
        f"    Reconciliation Invariant: {dqa['raw_rows']} == {dqa['accepted_rows']} + "
        f"{dqa['quarantined_rows']} + {dqa['duplicate_rows']} [VERIFIED OK]"
    )
    anom = dqa["anomalies"]
    print(
        f"    Anomalies Flagged     : Invalid Dates: {anom['invalid_dates']} | "
        f"Invalid Qty/Price: {anom['invalid_quantities_or_prices']} | "
        f"Malformed Discounts: {anom['invalid_discounts']}"
    )

    print("\n[2] SALES PERFORMANCE KPIS (EXECUTIVE SUMMARY)")
    print(f"    Gross Sales Revenue   : Rp {sales['gross_sales']:,.0f}")
    print(f"    Total Discounts       : Rp {sales['discounts']:,.0f}")
    print(f"    Total Net Sales       : Rp {sales['net_sales']:,.0f}")
    print(f"    Unique Customer Orders: {sales['unique_orders']:,} orders")
    print(f"    Average Basket (ATV)  : Rp {sales['average_transaction_value']:,.0f}")
    print(f"    Total Units Sold      : {sales['total_units_sold']:,} units")

    print("\n[3] TOP 5 REVENUE GENERATING SKUs (PARETO REVENUE DRIVERS)")
    for i, item in enumerate(summary["top_5_products_by_revenue"], 1):
        print(
            f"    {i}. {item['sku']} - {item['product_name'][:25]:<25} : "
            f"Rp {item['net_sales']:>11,.0f} ({item['revenue_share_pct']:.1f}% share)"
        )

    print("\n[4] CUSTOMER RFM BEHAVIORAL COHORTS")
    for seg in summary["rfm_customer_segments"]:
        print(
            f"    - {seg['segment']:<18}: {seg['customer_count']:>3} members "
            f"({seg['revenue_share_pct']:>5.1f}% rev) | Spend: Rp {seg['total_revenue']:>10,.0f}"
        )
    walk_in = summary["unregistered_walk_in"]
    print(
        f"    - Unregistered Walk-in : {walk_in['transaction_count']:>3} orders  | "
        f"Revenue: Rp {walk_in['total_revenue']:>10,.0f}"
    )

    print("\n[5] PORTFOLIO ASSETS & REFERENCE DELIVERABLES")
    print("    - Local Artifact Saved: output/showcase/showcase_summary.json (git-ignored)")
    print("    - Pre-generated Report: examples/sample_report.xlsx (8-sheet Executive Workbook)")
    print("    - Visual Screenshots  : examples/screenshots/README.md")
    print("==============================================================================\n")


def main() -> None:
    """CLI entrypoint for running the showcase demonstration."""
    parser = argparse.ArgumentParser(
        prog="retail-showcase",
        description="UMKM Retail Analytics: Technical Portfolio Showcase Demonstration",
    )
    parser.parse_args()

    try:
        summary = run_showcase_demo()
        print_showcase_terminal_report(summary)
    except FileNotFoundError as err:
        print(f"\n[ERROR] Showcase fixture missing: {err}", file=sys.stderr)
        sys.exit(1)
    except (ValueError, SchemaValidationError, AssertionError) as err:
        print(f"\n[ERROR] Showcase execution failed: {err}", file=sys.stderr)
        sys.exit(1)
    except Exception as err:
        print(f"\n[UNEXPECTED ERROR] {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
