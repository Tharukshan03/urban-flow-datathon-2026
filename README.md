# Urban Flow Analytics (Datathon 2026 Starter)

## Project purpose
This repository is a clean starter workspace for a 4-member Datathon 2026 team to collaborate on Urban Flow Analytics tasks (EDA, prediction tracks, forecasting, and final integration) in parallel.

## Team roles
- **Member 1**: Data Cleaning, EDA, shared feature engineering
- **Member 2**: Fare prediction and trip-duration prediction
- **Member 3**: Demand forecasting and hotspot/origin-destination analysis
- **Member 4**: Final notebook, technical report, architecture, integration, demo

## Folder structure
```text
.
├── data/
│   ├── raw/
│   ├── processed/
│   └── splits/
├── docs/
│   ├── DATA_CONTRACT.md
│   ├── SUBMISSION_CHECKLIST.md
│   └── TEAM_WORKFLOW.md
├── figures/
├── models/
├── notebooks/
│   ├── 01_EDA_Cleaning.ipynb
│   ├── 02_FarePrediction.ipynb
│   ├── 03_DurationPrediction.ipynb
│   ├── 04_DemandForecasting.ipynb
│   └── 05_SpatialAnalysis.ipynb
├── reports/
├── src/
│   ├── __init__.py
│   ├── features.py
│   ├── preprocessing.py
│   └── utils.py
├── TeamName_FinalNotebook.ipynb
├── requirements.txt
└── .gitignore
```

## Setup instructions
1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Add local competition data files under `data/raw/` (do not commit them).
4. Start notebooks with:
   ```bash
   jupyter notebook
   ```

## Confidentiality note
Competition datasets, credentials, and trained artifacts must remain local and must not be committed to this repository.

## Final submission ZIP name
`TeamName_CodefestDatathon2026.zip`
