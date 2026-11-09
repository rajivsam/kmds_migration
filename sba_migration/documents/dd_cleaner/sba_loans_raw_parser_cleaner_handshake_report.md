# 📑 Data Dictionary: Provisional Entity Assignment Report
**Generation Timestamp:** `2026-11-08 08:56:54`
**Source Blueprint:** `sba_dd.csv`

### 🏗️ Structural Assessment
- **Dataset Type:** `cross-sectional`
> ⚠️ **Note:** This dataset type is provided by configuration and should match your workspace settings. Update `dataset_type` in `config.yaml` if the dataset is actually a panel or longitudinal dataset.

### 📊 Classification Summary
- **Logical Category**: 23 fields
- **Logical Categories**: 8 fields
- **Conceptual Entity**: 7 fields
- **Person**: 2 fields
- **Geographical**: 2 fields
- **Organization**: 1 fields
- **Location**: 1 fields

---

### 📋 Detailed Assignments
| Attribute                    | Assignment           | Logical Type   | Physical Type   | Flag: Geographical   |
|------------------------------|----------------------|----------------|-----------------|----------------------|
| `AsOfDate`                   | `Logical Category`   | `unknown`      | `unknown`       | `False`              |
| `Program`                    | `Logical Categories` | `unknown`      | `unknown`       | `False`              |
| `LocationID`                 | `Conceptual Entity`  | `unknown`      | `unknown`       | `False`              |
| `BorrName`                   | `Person`             | `unknown`      | `unknown`       | `False`              |
| `BorrStreet`                 | `Logical Category`   | `unknown`      | `unknown`       | `False`              |
| `BorrCity`                   | `Logical Category`   | `unknown`      | `unknown`       | `False`              |
| `BorrState`                  | `Logical Category`   | `unknown`      | `unknown`       | `False`              |
| `BorrZip`                    | `Geographical`       | `unknown`      | `unknown`       | `False`              |
| `BankName`                   | `Logical Category`   | `unknown`      | `unknown`       | `False`              |
| `BankFDICNumber`             | `Organization`       | `unknown`      | `unknown`       | `False`              |
| `BankNCUANumber`             | `Logical Category`   | `unknown`      | `unknown`       | `False`              |
| `BankStreet`                 | `Location`           | `unknown`      | `unknown`       | `False`              |
| `BankCity`                   | `Conceptual Entity`  | `unknown`      | `unknown`       | `False`              |
| `BankState`                  | `Conceptual Entity`  | `unknown`      | `unknown`       | `False`              |
| `BankZip`                    | `Geographical`       | `unknown`      | `unknown`       | `False`              |
| `GrossApproval`              | `Logical Category`   | `unknown`      | `unknown`       | `False`              |
| `SBAGuaranteedApproval`      | `Logical Category`   | `unknown`      | `unknown`       | `False`              |
| `ApprovalDate`               | `Logical Category`   | `unknown`      | `unknown`       | `False`              |
| `ApprovalFY`                 | `Logical Category`   | `unknown`      | `unknown`       | `False`              |
| `FirstDisbursementDate`      | `Person`             | `unknown`      | `unknown`       | `False`              |
| `ProcessingMethod`           | `Logical Categories` | `unknown`      | `unknown`       | `False`              |
| `InitialInterestRate`        | `Logical Category`   | `unknown`      | `unknown`       | `False`              |
| `FixedorVariableInterestInd` | `Logical Category`   | `unknown`      | `unknown`       | `False`              |
| `TermInMonths`               | `Conceptual Entity`  | `unknown`      | `unknown`       | `False`              |
| `NaicsCode`                  | `Logical Categories` | `unknown`      | `unknown`       | `False`              |
| `NaicsDescription`           | `Logical Categories` | `unknown`      | `unknown`       | `False`              |
| `FranchiseCode`              | `Logical Category`   | `unknown`      | `unknown`       | `False`              |
| `FranchiseName`              | `Conceptual Entity`  | `unknown`      | `unknown`       | `False`              |
| `ProjectCounty`              | `Logical Category`   | `unknown`      | `unknown`       | `False`              |
| `ProjectState`               | `Logical Category`   | `unknown`      | `unknown`       | `False`              |
| `SBADistrictOffice`          | `Logical Category`   | `unknown`      | `unknown`       | `False`              |
| `CongressionalDistrict`      | `Logical Category`   | `unknown`      | `unknown`       | `False`              |
| `BusinessType`               | `Logical Category`   | `unknown`      | `unknown`       | `False`              |
| `BusinessAge`                | `Logical Categories` | `unknown`      | `unknown`       | `False`              |
| `LoanStatus`                 | `Logical Categories` | `unknown`      | `unknown`       | `False`              |
| `PaidInFullDate`             | `Conceptual Entity`  | `unknown`      | `unknown`       | `False`              |
| `ChargeOffDate`              | `Logical Category`   | `unknown`      | `unknown`       | `False`              |
| `GrossChargeOffAmount`       | `Logical Category`   | `unknown`      | `unknown`       | `False`              |
| `RevolverStatus`             | `Logical Categories` | `unknown`      | `unknown`       | `False`              |
| `JobsSupported`              | `Conceptual Entity`  | `unknown`      | `unknown`       | `False`              |
| `CollateralInd`              | `Logical Category`   | `unknown`      | `unknown`       | `False`              |
| `SoldSecMrktInd`             | `Logical Category`   | `unknown`      | `unknown`       | `False`              |

---
*Report generated via automated dd-parser post-processing.*