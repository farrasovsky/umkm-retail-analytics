"""Deterministic date parsing and normalization for retail transactions."""

from __future__ import annotations

from datetime import datetime
import pandas as pd


SUPPORTED_ISO_FORMATS: tuple[str, ...] = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d %H:%M",
    "%Y/%m/%d",
)

SUPPORTED_DAYFIRST_FORMATS: tuple[str, ...] = (
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y",
    "%d-%m-%Y %H:%M:%S",
    "%d-%m-%Y %H:%M",
    "%d-%m-%Y",
)

SUPPORTED_MONTHFIRST_FORMATS: tuple[str, ...] = (
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
    "%m/%d/%Y",
    "%m-%d-%Y %H:%M:%S",
    "%m-%d-%Y %H:%M",
    "%m-%d-%Y",
)


def parse_single_date(val: object, dayfirst: bool = True) -> pd.Timestamp | None:
    """Parse a single date string deterministically into a pd.Timestamp.

    Parameters
    ----------
    val : object
        Input date value (string, datetime, Timestamp, etc.).
    dayfirst : bool, default True
        If True, slash and dash dates follow Indonesian/Commonwealth convention (DD/MM/YYYY).

    Returns
    -------
    pd.Timestamp | None
        Normalized Timestamp or None if invalid or out of range (2000-2050).
    """
    if pd.isna(val) or val is None:
        return None

    if isinstance(val, (datetime, pd.Timestamp)):
        if 2000 <= val.year <= 2050:
            return pd.Timestamp(val)
        return None

    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "null", "nat", ""):
        return None

    # Priority 1: ISO formats if starts with 4-digit year (YYYY- or YYYY/)
    if len(s) >= 10 and s[:4].isdigit() and s[4] in ("-", "/"):
        for fmt in SUPPORTED_ISO_FORMATS:
            try:
                dt = datetime.strptime(s, fmt)
                if 2000 <= dt.year <= 2050:
                    return pd.Timestamp(dt)
            except ValueError:
                pass

    # Priority 2: Slash / Dash formats with explicit dayfirst precedence
    non_iso_formats = (
        SUPPORTED_DAYFIRST_FORMATS + SUPPORTED_MONTHFIRST_FORMATS
        if dayfirst
        else SUPPORTED_MONTHFIRST_FORMATS + SUPPORTED_DAYFIRST_FORMATS
    )

    for fmt in non_iso_formats:
        try:
            dt = datetime.strptime(s, fmt)
            if 2000 <= dt.year <= 2050:
                return pd.Timestamp(dt)
        except ValueError:
            pass

    return None


def parse_date_series(
    series: pd.Series,
    dayfirst: bool = True,
) -> tuple[pd.Series, pd.Series]:
    """Parse an entire series of date strings deterministically.

    Parameters
    ----------
    series : pd.Series
        Raw transaction date strings.
    dayfirst : bool, default True
        Indonesian/Commonwealth default parsing convention for slash dates.

    Returns
    -------
    tuple[pd.Series, pd.Series]
        (parsed_series, is_valid_boolean_mask)
    """
    parsed = series.apply(lambda v: parse_single_date(v, dayfirst=dayfirst))
    valid_mask = parsed.notna()
    return parsed, valid_mask

