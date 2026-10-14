"""CLI script to generate or regenerate deterministic synthetic retail datasets."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Ensure src is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from retail_analytics.synthetic_data import generate_and_save_all_sample_data


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regenerate synthetic retail sample data for umkm-retail-analytics-engine."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/sample"),
        help="Target folder for generated CSV files (default: data/sample).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic generation (default: 42).",
    )

    args = parser.parse_args()
    print(f"Generating synthetic datasets with seed={args.seed} in {args.output_dir}...")
    txn_p, inv_p, pm_p = generate_and_save_all_sample_data(data_dir=args.output_dir, seed=args.seed)
    print(f"[OK] Transactions: {txn_p}")
    print(f"[OK] Inventory:    {inv_p}")
    print(f"[OK] Catalog:      {pm_p}")
    print("Sample generation complete.")


if __name__ == "__main__":
    main()

