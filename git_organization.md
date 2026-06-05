# Git Organization Guide

This document explains how this repository is organized and how a code assistant should operate within it.

## Top-Level Model

The parent repository is a container for multiple migration examples.

- Parent repo: `dd_parser_cleaner_migration`
- Child example folders: one folder per migration example (for example, `sba_migration/`)

Each child folder is treated as a normal directory in the parent Git repository.

## Repository Rules

1. Keep a single Git repository at the parent level.
2. Do not initialize nested Git repositories inside child migration folders.
3. Keep each migration example self-contained with its own documentation and config.
4. Keep parent-level docs focused on cross-example guidance.

## Expected Directory Pattern

- `README.md`: parent-level purpose and navigation
- `git_organization.md`: this operational guide
- `<example_name>/`: one migration example directory
  - `README.md`: brief instructions for that example
  - project-specific configs, data references, notebooks, and outputs

## How A Code Assistant Should Work Here

1. Start at the parent `README.md` and this file for context.
2. Scope changes to one migration directory unless asked to do cross-example changes.
3. Avoid moving or renaming folders unless explicitly requested.
4. Prefer minimal, targeted commits.
5. Update docs whenever workflow or structure changes.
6. Preserve reproducibility: do not delete required inputs or generated evidence files unless requested.

## Commit Strategy

Use clear commit boundaries:

- `docs:` for README or organization updates
- `feat:` for new migration logic or tooling
- `fix:` for corrections in scripts/config/workflow
- `chore:` for non-functional maintenance

## Adding New Migration Examples

When adding a new example:

1. Create a new top-level child folder (for example, `customer_x_migration/`).
2. Add a brief `README.md` in that folder.
3. Add project files for that migration.
4. Update parent `README.md` to list the new example.
5. Commit all related files together.
