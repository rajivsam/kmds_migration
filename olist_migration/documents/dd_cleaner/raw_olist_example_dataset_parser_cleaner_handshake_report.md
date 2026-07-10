# 📑 Data Dictionary: Provisional Entity Assignment Report
**Generation Timestamp:** `2026-07-06 11:28:23`
**Source Blueprint:** `olist_example_dd.csv`

### 🏗️ Structural Assessment
- **Dataset Type:** `cross-sectional`
> ⚠️ **Note:** This dataset type is provided by configuration and should match your workspace settings. Update `dataset_type` in `config.yaml` if the dataset is actually a panel or longitudinal dataset.

### 📊 Classification Summary
- **Order Details**: 4 fields
- **Shipping Addresses**: 2 fields
- **Customer Demographics**: 2 fields
- **Product Information**: 1 fields

### ⚠️ Orphans in Data Dictionary
> These attributes exist in the dictionary but were **not found** in the raw data file. They have been excluded from the assignments below.

- `customer_unique_id`
- `freq_cust`
- `freq_purch_prod`
- `month`
- `woy`
- `year`

---

### 📋 Detailed Assignments
| Attribute                  | Assignment              | Logical Type   | Physical Type   |
|----------------------------|-------------------------|----------------|-----------------|
| `customer_city`            | `Shipping Addresses`    | `text`         | `str`           |
| `customer_id`              | `Customer Demographics` | `text`         | `str`           |
| `customer_state`           | `Customer Demographics` | `categorical`  | `str`           |
| `customer_zip_code_prefix` | `Shipping Addresses`    | `numeric`      | `int`           |
| `order_id`                 | `Order Details`         | `text`         | `str`           |
| `order_item_id`            | `Order Details`         | `numeric`      | `float`         |
| `order_purchase_timestamp` | `Order Details`         | `datetime`     | `datetime`      |
| `price`                    | `Order Details`         | `numeric`      | `float`         |
| `product_id`               | `Product Information`   | `text`         | `str`           |

---
*Report generated via automated dd-parser post-processing.*