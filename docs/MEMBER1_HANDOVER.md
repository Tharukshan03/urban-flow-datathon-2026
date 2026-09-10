# Member 1 Data Lead Handover

**Status:** Complete through Step 9. No modelling started.

## Outputs

- Processed dataset: `data/processed/clean_trips.parquet`
- Retained rows: **45,533,334**
- Feature contract: `data/feature_contract.md`
- Cleaning decisions: `reports/data_cleaning_decisions.md`
- Notebook: `notebooks/01_data_audit_and_cleaning.ipynb`

## Chronological splits

| Split | Path | Rows | Pickup boundary |
|---|---|---:|---|
| Train | `data/splits/train.parquet` | 31,988,176 | `< 2025-12-11 00:00:00` |
| Validation | `data/splits/validation.parquet` | 6,814,901 | `>= 2025-12-11 00:00:00` and `< 2026-02-05 00:00:00` |
| Test | `data/splits/test.parquet` | 6,730,257 | `>= 2026-02-05 00:00:00` |

The split counts sum exactly to **45,533,334**. Timestamp ranges are disjoint, train is earliest, validation is intermediate, and test contains the latest observation through `2026-03-31 23:59:59`. Splits were written incrementally by Parquet row group without shuffling or loading the full dataset into memory.

## Important warnings for Member 2

- Use only features documented as pre-trip in `data/feature_contract.md`.
- `distance_miles`, `rider_count`, `rate_class_id`, `fare_settlement_method`, and `offline_record_flag` are conditional; confirm their availability before trip start.
- Do not use completed-trip charges, tips, tolls, dropoff timestamps, duration, speed, audit fields, or source provenance as model features.
- No imputation policy has been approved in the feature contract.
- The whole-day boundaries target approximately 70% / 15% / 15%; the resulting proportions are 70.252216% / 14.966839% / 14.780945%.
- Split files use Zstandard compression due to disk-space constraints.
- The notebook's protected Step 7 build cell has a recorded refusal/error when the output already exists; the processed file and its lightweight verification completed successfully.
- No train/validation/test modelling, tuning, or machine learning has been performed.
