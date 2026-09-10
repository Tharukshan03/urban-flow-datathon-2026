# Data Contract

## Scope
This project uses competition-provided trip and related data files stored locally, not in GitHub.

## Input storage rules
- Place original files in `data/raw/`.
- Place transformed files in `data/processed/`.
- Place train/validation/test splits in `data/splits/`.
- Reference files with **relative paths only**.

## Governance rules
- Do **not** add competition datasets to the repository.
- Do **not** invent extra dataset columns.
- Do **not** commit trained `.pkl` / `.joblib` artifacts.
- Do **not** include secrets or credentials.

## Hand-off expectations
- Member 1 documents cleaning steps and shared feature assumptions.
- Members 2 and 3 consume agreed processed/split files.
- Member 4 validates final notebook reproducibility from documented paths.
