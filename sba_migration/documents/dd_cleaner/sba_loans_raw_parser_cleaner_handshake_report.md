# 📑 Data Dictionary: Provisional Entity Assignment Report
**Generation Timestamp:** `2026-11-17 12:18:22`
**Source Blueprint:** `sba_dd.csv`

### 🏗️ Structural Assessment
- **Dataset Type:** `cross-sectional`
> ⚠️ **Note:** This dataset type is provided by configuration and should match your workspace settings. Update `dataset_type` in `config.yaml` if the dataset is actually a panel or longitudinal dataset.

### 📊 Classification Summary
- **Logical Categories**: 24 fields
- **Logical Category**: 9 fields
- **Conceptual Entity**: 3 fields
- **Location**: 2 fields
- **Person**: 1 fields
- **Geographical**: 1 fields
- **Logical Category: Address**: 1 fields
- **Geographical Entity**: 1 fields

### ⚠️ Orphans in Data Dictionary
> These attributes exist in the dictionary but were **not found** in the raw data file. They have been excluded from the assignments below.

- `loan_age_months`
- `estimated_balance`

---

### 📋 Detailed Assignments
| Attribute                    | Assignment                  | Logical Type   | Physical Type   | Flag: Geographical   |
|------------------------------|-----------------------------|----------------|-----------------|----------------------|
| `AsOfDate`                   | `Logical Category`          | `datetime`     | `datetime`      | `False`              |
| `Program`                    | `Logical Categories`        | `datetime`     | `datetime`      | `False`              |
| `LocationID`                 | `Logical Category`          | `numeric`      | `int`           | `False`              |
| `BorrName`                   | `Person`                    | `text`         | `str`           | `False`              |
| `BorrStreet`                 | `Logical Categories`        | `text`         | `str`           | `False`              |
| `BorrCity`                   | `Location`                  | `text`         | `str`           | `True`               |
| `BorrState`                  | `Logical Category`          | `categorical`  | `str`           | `False`              |
| `BorrZip`                    | `Geographical`              | `numeric`      | `int`           | `False`              |
| `BankName`                   | `Logical Category`          | `categorical`  | `str`           | `False`              |
| `BankFDICNumber`             | `Logical Categories`        | `numeric`      | `float`         | `False`              |
| `BankNCUANumber`             | `Logical Categories`        | `numeric`      | `float`         | `False`              |
| `BankStreet`                 | `Logical Category: Address` | `categorical`  | `str`           | `False`              |
| `BankCity`                   | `Location`                  | `categorical`  | `str`           | `True`               |
| `BankState`                  | `Logical Category`          | `categorical`  | `str`           | `False`              |
| `BankZip`                    | `Geographical Entity`       | `numeric`      | `int`           | `True`               |
| `GrossApproval`              | `Logical Categories`        | `numeric`      | `float`         | `False`              |
| `SBAGuaranteedApproval`      | `Logical Categories`        | `numeric`      | `float`         | `False`              |
| `ApprovalDate`               | `Logical Categories`        | `datetime`     | `datetime`      | `False`              |
| `ApprovalFY`                 | `Logical Category`          | `numeric`      | `int`           | `False`              |
| `FirstDisbursementDate`      | `Logical Categories`        | `datetime`     | `datetime`      | `False`              |
| `ProcessingMethod`           | `Logical Categories`        | `categorical`  | `str`           | `False`              |
| `InitialInterestRate`        | `Logical Categories`        | `numeric`      | `float`         | `False`              |
| `FixedorVariableInterestInd` | `Logical Categories`        | `categorical`  | `str`           | `False`              |
| `TermInMonths`               | `Logical Categories`        | `numeric`      | `float`         | `False`              |
| `NaicsCode`                  | `Logical Categories`        | `numeric`      | `int`           | `False`              |
| `NaicsDescription`           | `Logical Categories`        | `text`         | `str`           | `False`              |
| `FranchiseCode`              | `Logical Category`          | `categorical`  | `str`           | `False`              |
| `FranchiseName`              | `Conceptual Entity`         | `categorical`  | `str`           | `False`              |
| `ProjectCounty`              | `Conceptual Entity`         | `text`         | `str`           | `False`              |
| `ProjectState`               | `Logical Category`          | `categorical`  | `str`           | `False`              |
| `SBADistrictOffice`          | `Conceptual Entity`         | `categorical`  | `str`           | `False`              |
| `CongressionalDistrict`      | `Logical Categories`        | `numeric`      | `int`           | `False`              |
| `BusinessType`               | `Logical Categories`        | `categorical`  | `str`           | `False`              |
| `BusinessAge`                | `Logical Categories`        | `categorical`  | `str`           | `False`              |
| `LoanStatus`                 | `Logical Categories`        | `categorical`  | `str`           | `False`              |
| `PaidInFullDate`             | `Logical Category`          | `datetime`     | `datetime`      | `False`              |
| `ChargeOffDate`              | `Logical Categories`        | `datetime`     | `datetime`      | `False`              |
| `GrossChargeOffAmount`       | `Logical Categories`        | `numeric`      | `float`         | `False`              |
| `RevolverStatus`             | `Logical Categories`        | `categorical`  | `str`           | `False`              |
| `JobsSupported`              | `Logical Categories`        | `numeric`      | `float`         | `False`              |
| `CollateralInd`              | `Logical Categories`        | `categorical`  | `str`           | `False`              |
| `SoldSecMrktInd`             | `Logical Categories`        | `categorical`  | `str`           | `False`              |

---
*Report generated via automated dd-parser post-processing.*