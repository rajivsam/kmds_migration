# 📑 Data Dictionary: Provisional Entity Assignment Report
**Generation Timestamp:** `2026-07-05 08:25:30`
**Source Blueprint:** `sba_dd.csv`

### 🏗️ Structural Assessment
- **Dataset Type:** `cross-sectional`
> ⚠️ **Note:** This dataset type is provided by configuration and should match your workspace settings. Update `dataset_type` in `config.yaml` if the dataset is actually a panel or longitudinal dataset.

### 📊 Classification Summary
- **Logical Categories**: 16 fields
- **Logical Category**: 6 fields
- **Conceptual Entity**: 3 fields
- **Organization**: 1 fields
- **Location**: 1 fields
- **Geographical**: 1 fields
- **Person**: 1 fields
- **Attribute**: 1 fields
- **Geographical Entity**: 1 fields

### ⚠️ Orphans in Data Dictionary
> These attributes exist in the dictionary but were **not found** in the raw data file. They have been excluded from the assignments below.

- `BankName`
- `BankFDICNumber`
- `BankNCUANumber`
- `BankStreet`
- `BankCity`
- `BankState`
- `BankZip`
- `SBAGuaranteedApproval`
- `InitialInterestRate`
- `FixedorVariableInterestInd`
- `RevolverStatus`
- `SoldSecMrktInd`

### 👻 Orphans in Data (Ghosts)
> These headers exist in the raw data file but have **no corresponding entry** in the data dictionary.

- `cdc_name`
- `cdc_street`
- `cdc_city`
- `cdc_state`
- `cdc_zip`
- `thirdpartylender_name`
- `thirdpartylender_city`
- `thirdpartylender_state`
- `thirdpartydollars`

---

### 📋 Detailed Assignments
| Attribute               | Assignment            | Logical Type   | Physical Type   | Flag: Geographical   |
|-------------------------|-----------------------|----------------|-----------------|----------------------|
| `asofdate`              | `Logical Category`    | `datetime`     | `datetime`      | `False`              |
| `program`               | `Logical Categories`  | `numeric`      | `int`           | `False`              |
| `locationid`            | `Logical Category`    | `numeric`      | `int`           | `False`              |
| `borrname`              | `Organization`        | `text`         | `str`           | `False`              |
| `borrstreet`            | `Logical Categories`  | `text`         | `str`           | `False`              |
| `borrcity`              | `Location`            | `text`         | `str`           | `True`               |
| `borrstate`             | `Logical Category`    | `categorical`  | `str`           | `False`              |
| `borrzip`               | `Geographical`        | `numeric`      | `int`           | `False`              |
| `grossapproval`         | `Logical Categories`  | `numeric`      | `int`           | `False`              |
| `approvaldate`          | `Logical Categories`  | `datetime`     | `datetime`      | `False`              |
| `approvalfy`            | `Logical Category`    | `numeric`      | `int`           | `False`              |
| `firstdisbursementdate` | `Person`              | `datetime`     | `datetime`      | `False`              |
| `processingmethod`      | `Logical Categories`  | `categorical`  | `str`           | `False`              |
| `subprogram`            | `Logical Categories`  | `categorical`  | `str`           | `False`              |
| `terminmonths`          | `Logical Categories`  | `numeric`      | `int`           | `False`              |
| `naicscode`             | `Logical Categories`  | `numeric`      | `int`           | `False`              |
| `naicsdescription`      | `Logical Categories`  | `text`         | `str`           | `False`              |
| `franchisecode`         | `Logical Categories`  | `numeric`      | `float`         | `False`              |
| `franchisename`         | `Conceptual Entity`   | `categorical`  | `str`           | `False`              |
| `projectcounty`         | `Conceptual Entity`   | `text`         | `str`           | `False`              |
| `projectstate`          | `Attribute`           | `categorical`  | `str`           | `False`              |
| `sbadistrictoffice`     | `Conceptual Entity`   | `categorical`  | `str`           | `False`              |
| `congressionaldistrict` | `Geographical Entity` | `numeric`      | `int`           | `False`              |
| `businesstype`          | `Logical Categories`  | `categorical`  | `str`           | `False`              |
| `businessage`           | `Logical Categories`  | `categorical`  | `str`           | `False`              |
| `loanstatus`            | `Logical Categories`  | `categorical`  | `str`           | `False`              |
| `paidinfulldate`        | `Logical Category`    | `datetime`     | `datetime`      | `False`              |
| `chargeoffdate`         | `Logical Category`    | `datetime`     | `datetime`      | `False`              |
| `grosschargeoffamount`  | `Logical Categories`  | `numeric`      | `float`         | `False`              |
| `jobssupported`         | `Logical Categories`  | `numeric`      | `int`           | `False`              |
| `collateralind`         | `Logical Categories`  | `numeric`      | `float`         | `False`              |

---
*Report generated via automated dd-parser post-processing.*