# 🤖 Cleaning Assistant Report

This report provides automated recommendations based on data profile physics and semantic metadata.

## 🛡️ User Responsibilities
- **Domain Logic**: User should capture domain-specific row filters in `config.yaml` or via an optional external custom logic module referenced explicitly in configuration.
- **Domain Deletions**: User must identify columns requiring deletion based on business rules.
- **Strategy Validation**: While we suggest mean/MISSING defaults, the user determines the final strategy.

## 📊 Summary of Actions
- **constant:MISSING**: 6 columns
- **drop-attribute**: 5 columns
- **mean-imputation**: 3 columns
- **custom:datetime_to_numeric**: 3 columns

## Deletion is recommended for the following attributes

| Attribute      | Type        | Entity             | What Needs Fixing                                         | Recommended Fix   |
|:---------------|:------------|:-------------------|:----------------------------------------------------------|:------------------|
| AsOfDate       | datetime    | Logical Category   | Constant value / Zero variance                            | drop-attribute    |
| Program        | datetime    | Logical Categories | Constant value / Zero variance                            | drop-attribute    |
| BankNCUANumber | numeric     | Logical Categories | Extreme sparsity (97.1%): Exceeds null threshold of 95.0% | drop-attribute    |
| ChargeOffDate  | datetime    | Logical Categories | Extreme sparsity (98.2%): Exceeds null threshold of 95.0% | drop-attribute    |
| SoldSecMrktInd | categorical | Logical Categories | Constant value / Zero variance                            | drop-attribute    |

## Derived attribute definition or deletion is recommended

| Attribute             | Type     | Entity             | What Needs Fixing                                                                                                                                    | Recommended Fix            |
|:----------------------|:---------|:-------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------|:---------------------------|
| ApprovalDate          | datetime | Logical Categories | This is a cross sectional dataset; if you want to use the datetime attributes, you need to derive numeric attributes from them and then delete them. | custom:datetime_to_numeric |
| FirstDisbursementDate | datetime | Logical Categories | This is a cross sectional dataset; if you want to use the datetime attributes, you need to derive numeric attributes from them and then delete them. | custom:datetime_to_numeric |
| PaidInFullDate        | datetime | Logical Category   | This is a cross sectional dataset; if you want to use the datetime attributes, you need to derive numeric attributes from them and then delete them. | custom:datetime_to_numeric |

## Missing value definition is recommended for the following attributes

### Numeric Attributes (Standard: Mean Imputation)

| Attribute             | Type    | Entity             | What Needs Fixing                                            | Recommended Fix   |
|:----------------------|:--------|:-------------------|:-------------------------------------------------------------|:------------------|
| BankFDICNumber        | numeric | Logical Categories | Numeric with 10.6% nulls: Recommendation is mean imputation. | mean-imputation   |
| InitialInterestRate   | numeric | Logical Categories | Numeric with 0.0% nulls: Recommendation is mean imputation.  | mean-imputation   |
| CongressionalDistrict | numeric | Logical Categories | Numeric with 0.0% nulls: Recommendation is mean imputation.  | mean-imputation   |

### Categorical Attributes (Standard: 'MISSING' Category)

| Attribute                  | Type        | Entity             | What Needs Fixing                                                                   | Recommended Fix   |
|:---------------------------|:------------|:-------------------|:------------------------------------------------------------------------------------|:------------------|
| BorrName                   | text        | Person             | Categorical/Text with 0.0% nulls: Recommendation is creating a 'MISSING' category.  | constant:MISSING  |
| FixedorVariableInterestInd | categorical | Logical Categories | Categorical/Text with 0.0% nulls: Recommendation is creating a 'MISSING' category.  | constant:MISSING  |
| FranchiseCode              | categorical | Logical Category   | Categorical/Text with 88.0% nulls: Recommendation is creating a 'MISSING' category. | constant:MISSING  |
| FranchiseName              | categorical | Conceptual Entity  | Categorical/Text with 88.0% nulls: Recommendation is creating a 'MISSING' category. | constant:MISSING  |
| BusinessType               | categorical | Logical Categories | Categorical/Text with 0.0% nulls: Recommendation is creating a 'MISSING' category.  | constant:MISSING  |
| BusinessAge                | categorical | Logical Categories | Categorical/Text with 0.0% nulls: Recommendation is creating a 'MISSING' category.  | constant:MISSING  |


---
*Generated by CleaningAssistant engine.*