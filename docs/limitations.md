# System Limitations & Boundary Disclosures

This document outlines the scope, technical boundaries, and explicit non-goals of the **UMKM Retail Analytics Technical Showcase**.

---

## 1. Technical Showcase Scope

- **Technical Portfolio Showcase Only**: This repository is a technical engineering showcase demonstrating data engineering concepts on synthetic datasets. It is not a general-purpose customer-data processing service or turnkey analytics product.
- **No Bring-Your-Own-Data Workflow**: The public demonstration runner is strictly parameterless and locked to the project's bundled synthetic fixture (`data/sample/raw_transactions.csv`). It does not accept arbitrary external customer files or unvetted directory structures. Compatibility with arbitrary POS exports has not been claimed or tested.
- **Pre-Generated Reference Deliverable**: The public demo prints an executive summary to the terminal and saves a lightweight demonstration artifact to `output/showcase/showcase_summary.json`. The complete eight-sheet Excel workbook is provided as a pre-generated reference portfolio artifact and is not included as a runnable public workflow.
- **Batch Processing Only**: The code demonstrates offline local batch processing. It does not ingest live event streams (Kafka/Pulsar) or poll real-time POS webhooks.
- **No Direct Hardware POS Connectors**: The system does not interface via USB/Bluetooth with receipt printers or cash registers, nor does it connect to marketplace APIs (Tokopedia, Shopee, TikTok Shop OAuth).

---

## 2. Analytical & Statistical Boundaries

- **Descriptive, Not Predictive**: All analytical outputs (RFM cohorts, sales run-rates, market basket pairs) are strictly descriptive historical summaries. The pipeline does not employ machine-learning churn forecasting, auto-regressive demand forecasting (ARIMA/Prophet), or uplift modeling.
- **Static Run-Rate Limitations**: The "Estimated Days of Stock" metric assumes static historical sales velocity. It does not account for seasonality, promotional spikes, lead time variance, minimum order quantities (MOQ), or supply chain delivery delays.
- **Revenue Is Not Cash Flow or Profit**: Net sales represents recognized top-line transactional turnover. It does not reflect net margins, operating expenses, cost of goods sold, tax withholdings, or payment settlement delays.
- **Market Basket Correlation vs. Causation**: Association rules reflect co-occurrence frequency within the recorded dataset. A high lift ratio indicates statistical affinity, not proof that stocking item A caused the customer to purchase item B.

---

## 3. Data Cleansing & Contract Integrity

- **Strict Bundled Synthetic Contract**: The showcase demonstrates schema validation and hygiene exclusively against the contract specified in `docs/data-schema.md` on bundled synthetic fixtures. It does not parse unstructured PDF receipts, hand-written ledger photos, or arbitrary unformatted text.
- **Deterministic Quarantine Policy**: Records missing required primary keys, containing unparseable timestamps, or containing malformed financial values are quarantined with descriptive reasons. The pipeline will not guess or impute missing transaction dates or prices.
- **Synthetic Data Demonstration**: The bundled sample dataset (`data/sample/`) is purely synthetic and deterministic (seed 42). All analytical findings are illustrative synthetic examples, not verified commercial business outcomes.
