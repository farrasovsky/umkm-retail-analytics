"""Source-controlled integrity manifest for the bundled synthetic showcase fixtures.

The public showcase only processes the designated synthetic fixture files listed here.
Each file must match its expected SHA-256 digest before it is read.

Updating the manifest (intentional fixture change only)
-------------------------------------------------------
1. Regenerate the fixtures deliberately, e.g. ``python scripts/generate_sample_data.py --seed 42``.
2. Review the diff of ``data/sample/`` to confirm the change is intended and synthetic.
3. Recompute digests: ``shasum -a 256 data/sample/raw_transactions.csv data/sample/product_master.csv``
   (or ``sha256sum`` on Linux).
4. Paste the new digests below and run ``pytest``.

The expected digests are never derived at runtime from the files being verified.
"""

from __future__ import annotations

FIXTURE_DIR_PARTS: tuple[str, ...] = ("data", "sample")

EXPECTED_FIXTURE_SHA256: dict[str, str] = {
    "raw_transactions.csv": "cadd1a1301dcb675334c3ba9d7671be08bb8b5685b00229ca6d516dd7e6ebf0a",
    "product_master.csv": "b0d8cfa75276a0a6834e5b7f630b4c65a4c96562ae4a9089dca088c1a25b8909",
}

OUTPUT_DIR_PARTS: tuple[str, ...] = ("output", "showcase")

