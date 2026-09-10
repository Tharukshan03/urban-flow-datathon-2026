# Bonus Track 5 — AI Mobility Assistant

## Business problem

Fleet managers and city officials need quick answers to operational questions without writing SQL or Python. The assistant focuses on the planning questions that matter for taxi deployment: where demand concentrates, when it peaks, which OD flows matter, how the forecast models compare, and which verified recommendations should guide action.

## Solution

The assistant is a safe natural-language layer over the verified small analytics snapshot that already powers Track 6. It does not execute arbitrary code. Instead, it routes each question into one of a small number of deterministic analytics functions backed by small CSV and report files copied from the verified Track 6 bundle.

Architecture:

1. Normalize the question.
2. Classify the intent with keyword and pattern rules.
3. Extract a zone, borough, horizon or time window when needed.
4. Call a fixed analytics function.
5. Return a concise, explainable answer grounded in the bundled data.

## Supported intents

- Top pickup zones
- Top destination zones
- Borough pickup demand
- Hourly demand
- Weekday demand
- OD routes overall
- OD routes from a specific origin zone
- OD routes by operating window
- Forecast model comparison for 24/48/72 hours
- Saved forecast outputs for a zone and horizon
- Operational recommendations from the verified report

## Safety approach

- No arbitrary Python execution
- No unrestricted SQL generation
- No raw taxi data access
- No parquet dependency
- No model artifact dependency
- No silent guessing when the question is vague or unsupported

If a zone is unknown, the assistant reports that clearly and can suggest similar valid zone names. If the request is vague, it asks for clarification. If the request is outside scope, it explains the supported topics instead of fabricating an answer.

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

## Limitations

- The assistant only answers from the verified bundled snapshot.
- Forecast outputs are archived April 1-3, 2026 values, not a live operational model.
- Forecast metrics are backtest results, not deployment outcomes.
- OD tables are truncated reporting extracts, so the assistant only reports what is present in the bundle.

## Track 5 fit

This solution satisfies Track 5 by providing an intelligent, business-facing assistant that helps answer recurring mobility questions safely and explainably, while reusing the already verified analytics outputs from the project.
