"""Synthetic retail data generation with controlled realistic data quality anomalies."""

from __future__ import annotations

from datetime import datetime, timedelta
import random
from pathlib import Path
import numpy as np
import pandas as pd


CANONICAL_PRODUCTS: list[dict[str, object]] = [
    {"product_id": "PRD-0001", "sku": "SKU-0001", "product_name": "Beras Premium 5kg", "category": "Kebutuhan Pokok", "unit_price": 72000, "aliases": "SKU0001;BERAS5KG"},
    {"product_id": "PRD-0002", "sku": "SKU-0002", "product_name": "Minyak Goreng Sawit 2L", "category": "Kebutuhan Pokok", "unit_price": 35000, "aliases": "SKU0002;MINYAK2L"},
    {"product_id": "PRD-0003", "sku": "SKU-0003", "product_name": "Gula Pasir 1kg", "category": "Kebutuhan Pokok", "unit_price": 17500, "aliases": "SKU0003;GULA1KG"},
    {"product_id": "PRD-0004", "sku": "SKU-0004", "product_name": "Telur Ayam 1kg", "category": "Kebutuhan Pokok", "unit_price": 28000, "aliases": "SKU0004;TELUR1KG"},
    {"product_id": "PRD-0005", "sku": "SKU-0005", "product_name": "Mi Instan Goreng 85g", "category": "Makanan & Minuman", "unit_price": 3500, "aliases": "SKU0005;MIGORENG"},
    {"product_id": "PRD-0006", "sku": "SKU-0006", "product_name": "Mi Instan Kuah Soto 75g", "category": "Makanan & Minuman", "unit_price": 3500, "aliases": "SKU0006;MISOTO"},
    {"product_id": "PRD-0007", "sku": "SKU-0007", "product_name": "Kopi Susu Instant 10x20g", "category": "Makanan & Minuman", "unit_price": 15000, "aliases": "SKU0007;KOPISUSU"},
    {"product_id": "PRD-0008", "sku": "SKU-0008", "product_name": "Teh Celup Melati 25s", "category": "Makanan & Minuman", "unit_price": 8500, "aliases": "SKU0008;TEHMELATI"},
    {"product_id": "PRD-0009", "sku": "SKU-0009", "product_name": "Susu UHT Cokelat 250ml", "category": "Makanan & Minuman", "unit_price": 6500, "aliases": "SKU0009;SUSUUHT"},
    {"product_id": "PRD-0010", "sku": "SKU-0010", "product_name": "Biskuit Gandum 200g", "category": "Camilan & Snack", "unit_price": 12000, "aliases": "SKU0010;BISKUIT"},
    {"product_id": "PRD-0011", "sku": "SKU-0011", "product_name": "Wafer Cokelat 145g", "category": "Camilan & Snack", "unit_price": 9500, "aliases": "SKU0011;WAFER"},
    {"product_id": "PRD-0012", "sku": "SKU-0012", "product_name": "Keripik Singkong Balado 150g", "category": "Camilan & Snack", "unit_price": 14000, "aliases": "SKU0012;KERIPIK"},
    {"product_id": "PRD-0013", "sku": "SKU-0013", "product_name": "Kacang Kulit Gurih 200g", "category": "Camilan & Snack", "unit_price": 16500, "aliases": "SKU0013;KACANG"},
    {"product_id": "PRD-0014", "sku": "SKU-0014", "product_name": "Sabun Mandi Cair 450ml", "category": "Perawatan Diri", "unit_price": 24500, "aliases": "SKU0014;SABUNCAIR"},
    {"product_id": "PRD-0015", "sku": "SKU-0015", "product_name": "Shampoo Anti Ketombe 160ml", "category": "Perawatan Diri", "unit_price": 26000, "aliases": "SKU0015;SHAMPOO"},
    {"product_id": "PRD-0016", "sku": "SKU-0016", "product_name": "Pasta Gigi Herbal 190g", "category": "Perawatan Diri", "unit_price": 18500, "aliases": "SKU0016;PASTAGIGI"},
    {"product_id": "PRD-0017", "sku": "SKU-0017", "product_name": "Sikat Gigi Charcoal 3s", "category": "Perawatan Diri", "unit_price": 21000, "aliases": "SKU0017;SIKATGIGI"},
    {"product_id": "PRD-0018", "sku": "SKU-0018", "product_name": "Sabun Cuci Piring Jeruk Nipis 750ml", "category": "Perlengkapan Rumah", "unit_price": 14500, "aliases": "SKU0018;CUCIPIRING"},
    {"product_id": "PRD-0019", "sku": "SKU-0019", "product_name": "Deterjen Bubuk Konsentrat 800g", "category": "Perlengkapan Rumah", "unit_price": 22000, "aliases": "SKU0019;DETERJEN"},
    {"product_id": "PRD-0020", "sku": "SKU-0020", "product_name": "Pembersih Lantai Lavender 750ml", "category": "Perlengkapan Rumah", "unit_price": 13500, "aliases": "SKU0020;PEL"},
    {"product_id": "PRD-0021", "sku": "SKU-0021", "product_name": "Tisu Wajah 250 Sheets", "category": "Perlengkapan Rumah", "unit_price": 15500, "aliases": "SKU0021;TISU"},
    {"product_id": "PRD-0022", "sku": "SKU-0022", "product_name": "Kantong Sampah Roll 24s", "category": "Perlengkapan Rumah", "unit_price": 16000, "aliases": "SKU0022;TRASHBAG"},
    {"product_id": "PRD-0023", "sku": "SKU-0023", "product_name": "Saus Sambal Botol 335ml", "category": "Makanan & Minuman", "unit_price": 15000, "aliases": "SKU0023;SAUSSAMBAL"},
    {"product_id": "PRD-0024", "sku": "SKU-0024", "product_name": "Kecap Manis Refill 550ml", "category": "Makanan & Minuman", "unit_price": 21500, "aliases": "SKU0024;KECAP"},
    {"product_id": "PRD-0025", "sku": "SKU-0025", "product_name": "Mentega Serbaguna 200g", "category": "Kebutuhan Pokok", "unit_price": 11500, "aliases": "SKU0025;MENTEGA"},
    {"product_id": "PRD-0026", "sku": "SKU-0026", "product_name": "Tepung Terigu Serbaguna 1kg", "category": "Kebutuhan Pokok", "unit_price": 13000, "aliases": "SKU0026;TEPUNG"},
    {"product_id": "PRD-0027", "sku": "SKU-0027", "product_name": "Garam Beryodium 250g", "category": "Kebutuhan Pokok", "unit_price": 4000, "aliases": "SKU0027;GARAM"},
    {"product_id": "PRD-0028", "sku": "SKU-0028", "product_name": "Air Mineral Galon 19L", "category": "Makanan & Minuman", "unit_price": 22000, "aliases": "SKU0028;GALON"},
    {"product_id": "PRD-0029", "sku": "SKU-0029", "product_name": "Air Mineral Botol 600ml", "category": "Makanan & Minuman", "unit_price": 4000, "aliases": "SKU0029;AIR600"},
    {"product_id": "PRD-0030", "sku": "SKU-0030", "product_name": "Minuman Isotonik 500ml", "category": "Makanan & Minuman", "unit_price": 7500, "aliases": "SKU0030;ISOTONIK"},
]


def generate_synthetic_product_master() -> pd.DataFrame:
    """Generate product master catalog."""
    rows = []
    for p in CANONICAL_PRODUCTS:
        rows.append({
            "product_id": p["product_id"],
            "sku": p["sku"],
            "product_name": p["product_name"],
            "category": p["category"],
            "default_unit_price": p["unit_price"],
            "sku_aliases": p["aliases"],
        })
    return pd.DataFrame(rows)


def generate_synthetic_inventory(seed: int = 42) -> pd.DataFrame:
    """Generate deterministic inventory snapshot with realistic stock levels and reorder points."""
    rng = random.Random(seed)
    rows = []

    for i, p in enumerate(CANONICAL_PRODUCTS):
        # Create varied stock health profiles
        if i in [0, 1, 4, 13]:  # Fast movers with low stock (triggering reorder alert)
            stock = rng.randint(2, 12)
            reorder = rng.randint(15, 25)
        elif i in [2, 7, 14, 18]:  # Warning zone (near reorder point)
            stock = rng.randint(16, 28)
            reorder = 20
        elif i in [11, 20, 21]:  # Overstocked slow movers
            stock = rng.randint(120, 200)
            reorder = 15
        else:  # Normal adequate stock
            stock = rng.randint(35, 90)
            reorder = rng.randint(10, 20)

        rows.append({
            "product_id": p["product_id"],
            "sku": p["sku"],
            "product_name": p["product_name"],
            "category": p["category"],
            "stock_on_hand": stock,
            "reorder_point": reorder,
            "unit_cost": int(float(p["unit_price"]) * 0.78),
        })

    return pd.DataFrame(rows)


def generate_synthetic_transactions(seed: int = 42, target_line_items: int = 1800) -> pd.DataFrame:
    """Generate synthetic retail transactions with realistic customer cohorts and controlled data noise."""
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)

    # 1. Setup Customer Cohorts (CUST-0001 to CUST-0150)
    # Loyal/Champions: CUST-0001 to CUST-0025 (frequent, high value)
    # Potential Loyalists: CUST-0026 to CUST-0050 (recent, 1-2 visits)
    # At Risk: CUST-0051 to CUST-0075 (frequent in past, no recent visits)
    # Needs Attention: CUST-0076 to CUST-0110 (moderate)
    # Lost: CUST-0111 to CUST-0140 (1 visit early on)
    # Anonymous walk-ins: 30% of transactions have None/blank customer_id
    customers = [f"CUST-{i:04d}" for i in range(1, 141)]

    channels = ["Toko Fisik", "Toko Fisik", "Toko Fisik", "WhatsApp Order", "Marketplace"]
    payment_methods = ["Tunai", "QRIS", "QRIS", "Transfer Bank", "Debit"]

    start_date = datetime(2026, 4, 1, 8, 30)
    end_date = datetime(2026, 9, 30, 21, 00)
    total_days = (end_date - start_date).days

    # Frequently paired item SKUs for market basket testing:
    # 1. Mi Goreng (SKU-0005) + Teh Melati (SKU-0008)
    # 2. Kopi Susu (SKU-0007) + Biskuit Gandum (SKU-0010)
    # 3. Sabun Cair (SKU-0014) + Shampoo (SKU-0015)
    # 4. Beras 5kg (SKU-0001) + Minyak 2L (SKU-0002)
    # 5. Sabun Cuci Piring (SKU-0018) + Deterjen (SKU-0019)

    records: list[dict[str, object]] = []
    txn_id_counter = 1

    while len(records) < target_line_items - 30:
        txn_id = f"TXN-{txn_id_counter:05d}"
        txn_id_counter += 1

        # Customer selection
        is_anonymous = rng.random() < 0.32
        if is_anonymous:
            cust_id = ""
            day_offset = rng.randint(0, total_days)
        else:
            cust_idx = rng.randint(0, len(customers) - 1)
            cust_id = customers[cust_idx]
            # Time distribution by cohort to guarantee realistic RFM segmentation
            if cust_idx < 25:  # Champions & Loyal (recent & throughout period)
                day_offset = rng.randint(total_days - 60, total_days) if rng.random() < 0.65 else rng.randint(0, total_days)
            elif cust_idx < 50:  # Potential Loyalists (recent visits)
                day_offset = rng.randint(total_days - 30, total_days)
            elif cust_idx < 75:  # At Risk (visited 90-180 days ago, stopped visiting recently)
                day_offset = rng.randint(0, total_days - 60)
            elif cust_idx < 110:  # Needs Attention
                day_offset = rng.randint(total_days - 90, total_days - 20)
            else:  # Lost
                day_offset = rng.randint(0, 45)

        txn_dt = start_date + timedelta(days=day_offset, hours=rng.randint(0, 12), minutes=rng.randint(0, 59))
        channel = rng.choice(channels)
        pay_method = rng.choice(payment_methods)

        # Decide items in this transaction (1 to 4 items)
        basket_type = rng.random()
        chosen_products: list[dict[str, object]] = []

        if basket_type < 0.25:
            # Pair 1: Mi Goreng + Teh Melati
            chosen_products.append(CANONICAL_PRODUCTS[4])
            chosen_products.append(CANONICAL_PRODUCTS[7])
        elif basket_type < 0.45:
            # Pair 2: Kopi Susu + Biskuit
            chosen_products.append(CANONICAL_PRODUCTS[6])
            chosen_products.append(CANONICAL_PRODUCTS[9])
        elif basket_type < 0.60:
            # Pair 3: Beras + Minyak
            chosen_products.append(CANONICAL_PRODUCTS[0])
            chosen_products.append(CANONICAL_PRODUCTS[1])
        elif basket_type < 0.70:
            # Pair 4: Sabun Mandi + Shampoo
            chosen_products.append(CANONICAL_PRODUCTS[13])
            chosen_products.append(CANONICAL_PRODUCTS[14])
        else:
            # Random selection
            num_items = rng.choices([1, 2, 3], weights=[0.55, 0.35, 0.10])[0]
            chosen_products = rng.sample(CANONICAL_PRODUCTS, num_items)

        for p in chosen_products:
            # Quantity logic: small snacks/mi instan sell more units
            if p["category"] in ["Makanan & Minuman", "Camilan & Snack"] and p["unit_price"] < 10000:
                qty = rng.choices([1, 2, 3, 5, 10], weights=[0.4, 0.3, 0.15, 0.1, 0.05])[0]
            else:
                qty = rng.choices([1, 2, 3], weights=[0.8, 0.15, 0.05])[0]

            # Line level discount (approx 8% of transactions have discounts)
            discount = 0.0
            if rng.random() < 0.08:
                discount = float(rng.choice([1000, 2000, 5000]))

            records.append({
                "transaction_id": txn_id,
                "transaction_date": txn_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "customer_id": cust_id,
                "product_id": p["product_id"],
                "sku": p["sku"],
                "product_name": p["product_name"],
                "category": p["category"],
                "quantity": qty,
                "unit_price": p["unit_price"],
                "discount_amount": discount,
                "sales_channel": channel,
                "payment_method": pay_method,
            })

    # Now intentionally inject controlled data quality issues:
    # Issue 1: Whitespace and case anomalies in SKUs (15 records)
    for idx in rng.sample(range(len(records)), 15):
        raw_sku = str(records[idx]["sku"])
        if rng.random() < 0.5:
            records[idx]["sku"] = f"  {raw_sku}  "
        else:
            records[idx]["sku"] = raw_sku.lower()

    # Issue 2: Date format variations (25 records)
    for idx in rng.sample(range(len(records)), 25):
        dt_val = datetime.strptime(str(records[idx]["transaction_date"]), "%Y-%m-%d %H:%M:%S")
        variant = rng.choice([
            dt_val.strftime("%d/%m/%Y"),
            dt_val.strftime("%Y/%m/%d %H:%M"),
            dt_val.strftime("%Y-%m-%d"),
        ])
        records[idx]["transaction_date"] = variant

    # Issue 3: Duplicate rows (6 exact duplicates)
    dup_samples = [records[i].copy() for i in rng.sample(range(len(records)), 6)]
    records.extend(dup_samples)

    # Issue 4: Invalid/unparseable dates (4 records)
    bad_dates = ["2026-02-30", "INVALID_DATE", "99/99/2026", "2026-13-45"]
    for i, bad_d in enumerate(bad_dates):
        rec = records[rng.randint(0, len(records) - 1)].copy()
        rec["transaction_id"] = f"TXN-ERR-D{i+1}"
        rec["transaction_date"] = bad_d
        records.append(rec)

    # Issue 5: Invalid quantity or unit_price (4 records)
    bad_nums = [
        {"quantity": 0, "unit_price": 10000},
        {"quantity": -2, "unit_price": 15000},
        {"quantity": "N/A", "unit_price": 20000},
        {"quantity": 1, "unit_price": -5000},
    ]
    for i, b_num in enumerate(bad_nums):
        rec = records[rng.randint(0, len(records) - 1)].copy()
        rec["transaction_id"] = f"TXN-ERR-N{i+1}"
        rec.update(b_num)
        records.append(rec)

    # Issue 6: Missing required fields (4 records)
    bad_reqs = [
        {"transaction_id": ""},
        {"sku": ""},
        {"transaction_date": ""},
        {"unit_price": ""},
    ]
    for i, b_req in enumerate(bad_reqs):
        rec = records[rng.randint(0, len(records) - 1)].copy()
        rec.update(b_req)
        records.append(rec)

    df = pd.DataFrame(records)
    # Shuffle deterministically to mix clean and messy records
    df = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    return df


def generate_and_save_all_sample_data(
    data_dir: Path | str = "data/sample",
    seed: int = 42,
) -> tuple[Path, Path, Path]:
    """Generate and persist all synthetic datasets to disk."""
    out_dir = Path(data_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    master_path = out_dir / "product_master.csv"
    inv_path = out_dir / "inventory_snapshot.csv"
    txn_path = out_dir / "raw_transactions.csv"

    pm_df = generate_synthetic_product_master()
    inv_df = generate_synthetic_inventory(seed=seed)
    txn_df = generate_synthetic_transactions(seed=seed)

    pm_df.to_csv(master_path, index=False, encoding="utf-8")
    inv_df.to_csv(inv_path, index=False, encoding="utf-8")
    txn_df.to_csv(txn_path, index=False, encoding="utf-8")

    return txn_path, inv_path, master_path

