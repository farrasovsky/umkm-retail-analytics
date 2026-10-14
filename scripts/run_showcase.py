"""Public entrypoint script to execute the UMKM Retail Analytics Technical Showcase.

Usage:
    python scripts/run_showcase.py
"""

from __future__ import annotations

from pathlib import Path
import sys

# Ensure src is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from retail_analytics.showcase.summary import main

if __name__ == "__main__":
    main()

