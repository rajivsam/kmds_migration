# ITSM Resolution Analysis

## Problem statement

The ITSM case study addresses a common operational problem in help-desk management: measuring support-group performance under censoring and incomplete ticket closure. Standard operational metrics such as mean time to resolution are not sufficient for this setting because they are biased when tickets remain open at the end of the observation window. This creates an incomplete picture of service performance and can distort comparisons across support groups with different workload compositions and closure dynamics.

The objective of the study is therefore to estimate time-to-resolution distributions for support groups using a survival-analysis framework that explicitly accounts for incomplete follow-up. The analysis is implemented within the KMDS workflow and uses the ServiceNow incident dataset from the UCI Machine Learning Repository as the source of historical ticket lifecycle information.

## Dataset and scope

The study uses the incident event log as a longitudinal operational dataset with ticket-level lifecycle records, including the ticket identifier, assignment group, creation time, resolution time, closure time, and the final incident state. The data are organized as an event log in which each ticket is treated as a subject and the relevant outcome is the duration from submission to resolution or censoring.

The modeling task is framed as a time-to-event problem in which the primary target is the time required to resolve a ticket by the final assignment group associated with that incident. This choice reflects the operational question of interest: how long do tickets ultimately handled by a given support group remain active before they are resolved or otherwise exit the queue?

The analysis is intentionally restricted to a one-year observation window defined from the latest timestamp in the dataset backward by 365 days. This avoids mixing historical tickets from materially different operating periods and reduces the risk of spurious comparisons driven by temporal drift in incident volume, staffing, or ticket mix.

## Preprocessing choices

The raw incident data are cleaned and standardized through the KMDS preprocessing pipeline before survival modeling. The workflow removes incomplete or non-human assignment categories represented by a placeholder value (`"?"`), keeps only tickets with a valid assignment group, and defines the study window on a rolling one-year basis.

Each ticket is reduced to a single subject-level record using the latest available assignment group and final state for that ticket. The cleaned dataset retains the relevant lifecycle timestamps and records the ticket's opening time, final state, and event indicator. This produces a consistent and auditable representation of the ticket lifecycle suitable for survival analysis.

The event indicator is defined as follows: a ticket is coded as an event ($E = 1$) when its final state is closed or resolved; otherwise it is treated as censored ($E = 0$), with the censoring time defined as the end of the observation window minus the ticket open time. This choice is important because it ensures that unresolved tickets remain in the risk set without being treated as artificially resolved.

## Feature engineering and representation choices

The implementation does not rely on a complex predictive feature set. Instead, it preserves a compact operational representation that is aligned with the service-management problem. The key subject-level attributes are the ticket identifier, assignment group, incident state, ticket open time, ticket close time, event indicator, and the derived duration variable.

The model-ready representation is therefore a survival table in which each row corresponds to one ticket and the analysis uses the support group as the grouping variable. This representation is intentionally simple and transparent: the feature of interest is not an engineered ML feature set but a directly interpretable operational attribute, namely the support group responsible for resolution.

The implementation also creates a support-group eligibility filter based on the observed ticket volume and censoring pattern. A group is retained only if it has at least 20 closed tickets within the study window and if the proportion of open tickets is less than or equal to 70% of the group total. This thresholding step is designed to ensure that the Kaplan-Meier curves are estimated from groups with sufficient event information and a tractable censoring profile.

## Modeling choices and why they were selected

The primary modeling method is the Kaplan-Meier estimator, selected because the study target is a non-parametric survival distribution for ticket resolution time. This approach is appropriate for operational service data because it does not assume a parametric form for the underlying survival distribution, while still yielding interpretable estimates of the survival function over time.

Kaplan-Meier analysis is particularly well suited to the ITSM use case because support groups operate under heterogeneous event patterns, and the censoring mechanism is not random from a business perspective but arises from open incidents that remain active at the study cutoff. A non-parametric survival estimator provides a direct way to compare time-to-resolution across groups while preserving the incomplete follow-up information that would otherwise be lost in simpler mean-based metrics.

In the implementation, each support group is modeled as a separate stratum, and a survival curve is estimated over the ticket duration scale. The resulting curves provide a direct comparison of how quickly tickets from each support group progress from open to resolved status. This operational framing is consistent with the service-level objective of benchmarking support performance under realistic conditions rather than under the idealized assumptions of fully observed closure times.

## Evaluation criteria

The evaluation is designed around survival-curve interpretation rather than single-point summary metrics. The main criteria are the estimated survival function, the number of observed resolution events, and the censoring profile of each group. This is important because ticket resolution is a time-to-event process with incomplete observation, so model quality is assessed by whether the estimated survival curves are stable, interpretable, and operationally meaningful.

The implementation emphasizes the support group screening rules before model fitting: groups are excluded if they do not reach the minimum event threshold or if they are dominated by open tickets. This ensures that the comparison is conducted on groups with enough resolved cases to support a reliable estimate. In practice, the final Kaplan-Meier comparison is therefore grounded in a dataset that balances statistical stability with realistic operational coverage.

## Key outputs

The ITSM implementation produces a set of artifacts that make the workflow reproducible and auditable:

- Cleaned ticket dataset and lifecycle metadata in the KMDS data and documentation folders.
- Survival-ready dataset for time-to-resolution modeling.
- Kaplan-Meier model summary exported to `models/itsm_ticket_survival_km_summary.csv`.
- Kaplan-Meier plots stored in `models/itsm_ticket_survival_km.png`.
- Pipeline and model documentation in the project notebooks and configuration files.

The exported model summary reports, by support group, the number of observed events, the minimum and maximum observed durations, and the count of tickets retained in the estimation set. These outputs support quantitative comparison of service performance across groups and provide the analytical basis for operational interpretation.

## Interpretation for stakeholders

The ITSM application demonstrates the practical value of KMDS for operational analytics. Rather than summarizing performance with a single average resolution metric, the framework preserves the time-to-event structure of ticket resolution and makes censoring explicit. This allows service managers to understand not only whether a group resolves tickets quickly, but also how resilient that performance is under realistic workload conditions and incomplete closure histories.

From a stakeholder perspective, the Kaplan-Meier curves provide a transparent way to benchmark support groups against one another. They support operational discussions about workload management, queue dynamics, and service-level expectations without over-claiming the precision of a purely deterministic metric. The system therefore functions as a decision-support tool for service operations rather than as an autonomous replacement for operational judgment.

## Design decisions that were revisited or changed

A central design choice in this implementation was to define the ticket outcome at the final assignment-group level. This makes the analysis operationally interpretable because the unit of analysis reflects the group ultimately responsible for service completion. The approach also reduces ambiguity when tickets are reassigned during their lifecycle, which is common in incident management systems.

Another important decision was the use of a strict minimum event threshold and censoring guard. This was not a cosmetic choice: it ensures that the Kaplan-Meier comparison is based on groups with a sufficiently stable number of resolved cases and a manageable level of active backlog. The workflow therefore prioritizes reliable comparison over maximizing the number of groups included at the cost of statistical instability.

The implementation also treats the end of the one-year window as a censoring boundary rather than as a reason to discard active tickets. This preserves the integrity of the survival analysis by retaining unresolved tickets in the risk set and providing a valid estimate of the distribution of time to resolution under partial observation.

## Links to notebooks / scripts / outputs

- Data-preparation notebook: `notebooks/create_itsm_survival_pipeline.ipynb`
- Modeling notebook: `notebooks/create_itsm_survival_kaplan_meier_model.ipynb`
- Supporting data-preparation notes: `agent_docs/data_prep_doc.md`
- Featurization script: `featurization_scripts/featurization.py`
- Configuration: `config.yaml`
- Featurizer configuration: `featurizer_config.yaml`
- Model summary: `models/itsm_ticket_survival_km_summary.csv`
- Plot: `models/itsm_ticket_survival_km.png`
- Survival-ready data: `data/featurization/itsm_survival_model_ready_numeric_data.csv`

## Summary

The ITSM case study shows how a KMDS workflow can support a scientifically defensible time-to-resolution analysis for help-desk operations. By combining a disciplined data-preparation pipeline, explicit censoring rules, and a non-parametric survival model, the implementation produces group-level service-time estimates that are both operationally relevant and statistically appropriate for incomplete ticket outcomes. The resulting analysis supports the manuscript narrative by demonstrating that KMDS can preserve methodological rigor, operational context, and reproducibility in an applied service-management setting.
