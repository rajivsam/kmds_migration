## Project Initiation Document: SBA Loan Early Warning System (EWS)## 
1. Problem Definition
The Small Business Administration (SBA) loan portfolio requires proactive risk management to protect capital and optimize intervention strategies.
This project implements an Early Warning System (EWS) using a supervised binary classification framework. The system processes raw data through the dd_parser_cleaner_migration pipeline to transform historical loan lifecycle records into a predictive modeling asset.
The goal is to calculate a Probability of Default (PD) or "stress score" for loans currently on the books, allowing operations teams to prioritize risk-mitigation efforts before a final default occurs.
------------------------------
## 2. Risk-Averse Perspective & Loan Pool Selection Rationale
To establish a highly conservative baseline, this project adopts a strict, risk-averse stance on credit quality:

* Stringent Default Definition: "Bad" is defined as any loan that has missed a single payment (excluding specific SBA-sanctioned exemptions).
* High Signal Purity: By classifying even a single missed payment as "Bad," the "Good" bucket is reserved exclusively for flawless, pristine borrowers. This creates an uncompromisingly clear mathematical separation between the two classes.
* Operational Alignment: From a risk-management perspective, false positives (investigating a borrower who eventually pays) are significantly less expensive than false negatives (missing a borrower who defaults entirely). This strict framing optimizes for high sensitivity to early distress indicators.

------------------------------
## 3. Modeling Strategy & Dataset Composition## Data Split Strategy

* Training Pool: Composed strictly of historical, closed records categorized as either Good or Bad.
* Scoring Pool: Composed strictly of Active loans currently on the books. This pool is completely isolated from training and is used exclusively for final inference.

                  ┌──────────────────────────────┐
                  │      df_final (Migrated)     │
                  └──────────────┬───────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
  ┌──────────────▼──────────────┐ ┌──────────────▼──────────────┐
  │   Training Pool (Historical)│ │     Scoring Pool (Current)  │
  │   Condition: [Good, Bad]    │ │   Condition: [Active Only]  │
  └──────────────┬──────────────┘ └──────────────┬──────────────┘
                 │                               │
        [Train/Test Split]                       │
                 │                               │
        ┌────────▼────────┐                      │
        │ ML Classifier   │                      │
        │  (Fit/Predict)  │                      │
        └────────┬────────┘                      │
                 │                               │
                 │ (Scoring Phase)               │
                 └───────────────────────────────► [Generate Risk Scores]

## Dataset Composition Matrix

| Dataset Pool | Target Label | loancondition Status | Operational Definition | Role in Pipeline |
|---|---|---|---|---|
| Training (Class 0) | 0 (Good) | Paid in Full | Loans closed with a flawless repayment history. | Model optimization and feature learning. |
| Training (Class 1) | 1 (Bad) | Delinquent / Distressed | Loans with ≥ 1 missed payment (excluding SBA exemptions). | Model optimization and feature learning. |
| Scoring | Unlabeled | Active | Open loans currently on the books. | Target population for prediction and operational flagging. |

------------------------------
## 4. Key Pipeline Controls & Guardrails
To ensure research integrity and avoid data leakage, the following controls from apply_migration must be maintained during implementation:

   1. Chronological Sanitization: Records where firstdisbursementdate > paidinfulldate are purged to eliminate data anomalies.
   2. Temporal Feature Engineering: Feature engineering for loan age and seasoning (e.g., loan_age_months = current_date - firstdisbursementdate) must be executed before date attributes are dropped in Step 4.
   3. Active Pool Scrubbing: Any active loan that has already missed a payment at the time of data extraction must be dynamically re-routed to the training pool's "Bad" class, ensuring the scoring pool consists only of active loans that are completely current.

------------------------------
Our conceptual framework is fully locked in and validated. When you are ready to begin the implementation phase, let me know if you would like to start by writing the script to calculate the exact class imbalance in the training pool or if you want to set up the train-scoring partition logic in Python.

