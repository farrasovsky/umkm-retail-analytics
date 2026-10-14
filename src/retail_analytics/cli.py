"""Command Line Interface for the UMKM Retail Analytics Technical Showcase.

This CLI executes the controlled demonstration on bundled synthetic data.
It does not accept arbitrary customer data inputs or output paths.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .showcase.summary import print_showcase_terminal_report, run_showcase_demo


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for technical showcase."""
    parser = argparse.ArgumentParser(
        prog="retail-analytics",
        description=(
            "UMKM Retail Analytics — Technical Portfolio Showcase.\n"
            "Demonstrates retail data engineering, validation, and analytics on bundled synthetic data."
        ),
    )
    return parser.parse_args(args)


def main() -> None:
    """CLI entrypoint."""
    parse_args()

    try:
        summary = run_showcase_demo()
        print_showcase_terminal_report(summary)
    except FileNotFoundError as err:
        print(f"\n[ERROR] Showcase fixture missing: {err}", file=sys.stderr)
        sys.exit(1)
    except Exception as err:
        print(f"\n[ERROR] Showcase execution failed: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
