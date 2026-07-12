# Kaplan-Meier Survival Curve Prompt

1. Use the get_package_info() of the kmds-featurization package to get the featurization interfaces. Use the get_package_info() and the get_spec_questions() (check the name here, could be a variation of this) of th kmds-modeling package to get the modeling interfaces.
2. Use the notebook utils of the featurization package to load the survival dataset for modeling.
3. This will be kaplan-mier survival model, set the regression methods and answer the model spec questions by inspection of the config.yaml and dataset questions available as part of this workspace.
4. For illustrative purposes, pick the groups with the slowest resolutio time (median), the top 3 and plot the survival curves for these groups.
5. This example is provided to show that KMDS is applicable acrosss a range of datasets, that is the primary purpose here.
