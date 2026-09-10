# Team Workflow

## Objective
Coordinate a 4-member workflow for the Urban Flow Analytics Datathon 2026 project without blocking each other.

## Roles and ownership
- **Member 1**: Data cleaning, EDA, shared feature engineering.
- **Member 2**: Fare prediction and trip-duration prediction.
- **Member 3**: Demand forecasting and hotspot/origin-destination analysis.
- **Member 4**: Final notebook, technical report, architecture, integration, demo.

## Branching and collaboration
- Create short-lived feature branches per task.
- Keep pull requests focused and small.
- Use clear commit messages with scope (e.g., `eda: add missing value profiling`).

## Shared conventions
- Use **relative paths only** in notebooks and scripts.
- Do not commit competition datasets or trained model artifacts.
- Keep reusable logic in `src/` and call it from notebooks.

## Suggested execution order
1. Member 1 prepares cleaned datasets and shared feature definitions.
2. Members 2 and 3 build task-specific experiments on agreed inputs.
3. Member 4 integrates outputs into the final notebook/report and prepares demo assets.
