# Public Portfolio Scope & Disclosures

This document outlines the scope, purpose, and intentional design boundaries of the **UMKM Retail Analytics Technical Showcase** repository.

---

## 1. Portfolio Purpose & Public Scope

The **UMKM Retail Analytics** repository is published as a **technical engineering portfolio showcase**. Its primary purpose is to demonstrate practical, production-style Python data engineering, schema validation contracts, deterministic date handling, data quality reconciliation, and retail business analytics concepts using synthetic data.

This codebase is intentionally designed as a focused portfolio showcase rather than a general-purpose, turnkey analytics product or customer data processing service:

- **Synthetic Retail Data Only**: All transaction records, customer tokens, product SKUs, and inventory figures in `data/sample/` are 100% synthetic, generated with fixed deterministic seeds. The repository contains no real customer data, personal identifiables, confidential business records, or production infrastructure credentials.
- **Controlled Showcase Demonstration**: The public demo runner (`scripts/run_showcase.py` / `retail-analytics`) executes a focused, parameterless demonstration strictly bound to the bundled synthetic fixtures. It does not accept arbitrary external customer files or unvetted directory inputs.
- **Pre-Generated Reference Deliverable**: The committed workbook ([`examples/sample_report.xlsx`](../examples/sample_report.xlsx)) and visual gallery ([`examples/screenshots/`](../examples/screenshots/)) are pre-generated reference portfolio artifacts demonstrating deliverable format, data density, and executive presentation quality. The complete multi-sheet workbook generation workflow is not provided as a runnable public pipeline.
- **Engineering Demonstration**: Public source code illustrates modular design, defensive programming, automated test coverage, type safety, and data accounting invariants. It demonstrates engineering capability and is not intended to represent the full private service infrastructure of bacadataku.

---

## 2. Technical Capabilities Demonstrated

The showcase demonstrates several foundational data engineering and analytics techniques:

1. **Defensive Ingestion**: Schema contract enforcement with encoding resilience (`utf-8-sig`, `utf-8`, `latin-1`) and mandatory column presence verification.
2. **Deterministic Data Hygiene**: Resolving multi-format timestamps (ISO precedence over Indonesian `DD/MM/YYYY`), positive numeric coercions, financial discount validations, and quarantine isolation with audit trails.
3. **Data Quality Reconciliation**: Guaranteeing strict row-accounting invariants ($\text{Input} = \text{Accepted} + \text{Quarantined} + \text{Duplicates}$) with zero silent record drops.
4. **Stateless Retail Analytics**: Pure calculation functions for Sales KPIs, Pareto catalog analysis, customer RFM quintiles, inventory velocity run-rates, and market basket co-occurrence affinities.
5. **Rigorous Quality Assurance**: Comprehensive automated unit, integration, and security regression test suites verifying schema boundaries, symlink defense, path confinement, and deliverable integrity.

---

## 3. Terms of Use & Copyright

Copyright © 2026 bacadataku. All rights reserved.

> No open-source license is granted. This repository is published as a technical portfolio showcase. The original code and assets remain under their respective copyright. GitHub users may view and fork the public repository as permitted by GitHub's Terms of Service. No additional permission to reuse, modify, or redistribute the original code is granted through an open-source license.
