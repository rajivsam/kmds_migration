# Attribute Assignment Issue

## Summary
When running `classify-entities` with `config.yaml`, the package asks the LLM to return a `static_dynamic` classification for each attribute. This causes a numeric attribute such as `number` to be assigned `dynamic` by the LLM, even though the package heuristic would classify it as `static`.

When running `classify-entities` with `itsm_config.yaml`, the prompt does not request `static_dynamic`. As a result, the package falls back to its internal inference logic, which correctly assigns `number` as `static`.

## Reproduction
1. Run `classify-entities --config config.yaml`.
2. Observe that `number` is assigned `static_dynamic: dynamic` in the output manifest.
3. Run `classify-entities --config itsm_config.yaml`.
4. Observe that `number` is assigned `static_dynamic: static` instead.

## Root Cause
- `config.yaml` contains an `entity_discovery_template` that explicitly asks the model for `static_dynamic`:
  - `... "static_dynamic": "dynamic", ...`
- `itsm_config.yaml` uses a simpler prompt and does not ask for `static_dynamic`.
- In `dd_parser/post_processor.py`, the code uses the model-provided `static_dynamic` when present.
- If `static_dynamic` is missing, the code falls back to `_infer_static_dynamic()`.
- `_infer_static_dynamic()` includes `number` as a static indicator, so it correctly returns `static`.

## Why This Is a Bug
The package is inconsistently depending on LLM output for time-dependency classification. When the model is allowed to provide `static_dynamic`, its output can override a more reliable heuristic and produce incorrect assignments.

## Suggestion for Fix
Option 1:
- Avoid asking the LLM for `static_dynamic` in the prompt template.
- Let the package infer `static_dynamic` consistently for panel/longitudinal datasets.

Option 2:
- Keep the prompt field, but validate the model output against heuristics.
- If the model returns a questionable `dynamic` assignment for numeric attributes like `number`, use the package inference instead.

## Files Involved
- `config.yaml`
- `itsm_config.yaml`
- `.venv/lib/python3.13/site-packages/dd_parser/llm_client.py`
- `.venv/lib/python3.13/site-packages/dd_parser/post_processor.py`
