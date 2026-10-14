# Data Schema & Contracts — Technical Showcase

This document specifies the synthetic data contracts, validation constraints, and canonical fields demonstrated in the **UMKM Retail Analytics Technical Showcase**.

---

## 1. Transactions Dataset (`raw_transactions.csv`)

The transactions fixture represents raw Point of Sale (POS) exports at the line-item level.

| Field Name | Type | Requirement | Normalization Rule | Validation Rule | Action When Invalid | Business Description |
|---|---|---|---|---|---|---|
| `transaction_id` | String | **Mandatory** | Trim whitespace, uppercase | Must be non-empty string | Quarantined (`Missing mandatory field`) | Unique identifier for a sales basket or receipt. |
| `transaction_date` | String / DateTime | **Mandatory** | Parsed via multi-format engine (`YYYY-MM-DD`, `DD/MM/YYYY`) | Must parse to calendar date between 2000 and 2050 | Quarantined (`Unparseable date`) | Timestamp when transaction was recorded. |
| `sku` | String | **Mandatory** | Trim whitespace, uppercase, strip extraneous tabs | Must be non-empty string; mapped via master catalog if aliases match | Quarantined (`Missing mandatory field`) | Stock Keeping Unit code identifying the item. |
| `quantity` | Numeric (Integer / Float) | **Mandatory** | Cast to numeric | Must be strictly positive ($> 0$) | Quarantined (`Invalid numerical values`) | Number of units sold in this line item. |
| `unit_price` | Numeric (Float) | **Mandatory** | Cast to float | Must be non-negative ($\ge 0$) | Quarantined (`Invalid numerical values`) | Retail selling price per unit before line discounts. |
| `customer_id` | String | *Optional* | Trim whitespace, uppercase; `nan`, `none`, empty strings cast to `None` | None | Preserved as `None` (Unregistered Walk-in) | Identifier for registered loyalty or customer account. |
| `product_id` | String | *Optional* | Trim whitespace | Looked up from Product Master if absent | Filled with Master ID or left blank | Canonical internal system identifier for product. |
| `product_name` | String | *Optional* | Trim whitespace | Looked up from Product Master if blank | Filled with `Unknown Product` | Human-readable product description. |
| `category` | String | *Optional* | Trim whitespace, Title Case | Looked up from Product Master if blank | Filled with `Uncategorized` | Merchandising department or category. |
| `discount_amount` | Numeric (Float) | *Optional* | Cast to float; blank/null defaults to $0.0$ | Must be numeric and $\ge 0$ | Quarantined (`Malformed or negative discount value`) | Monetary discount applied to this line item. |
| `sales_channel` | String | *Optional* | Trim whitespace, Title Case | None | Defaults to `Store` | Channel where order occurred (e.g. `Store`, `WhatsApp`, `Marketplace`). |
| `payment_method` | String | *Optional* | Trim whitespace, Title Case | None | Defaults to `Cash` | Tender type used (e.g. `Cash`, `QRIS`, `Transfer`). |

---

## 2. Inventory Snapshot (`inventory_snapshot.csv`)

Represents a point-in-time snapshot of warehouse or shelf stock levels.

| Field Name | Type | Requirement | Normalization Rule | Validation Rule | Business Description |
|---|---|---|---|---|---|
| `sku` | String | **Mandatory** | Trim whitespace, uppercase | Must exist in catalog | Item SKU code matching transaction lines. |
| `stock_on_hand` | Integer | **Mandatory** | Cast to integer, fillna $0$ | Must be integer ($\ge 0$) | Current physical inventory count available on shelf. |
| `reorder_point` | Integer | **Mandatory** | Cast to integer, fillna $0$ | Must be integer ($\ge 0$) | Minimum safety threshold triggering replenishment. |
| `product_name` | String | *Optional* | Trim whitespace | None | Descriptive item name. |
| `category` | String | *Optional* | Title Case | None | Category grouping. |
| `unit_cost` | Float | *Optional* | Cast to float | None | Wholesale purchase cost per unit. |

---

## 3. Product Master Catalog (`product_master.csv`)

Canonical source of truth for merchandise taxonomy, standardized descriptions, and alias mappings.

| Field Name | Type | Requirement | Description |
|---|---|---|---|
| `sku` | String | **Mandatory** | Canonical standardized SKU code. |
| `product_name` | String | **Mandatory** | Canonical product label. |
| `category` | String | **Mandatory** | Official merchandising category. |
| `default_unit_price` | Float | *Optional* | Standard shelf price. |
| `sku_aliases` | String | *Optional* | Semicolon-delimited list of legacy or dirty SKUs (e.g. `MIGORENG;SKU0005`). |

---

## 4. Quarantine Classification Taxonomy

When raw records fail mandatory data validation, they are diverted into quarantine storage with an explicit reason:

1. `Missing mandatory transactional field (ID, SKU, Date, Qty, or Price)`: The row lacks critical attributes needed for processing.
2. `Unparseable or out-of-range transaction date`: The timestamp string cannot be parsed or lies outside calendar years 2000–2050.
3. `Invalid numerical values (qty <= 0 or price < 0)`: Quantity is zero or negative, or selling price is corrupt.
4. `Malformed or negative discount value`: The discount cell contains non-numeric text (e.g. `"N/A"`, `"oops"`) or a negative value.
