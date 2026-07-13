## 1. Problem Statement and Study Goal

* Problem Statement: Standard IT metrics like Mean Time to Resolution (MTTR) introduce severe statistical bias because they cannot account for open tickets, which artificially skews the operational picture of help desk efficiency.
* Study Goal: This study applies non-parametric survival analysis via Kaplan-Meier curves to accurately measure and benchmark the time-to-resolution operational effectiveness of high-volume, established support groups.
* Dataset Description: The analysis utilizes the IT Service Management (ITSM) dataset from the UCI Machine Learning Repository, which tracks historical incident lifecycles under the ITIL framework.
* Dataset Source: The data is sourced from a large IT service provider's ServiceNow logging platform, capturing multi-row state updates, assignments, and timestamps for tracking ticket lifecycles.

## 2. Rationale and Criteria for Selecting Support Groups

* Target Variable Choice: The analysis uses the last registered support group and its final state timestamp for each unique ticket.
* Operational Rationale: Attributing the ticket to the final assignment group directly evaluates that group's capacity to successfully resolve and exit the incident from the active queue.
* Analytical Choice: This choice measures the *total elapsed duration* from a ticket's opening time until closure by that final group, answering how long tickets ultimately landing in that domain take to resolve.
* Placeholder Removal: All unassigned or incomplete tracking categories labeled as `"?"` are discarded from the study because they do not represent active human support teams.
* Volume Threshold Filter: A strict inclusion rule is applied requiring a group to have at least 20 closed tickets within the observation period.
* Volume Threshold Rationale: This minimum closure baseline controls statistical variance and ensures the Kaplan-Meier curve has sufficient events to calculate stable survival probabilities.
* Censoring Guard Filter: A maximum censoring boundary is enforced where the proportion of open tickets to total tickets must be less than or equal to 70% ($\frac{\text{Open}}{\text{Total}} \le 0.70$).
* Censoring Guard Rationale: This rule guarantees that the survival curve drops far enough below the $0.50$ Y-axis mark, enabling the estimator to calculate a valid, unambiguous Median Survival Time for benchmarking.

## 3. Attribute Filters and Data Processing Algorithm Sketch

* Temporal Window Filter: The observation boundaries are defined by finding the absolute maximum timestamp in the data ($T_{end}$) and calculating exactly one year backward ($T_{start} = T_{end} - 365\text{ days}$).
* Subject Entry Filter: Only tickets with an `opened_at` timestamp strictly falling between $T_{start}$ and $T_{end}$ are included to prevent left-truncation and immortal time bias.
* Step 1 (Boundary Setting): Identify the absolute maximum dataset timestamp ($T_{end}$) and subtract 365 days to establish the strict rolling 1-year study window ($T_{start}$).
* Step 2 (Data Cleaning): Drop all rows containing unassigned `"?"` values within the `assignment_group` attribute.
* Step 3 (Window Isolation): Filter the rows to isolate only those incidents whose original opening timestamp falls within the $[T_{start}, T_{end}]$ window.
* Step 4 (Event Mapping): Map the event indicator ($E$) per ticket based on its final operational state at $T_{end}$, assigning $E = 1$ for Closed/Resolved states and $E = 0$ (censored) for all active states (e.g., New, Active, On Hold).
* Step 5 (Duration Calculation): Dynamically compute the duration ($T$) for the subject row. If $E = 1$, $T = \text{Closed Time} - \text{Opening Time}$. If $E = 0$, $T = T_{end} - \text{Opening Time}$.
