"""Data quality metrics tracking and validation reporting."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import pandas as pd


@dataclass
class DataQualityReport:
    """Tracks before-and-after data hygiene metrics across the pipeline.

    Attributes
    ----------
    input_rows : int
        Total rows received in the raw input file.
    output_rows : int
        Total clean line items retained for analytical processing.
    exact_duplicates_count : int
        Total exact duplicate rows detected and eliminated.
    invalid_date_count : int
        Rows with unparseable or out-of-range timestamps.
    missing_required_fields_count : int
        Rows missing primary keys, SKUs, or mandatory transactional fields.
    invalid_quantity_price_count : int
        Rows with non-numeric, negative, or zero quantities/prices.
    invalid_discount_count : int
        Rows with non-numeric, malformed, or negative discount amounts.
    unknown_sku_count : int
        Rows referencing SKUs missing from the product master.
    corrected_sku_formatting_count : int
        Rows where whitespace, lowercase, or punctuation was corrected.
    quarantined_rows_count : int
        Total invalid records quarantined and excluded from analysis.
    clean_unique_transactions : int
        Number of distinct transactions in the clean analytical set.
    warnings : list[str]
        List of specific warnings or anomalies identified during processing.
    """

    input_rows: int = 0
    output_rows: int = 0
    exact_duplicates_count: int = 0
    invalid_date_count: int = 0
    missing_required_fields_count: int = 0
    invalid_quantity_price_count: int = 0
    invalid_discount_count: int = 0
    unknown_sku_count: int = 0
    corrected_sku_formatting_count: int = 0
    quarantined_rows_count: int = 0
    clean_unique_transactions: int = 0
    warnings: list[str] = field(default_factory=list)

    @property
    def retention_rate(self) -> float:
        """Percentage of raw input rows retained after cleaning."""
        if self.input_rows == 0:
            return 0.0
        return round((self.output_rows / self.input_rows) * 100, 2)

    def to_dict(self) -> dict[str, object]:
        """Convert report metrics to a dictionary."""
        d = asdict(self)
        d["retention_rate_pct"] = self.retention_rate
        return d

    def to_summary_dataframe(self) -> pd.DataFrame:
        """Convert metrics to a structured DataFrame for Excel and reporting."""
        records = [
            ("Total Raw Input Rows", self.input_rows, "Initial row count received from transaction source"),
            ("Clean Analytical Rows", self.output_rows, "Accepted line items passed to analytics engine"),
            ("Data Retention Rate", f"{self.retention_rate}%", "Percentage of raw records retained after quality filters"),
            ("Exact Duplicate Rows Removed", self.exact_duplicates_count, "Identical duplicate rows removed from dataset"),
            ("Quarantined Invalid Rows", self.quarantined_rows_count, "Total records excluded due to data corruption or missing required fields"),
            ("Invalid or Unparseable Dates", self.invalid_date_count, "Dates failing parsing or falling outside valid calendar ranges"),
            ("Missing Mandatory Fields", self.missing_required_fields_count, "Records missing transaction ID, SKU, quantity, unit price, or date"),
            ("Invalid Quantity or Price", self.invalid_quantity_price_count, "Records with non-numeric, zero, or negative quantity or price"),
            ("Invalid or Malformed Discounts", self.invalid_discount_count, "Records with malformed non-numeric or negative discount amounts"),
            ("SKU Formatting Corrections", self.corrected_sku_formatting_count, "SKUs standardized (stripped whitespace, uppercase normalized)"),
            ("Unmatched / Unknown SKUs", self.unknown_sku_count, "SKUs missing from canonical product master catalog"),
            ("Clean Unique Transactions", self.clean_unique_transactions, "Count of distinct valid transaction orders"),
        ]
        return pd.DataFrame(records, columns=["Metric", "Value", "Description"])
