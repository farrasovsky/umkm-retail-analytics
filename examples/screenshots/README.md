# Report Screenshots & Visual Gallery

This directory contains high-resolution visual previews rendered directly from the committed executive Excel report ([`examples/sample_report.xlsx`](../sample_report.xlsx)).

## Available Previews

1. **`executive-summary.png`**:
   - Executive performance dashboard from worksheet `01_EXECUTIVE_SUMMARY`.
   - Displays 5 high-level KPI cards (Total Net Sales, Total Orders, ATV, Units Sold, Reorder Alerts), Monthly Net Sales bar chart, and core analytical takeaways.

2. **`sales-analysis.png`**:
   - Detailed financial and channel breakdown from worksheet `02_SALES_OVERVIEW`.
   - Displays channel contribution pie chart (Store, WhatsApp, Marketplace), merchandise category rankings, and chronological monthly financial table.

3. **`data-quality.png`**:
   - Data hygiene and audit reconciliation report from worksheet `07_DATA_QUALITY`.
   - Displays before-and-after ingestion metrics (98.99% retention), strict row reconciliation proof ($1,788 = 1,770 + 12 + 6$), and sample quarantined record audit table.

## Rendering Origin & Reproducibility

These previews were rendered from the actual data and tables of [`examples/sample_report.xlsx`](../sample_report.xlsx) using `scripts/render_screenshots.py`. All figures, counts, and categories match the synthetic demonstration dataset deterministically.
