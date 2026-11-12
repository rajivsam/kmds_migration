# 📑 Data Dictionary: Provisional Entity Assignment Report
**Generation Timestamp:** `2026-11-12 05:17:42`
**Source Blueprint:** `california_housing_data_dictionary.csv`

### 🏗️ Structural Assessment
- **Dataset Type:** `cross-sectional`
> ⚠️ **Note:** This dataset type is provided by configuration and should match your workspace settings. Update `dataset_type` in `config.yaml` if the dataset is actually a panel or longitudinal dataset.

### 📊 Classification Summary
- **Household Characteristics**: 5 fields
- **Geographic Information**: 2 fields
- **Population Metrics**: 1 fields
- **Property Values**: 1 fields

---

### 📋 Detailed Assignments
| Attribute     | Assignment                  | Logical Type   | Physical Type   |
|---------------|-----------------------------|----------------|-----------------|
| `MedInc`      | `Household Characteristics` | `numeric`      | `float`         |
| `HouseAge`    | `Household Characteristics` | `numeric`      | `float`         |
| `AveRooms`    | `Household Characteristics` | `numeric`      | `float`         |
| `AveBedrms`   | `Household Characteristics` | `numeric`      | `float`         |
| `Population`  | `Population Metrics`        | `numeric`      | `float`         |
| `AveOccup`    | `Household Characteristics` | `numeric`      | `float`         |
| `Latitude`    | `Geographic Information`    | `numeric`      | `float`         |
| `Longitude`   | `Geographic Information`    | `numeric`      | `float`         |
| `MedHouseVal` | `Property Values`           | `numeric`      | `float`         |

---
*Report generated via automated dd-parser post-processing.*