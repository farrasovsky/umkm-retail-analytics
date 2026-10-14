"""Tests for DataQualityReport metrics dataclass."""

from retail_analytics.cleaning.validation import DataQualityReport


def test_data_quality_report_retention():
    dq = DataQualityReport(
        input_rows=100,
        output_rows=95,
        exact_duplicates_count=3,
        quarantined_rows_count=2,
    )
    assert dq.retention_rate == 95.0
    summary_df = dq.to_summary_dataframe()
    assert len(summary_df) >= 10
    assert "Clean Analytical Rows" in summary_df["Metric"].values


def test_zero_rows_retention():
    dq = DataQualityReport(input_rows=0, output_rows=0)
    assert dq.retention_rate == 0.0

