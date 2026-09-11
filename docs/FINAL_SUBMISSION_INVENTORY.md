# Final Submission Inventory

## A. Main deliverables

- `MergeConflicts_FinalNotebook.ipynb`
- `reports/MergeConflicts_Technical_Report.pdf`
- `docs/DEMO_VIDEO_LINK.txt`
- `docs/MergeConflicts_Demo_Script.md`

## B. Supporting notebooks and scripts

- `notebooks/01_data_audit_and_cleaning.ipynb`
- `notebooks/02_FarePrediction.ipynb`
- `notebooks/03_DurationPrediction.ipynb`
- `notebooks/03_demand_and_spatial_analysis.ipynb`
- `src/`
- `requirements.txt`
- `data/feature_contract.md`
- `reports/data_cleaning_decisions.md`
- `reports/demand_spatial_findings.md`
- `reports/member3_forecast_metrics.csv`
- `reports/forecast_24h.csv`
- `reports/forecast_48h.csv`
- `reports/forecast_72h.csv`

## C. Models

- `models/fare_pipeline.pkl`
- `models/duration_pipeline.pkl`

## D. Figures

### Member 2

- `reports/figures/fare_predicted_vs_actual.png`
- `reports/figures/fare_residual_distribution.png`
- `reports/figures/fare_mae_by_hour.png`
- `reports/figures/fare_mae_by_distance_bucket.png`
- `reports/figures/duration_predicted_vs_actual.png`
- `reports/figures/duration_residual_distribution.png`
- `reports/figures/duration_mae_by_hour.png`
- `reports/figures/duration_mae_by_distance_bucket.png`

### Member 3

- `reports/figures/demand_forecast.png`
- `reports/figures/hotspot_zones.png`
- `reports/figures/od_flows.png`
- `reports/figures/demand_by_hour.png`

### Member 4 and bonus presentation

- `reports/figures/MergeConflicts_Architecture_Diagram.png`
- `reports/figures/MergeConflicts_Architecture_Diagram.svg`
- `reports/figures/bonus_track6_overview.png`
- `reports/figures/bonus_track6_forecasting.png`

## E. Track 5 AI Mobility Assistant

- `assistant/app.py`
- `assistant/router.py`
- `assistant/analytics.py`
- `assistant/README.md`
- `assistant/data/`
- `reports/bonus_track5_summary.md`

Cache directories and test-generated artifacts are excluded from the final package.

## F. Track 6 Business Analytics Dashboard

- `dashboard/app.py`
- `dashboard/README.md`
- `dashboard/data/`
- `reports/bonus_track6_summary.md`

Cache directories and test-generated artifacts are excluded from the final package.

## G. Data required for the private competition submission

- `data/splits/train.parquet`
- `data/splits/validation.parquet`
- `data/splits/test.parquet`

Additional required competition context is represented by the feature contract, cleaning decisions, and bundled aggregate reporting files. Raw monthly source files and the full processed intermediate dataset are excluded because the requested private package uses the fixed competition splits.

> **Confidentiality warning:** These large competition datasets belong only in the private submission ZIP. They must not be added to public Git history or published through the repository.

## Submission exclusions

The package excludes `.git/`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ipynb_checkpoints/`, temporary helpers, raw source data, Mac metadata, duplicate outputs, local secrets, and personal files.
