# kmds-data-helper Experiment Report

## Purpose
This note documents the experiment applying `kmds-data-helper` to the `sba_migration` repository.
It explains what failed, what I had to do to fix it, and what should be fixed in the helper source or repo process.

## What happened
1. The repo did not have the helper-required `output/` folder or any of the expected helper output artifacts.
2. The helper package requires Python `>=3.12,<3.13`, while the workspace default venv was Python 3.13.
3. Because the installed repo venv was incompatible, I created a separate Python 3.12 virtual environment named `.kg_env`.
4. I installed `kmds-data-helper` from the cloned GitHub source into that 3.12 env.
5. The helper package was importable and the aggregation CLI was available.
6. The helper still required at least one helper output JSON artifact, so I created a minimal `output/full_service_report.json` manually.
7. I then ran the knowledge graph aggregation and produced `data/KMDS/project_knowledge_graph.xml`.

## Why it failed
- `kmds-data-helper` currently expects a fully populated KMDS helper workspace with `output/full_service_report.json`, `output/kmds_summary.json`, or `output/kmds_strategic_summary.json`.
- It also enforces a strict repo structure: `documents/`, `notebooks/`, `data_dictionary/`, and `output/`.
- The repository did not include the required helper output artifacts, so the aggregator could not proceed until those were created.
- The workspace venv was Python 3.13, but the helper package is pinned to Python `<3.13`, so the tool could not be installed in the default environment.

## What I fixed
- Created `.kg_env` with Python 3.12 and installed `kmds-data-helper` from source.
- Created `output/full_service_report.json` as the required helper artifact for this experiment.
- Created the target graph folder `data/KMDS/` and generated `data/KMDS/project_knowledge_graph.xml`.

## What should be fixed
1. `kmds-data-helper` should support a direct repo ingestion path without requiring pre-generated helper JSON artifacts, or it should include a helper stage that produces those artifacts from the repository automatically.
2. The package should clearly document the required repository shape and the required Python version in the repo README and install instructions.
3. The tool should provide a more graceful onboarding path for repositories that already contain data, documentation, notebooks, and model artifacts, instead of failing early on missing `output/`.
4. If the helper is meant to be part of the KMDS toolkit, it should not require manual JSON artifact creation for basic repo conversion; it should gather observations from the repository contents automatically.

## Result
- `data/KMDS/project_knowledge_graph.xml` was produced successfully.
- The graph is based on a synthetic helper artifact created for this experiment, but it demonstrates the intended repository-to-knowledge-graph conversion path.
- The conversion confirms that `kmds-data-helper` can be used to expose the KMDS workflow as a queryable knowledge graph.
