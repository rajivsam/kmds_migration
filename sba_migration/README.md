# sba_migration

This is the primary and largest migration example in `dd_parser_cleaner_migration`.

It demonstrates a full migration workflow using:
https://github.com/rajivsam/dd-parser-cleaner/

## What Is Included

- configuration files for migration and provisional runs
- source data, cleaned outputs, and quarantine artifacts
- data dictionary assets
- workflow and analysis documents
- notebooks used for verification and cleaning

## Typical Workflow

1. Review `config.yaml` and `provisional_config.yaml`.
2. Inspect documents in `documents/` and `data_dictionary/`.
3. Run and validate the cleaning/migration workflow.
4. Verify outputs in `data/dd_cleaner/` and `documents/dd_cleaner/`.

## Notes

Treat this folder as a self-contained example. Keep updates reproducible and document any workflow changes in the local docs.

For a senior-engineer view of the KMDS toolkit architecture, see `documents/KMDS_toolkit_summary.md`.

A screenshot of the generated KMDS knowledge graph workbench is available at `images/kmds-sba-migration_kg.png`.
