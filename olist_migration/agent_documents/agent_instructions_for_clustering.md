# Agent Instructions for Clustering Model Development

This document defines the development guidelines that an agent should follow when implementing a clustering task with `kmds-modeling`.

## 1. Task Definition
- Confirm the task intent is `CLUSTERING`.
- Ensure the dataset represents an unsupervised grouping problem, not a classification or regression problem.
- Identify the appropriate input matrix and the entity dimensions being clustered (for this project, weekly time windows and product activity columns).

## 2. Workspace and Configuration
- Use a single modeling config file (e.g. `modeling_config.yaml`).
- The config must include a valid `working_dir` and data resolution keys that `kmds_modeling.core.path_coordinator.PathCoordinator` can resolve.
- Ensure the config contains both top-level keys and a `data:` section if the package resolver expects both.
- For clustering tasks, include:
  - `working_dir`
  - `model_ready_data_file`
  - `featurization_output_dir`
  - `modeling_output_dir`
  - `project.task_type: CLUSTERING`
  - algorithm metadata such as `model_family`, `n_clusters`, and `embedding_dim`

## 2.1. Required Modeling Spec Question Answers
When the interface asks the modeling spec questions, provide these answers exactly:
- `project.strategy`: `spectral_clustering`
- `project.target_variable`: `none` (this is an unsupervised task)
- `project.user_intent`: `we want to understand the temporal affinity of products over the year in the SP region for planning and acquisition`
- `candidates`: one candidate named `spectral_clustering` with `class_path: models.spectral_clustering.run_spectral_clustering` and hyperparameters for `n_clusters`, `embedding_dim`, `random_state`, and `use_tfidf`
- `production_target.champion_candidate_name`: `spectral_clustering`
- `production_target.export_directory`: use the `modeling_config.yaml` value, typically `models`

## 3. Input Data Selection
- Use the featurization output as the source of truth.
- For this Olist clustering task, the correct input is `data/SP_2017_freq_prod_weekly_sales_prepared.parquet`.
- Verify the dataset contains the expected index/key column (`woy`) and feature columns representing product activity.
- Confirm the matrix shape aligns with the clustering logic: one row per week, one column per product.

## 4. Clustering Model Implementation
- Build a local clustering module under `models/` rather than implementing it as a notebook-only procedure.
- When possible, implement a reusable task wrapper such as `models/spectral_clustering.py`.
- The implementation should:
  1. Load the model-ready dataset using `kmds_modeling` notebook utils or workspace path resolution utilities.
  2. Construct a normalized affinity matrix appropriate for the clustering method.
  3. Compute a spectral decomposition or other embedding.
  4. Apply a cluster assignment algorithm (e.g., KMeans on the spectral embedding).
  5. Persist cluster labels and embedding artifacts under `models/`.

## 5. Spectral Clustering Guidance
- For bipartite week-product interaction matrices, spectral co-clustering is the preferred solution.
- Normalize the raw week-product matrix using TF-IDF or degree normalization to reduce dominant-product bias.
- Construct the normalized bipartite affinity matrix using:
  `B = D_W^{-1/2} A D_P^{-1/2}`
- Use SVD to compute the joint low-dimensional embedding.
- Stack the scaled left and right singular vectors into a joint embedding matrix `Z`.
- Run KMeans (or another partitioning algorithm) on `Z` to produce both week and product clusters.

## 6. Artifact Outputs
- Save inspection artifacts in the workspace `models/` directory.
- Required artifacts include:
  - `spectral_gap.csv`
  - `week_clusters.csv`
  - `product_clusters.csv`
  - `week_embeddings.csv`
  - `product_embeddings.csv`
  - `cluster_counts.csv`
  - `spectral_clustering_summary.md`
- Advisors or notebooks may also produce a `clustering_advisor_recommendation.json` artifact.

## 7. Advisor Integration
- Use `kmds_modeling.core.model_advisor.ModelAdvisor` to confirm the task intent.
- Profile the dataset with `ModelAdvisor.profile_data(...)`.
- For clustering, request `user_intent='CLUSTERING'` and generate a recommendation.
- Save advisor output and profile information to the workspace under `models/advisor/`.
- Include rationale describing why spectral clustering was chosen for bipartite week-product structure.

## 8. Notebook Support
- Create a notebook that runs the clustering model end-to-end and inspects output artifacts.
- Create a separate advisor notebook that runs the clustering advisor and shows the recommendation.
- The notebooks should use the shared config file and `models/` module, not hardcoded paths.

## 9. Documentation and Rationale
- Document the decision in a local agent doc such as `agent_documents/clustering_task_initialization.md`.
- Reference domain-specific rationale when available (for example, `rationale_for_spectral_clustering.md`).
- Explicitly state that data science experts favor spectral clustering here because it preserves the joint bipartite structure of weeks and products and mitigates high-frequency product dominance.

## 10. Validation and Testing
- Validate that the notebook and module run successfully in the workspace virtual environment.
- Ensure the advisor notebook executes without import or path resolution errors.
- Confirm the artifacts are created under `models/`.
- If any local package imports fail, fix them by verifying the virtual environment and Python path.
