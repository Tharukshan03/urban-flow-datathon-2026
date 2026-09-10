# AI Mobility Assistant

Bonus Track 5 is a safe, deterministic natural-language assistant for city officials and fleet managers. It answers business questions using only the verified small analytics snapshot copied from the Track 6 reporting bundle.

## Run

From the repository root:

```powershell
python -m pip install -r requirements.txt
streamlit run assistant/app.py
```

The app reads from `assistant/data/` and does not require raw taxi data, parquet files, notebook execution or trained model artifacts.

## What it answers

- Top pickup zones
- Top destination zones
- Borough pickup demand
- Hourly demand and weekday demand
- OD routes overall and by time window
- Forecast model comparison for 24/48/72 hours
- Saved 24/48/72-hour forecasts by zone
- Operational recommendations from the verified report

## Safety approach

The assistant does not translate questions into arbitrary SQL or Python.

Instead, it uses a small routing layer:

1. Normalize the question.
2. Classify the intent with keyword and pattern rules.
3. Extract a zone, borough, horizon or time window when needed.
4. Call a fixed analytics function.
5. Return a concise explanation grounded in bundled CSV/report files.

If a zone is not found, the assistant suggests similar valid zone names. If the question is too vague, it asks for clarification. If the request is outside the supported scope, it says so explicitly.

## Example questions

- What are the top 5 pickup zones?
- Which destination zone is busiest?
- What time is demand highest?
- What is the strongest OD route?
- What are the strongest evening routes?
- Which forecasting model should we use for 24 hours?
- What about 72 hours?
- What is the forecast for JFK Airport?
- What should fleet managers do during evening peaks?

## Notes

- Forecast metrics are backtest results from the verified reporting snapshot.
- Saved forecast outputs are archived April 1-3, 2026 values, not a live forecast.
- All answers remain descriptive and evidence-based.
