# 📑 Data Dictionary: Provisional Entity Assignment Report
**Generation Timestamp:** `2026-07-02 10:08:43`
**Source Blueprint:** `customer_data_dictionary.csv`

### 🏗️ Structural Assessment
- **Dataset Type:** `cross-sectional`
> ⚠️ **Note:** This dataset type is provided by configuration and should match your workspace settings. Update `cleaner.structural_assessment.dataset_type` in `config.yaml` if the dataset is actually a panel or longitudinal dataset.

### 📊 Classification Summary
- **CustomerLocation**: 3 fields
- **CustomerDemographics**: 1 fields

### ⚠️ Orphans in Data Dictionary
> These attributes exist in the dictionary but were **not found** in the raw data file. They have been excluded from the assignments below.

- `customer_unique_id`

### 👻 Orphans in Data (Ghosts)
> These headers exist in the raw data file but have **no corresponding entry** in the data dictionary.

- `order_id`
- `order_purchase_timestamp`
- `order_item_id`
- `product_id`
- `price`

---

### 📋 Detailed Assignments
| Attribute                  | Assignment             | Logical Type   | Physical Type   | Flag: Geographic   |
|----------------------------|------------------------|----------------|-----------------|--------------------|
| `customer_id`              | `CustomerDemographics` | `text`         | `str`           | `False`            |
| `customer_zip_code_prefix` | `CustomerLocation`     | `numeric`      | `int`           | `True`             |
| `customer_city`            | `CustomerLocation`     | `text`         | `str`           | `True`             |
| `customer_state`           | `CustomerLocation`     | `categorical`  | `str`           | `True`             |

---
*Report generated via automated dd-parser post-processing.*