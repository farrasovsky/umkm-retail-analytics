"""Configuration settings for the UMKM Retail Analytics Showcase."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ShowcaseConfig:
    """Configuration settings for the controlled portfolio showcase.

    Attributes
    ----------
    fixtures_dir : Path
        Directory containing bundled synthetic fixtures (default 'data/sample').
    output_dir : Path
        Directory where demonstration summary artifacts are saved (default 'output/showcase').
    seed : int
        Seed for deterministic generation or validation.
    currency_symbol : str
        Display symbol for currency (default 'Rp').
    """

    fixtures_dir: Path = field(default_factory=lambda: Path("data/sample"))
    output_dir: Path = field(default_factory=lambda: Path("output/showcase"))
    seed: int = 42
    currency_symbol: str = "Rp"
