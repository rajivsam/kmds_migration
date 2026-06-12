# KMDS Modeling Agent Initialization

## Purpose
This document helps you resolve initialization and runtime issues when installing `kmds-modeling` into an SBA workspace such as `sba_migration`.

The package is designed to be installed into an existing KMDS workspace and used with the same CLI commands provided by this repo.

## Expected workflow
1. Install the package into the SBA workspace.
2. Ensure the workspace has a valid `modeling_config.yaml` that points to `working_dir`.
3. Run the same CLI commands from the workspace:
   - `kmds-modeling evaluate --config /path/to/modeling_config.yaml`
   - `kmds-modeling export --config /path/to/modeling_config.yaml`

## Installation
From inside the SBA workspace environment:

```bash
pip install kmds-modeling
```

If you are installing from a built artifact instead of PyPI:

```bash
pip install /path/to/kmds_modeling-0.1.0-py3-none-any.whl
```

## Configuration expectations
The package resolves paths via `working_dir` in the config file. Your `modeling_config.yaml` should include a valid workspace root, for example:

```yaml
working_dir: /path/to/sba_migration
```

Common directories expected inside the workspace:
- `data/featurization/` for `model_ready_numeric_data.csv`
- `models/` for output artifacts

## CLI usage
Use the same commands you would in the package repo:

```bash
kmds-modeling evaluate --config /path/to/modeling_config.yaml
kmds-modeling export --config /path/to/modeling_config.yaml
```

If you install inside a virtualenv, make sure the `kmds-modeling` command is available in that environment.

## Troubleshooting steps

### 1. CLI command not found
If `kmds-modeling` is unavailable:
- Verify the package installed successfully:
  ```bash
  pip show kmds-modeling
  ```
- Check that the active Python environment is the one where you installed the package.
- If using a shell session, restart or re-source the virtualenv.

### 2. Config file problems
If the package refuses to load the config:
- Confirm `working_dir` is set and points to the SBA workspace root.
- Validate the YAML file for syntax errors.
- Ensure the path to the config file is absolute or relative to the current shell directory.

### 3. Missing `model_ready_numeric_data.csv`
The package expects KMDS featurization output under the workspace `data/featurization/` path.
- Confirm the file exists:
  ```bash
  ls /path/to/sba_migration/data/featurization/model_ready_numeric_data.csv
  ```
- If the file is missing, run the featurization pipeline first.

### 4. Workspace path resolution errors
If the package reports invalid or missing workspace directories:
- Verify `working_dir` in `modeling_config.yaml`.
- Confirm the SBA workspace has `data/featurization/` and can write to `models/`.
- Check permissions if the package cannot create or write artifacts.

### 5. Package import or runtime errors
If the installed package fails while running the CLI:
- Try importing the package in Python:
  ```python
  import kmds_modeling
  print(kmds_modeling.__file__)
  ```
- Confirm the installed code is the generic package, not a local repo path that includes workspace examples.
- If an error occurs during execution, capture the stack trace and verify the failing module is one of:
  - `kmds_modeling.cli`
  - `kmds_modeling.core.runner`
  - `kmds_modeling.core.path_coordinator`
  - `kmds_modeling.core.notebook_utils`

## Common SBA migration issues
- `working_dir` still points to the original repo instead of the new `sba_migration` workspace.
- The active workspace does not contain the featurization export file expected by the package.
- Virtualenv mismatch between install environment and runtime shell.
- `kmds_modeling` package installed from source without the correct `src/` layout.

## Recommended checks when issues occur
1. Confirm the active Python environment:
   ```bash
   python -c "import sys; print(sys.executable)"
   ```
2. Confirm the installed package location:
   ```bash
   python -c "import kmds_modeling; print(kmds_modeling.__file__)"
   ```
3. Confirm config file contents:
   ```bash
   cat /path/to/modeling_config.yaml
   ```
4. Confirm required input data exists:
   ```bash
   ls /path/to/sba_migration/data/featurization/model_ready_numeric_data.csv
   ```
5. Confirm output directory is writable:
   ```bash
   mkdir -p /path/to/sba_migration/models && touch /path/to/sba_migration/models/.write_test && rm /path/to/sba_migration/models/.write_test
   ```

## Notes
- This document is meant to help when the package is installed into a separate SBA workspace and you want to run the same CLI commands.
- The package itself does not bundle SBA-specific code; SBA examples remain outside the installable package.
- If you need deeper debugging, compare the workspace config and paths against the repo example layout.
