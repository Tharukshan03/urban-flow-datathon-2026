# Merge Conflicts — Urban Flow Analytics Demo Script

**Planned duration:** 4 minutes 20 seconds  
**Team:** Merge Conflicts  
**Recording goal:** Present the mandatory analytical work first, then demonstrate the two bonus interfaces as delivery layers for verified outputs.

## Timed demo script

### 0:00–0:25 — Introduction, problem, and objective

**Screen:**  
Open `MergeConflicts_FinalNotebook.ipynb` at **Project Overview**. Keep the project title and high-level solution summary visible.

**Action:**  
Begin with the notebook already open. Point briefly to the objective and the solution components; do not scroll yet.

**Speaker script:**  
“We are Team Merge Conflicts, and this is our solution to the Urban Flow Analytics challenge. We transformed 45,533,334 processed taxi trips into actionable operational insights. Our solution combines fare and duration prediction, demand forecasting, spatial analytics, a manager-facing dashboard, and a safe AI mobility assistant.”

### 0:25–0:50 — Dataset quality and preprocessing

**Screen:**  
Show the final notebook sections **Dataset Description**, **Data Quality Assessment**, **Cleaning Decisions**, and **Feature Engineering**.

**Action:**  
Scroll steadily through the four headings, pausing briefly on the chronological split and leakage controls. Avoid exposing raw dataset filenames.

**Speaker script:**  
“We preserved the raw source data and built a reliable analytical view using chronological train, validation, and test splits. Quality checks covered negative fares, zero-distance trips with fares, nonpositive durations, and unrealistic speeds. The resulting shared features follow an explicit leakage-safe contract so future information is kept out of pre-trip predictions.”

### 0:50–1:25 — Fare prediction

**Screen:**  
Show **Fare Prediction** in the final notebook, then switch to `reports/figures/fare_predicted_vs_actual.png`. If the predicted-versus-actual figure is difficult to read at recording resolution, use `reports/figures/fare_mae_by_distance_bucket.png` instead.

**Action:**  
Point to the selected model and test metrics, then hold the figure long enough for the trend to be visible.

**Speaker script:**  
“For fare prediction, LinearRegression was the best defensible model and outperformed the tested RandomForest and ExtraTrees candidates. On the final chronological test period, it achieved an MAE of 5.571799, RMSE of 10.324520, and R-squared of 0.676153. Estimated route distance substantially improved validation accuracy. This feature is valid only as a pre-trip route estimate; completed-trip mileage is not assumed to be available before pickup.”

### 1:25–1:55 — Trip duration prediction

**Screen:**  
Show **Trip Duration Prediction** in the final notebook, then display `reports/figures/duration_mae_by_distance_bucket.png`.

**Action:**  
Point to the final metrics and the change in error across distance buckets. Keep the chart visible while explaining the limitation.

**Speaker script:**  
“LinearRegression also performed best among the tested duration candidates. Final test MAE was 5.802654 minutes, RMSE was 22.259013 minutes, and R-squared was 0.206474. Longer-duration trips increase the squared error and therefore the RMSE. The model also lacks real-time traffic and weather context, which limits duration accuracy.”

### 1:55–2:30 — Demand forecasting and spatial insights

**Screen:**  
Show `reports/figures/demand_forecast.png`, followed by `reports/figures/hotspot_zones.png` and `reports/figures/od_flows.png`. Use `reports/figures/demand_by_hour.png` if time permits.

**Action:**  
Point to the winning forecast method at each horizon, then switch quickly to the hotspot and flow views.

**Speaker script:**  
“Forecast performance depends on the planning horizon. Gradient Boosting wins at 24 hours with an MAE of 32.302992781, supporting short-horizon tactical dispatch. The seasonal baseline wins at 48 and 72 hours, with MAEs of 33.574418557 and 33.571390821, making it the more reliable longer-range choice. Spatially, Upper East Side South leads pickups; JFK Airport and Midtown Center are major hubs. Manhattan-to-Manhattan accounts for 79.58 percent of trips, and evening demand intensity is 2.08 times morning intensity.”

### 2:30–3:05 — Track 6 business analytics dashboard

**Screen:**  
Show the prepared Streamlit dashboard launched with `python -m streamlit run dashboard/app.py`.

**Action:**  
Move smoothly through only these views: **Executive Overview**, **Demand and Hotspots**, **Forecasting**, and **Recommendations**. Do not demonstrate every control.

**Speaker script:**  
“The Track 6 business dashboard turns validated model outputs and spatial findings into a manager-facing view. The executive overview summarizes the operating picture. Fleet managers can then inspect demand patterns and hotspots, compare horizon-specific forecasts, and review evidence-linked recommendations. The application uses bundled, validated analytics data that remains consistent with the verified outputs.”

### 3:05–3:40 — Track 5 AI Mobility Assistant

**Screen:**  
Show the prepared assistant launched with `python -m streamlit run assistant/app.py`.

**Action:**  
Ask these questions in order. Pause just long enough to show each response.

1. **Question:** “What are the top 5 pickup zones?”  
   **Expected answer type:** Ranked pickup-hotspot list.  
   **Point out:** The answer comes from verified spatial totals.
2. **Question:** “Which forecasting model should we use for 24 hours?”  
   **Expected answer type:** Horizon-specific model recommendation.  
   **Point out:** Gradient Boosting is selected from validated 24-hour results.
3. **Question:** “What is the 24-hour forecast for JFK Airport?”  
   **Expected answer type:** Bundled JFK forecast response.  
   **Point out:** Use only the value displayed by the running assistant; do not narrate a value in advance.
4. **Question:** “What should fleet managers do during evening peaks?”  
   **Expected answer type:** Evidence-linked operational guidance.  
   **Point out:** The response connects evening demand patterns to supported actions.

**Speaker script:**  
“The Track 5 assistant makes the same verified analytics easier to query. It uses deterministic intent routing, entity extraction, predefined analytics functions, and bundled inputs. It does not execute arbitrary Python or unrestricted SQL. These questions demonstrate hotspot lookup, model selection, a zone forecast, and evidence-linked evening guidance without inventing answers.”

### 3:40–4:05 — Architecture and operational recommendations

**Screen:**  
Show `reports/figures/MergeConflicts_Architecture_Diagram.png` full-screen.

**Action:**  
Trace the diagram from left to right and top to bottom. Finish by pointing to **Operational Decision Support**.

**Speaker script:**  
“The architecture moves from raw data through quality controls and shared feature engineering into fare, duration, forecasting, and spatial analysis. Verified outputs then power the dashboard and assistant before reaching operational decision support. Supported actions include hotspot staging review, evening Midtown dispatch emphasis, late-night coverage review, origin-destination-aware repositioning, and using different forecasting methods for tactical and longer-range planning.”

### 4:05–4:20 — Conclusion

**Screen:**  
Return to the final notebook conclusion, or keep the architecture diagram visible.

**Action:**  
Hold on a clean summary view and end without further navigation.

**Speaker script:**  
“Merge Conflicts created an end-to-end solution combining predictive modelling, demand forecasting, spatial insight, a business dashboard, and an AI assistant. Together, these components support more informed taxi operational decisions. Thank you.”

## Recording order and screen preparation

Open and fully load everything before pressing **Record**. Arrange tabs in this order:

1. `MergeConflicts_FinalNotebook.ipynb`
2. `reports/figures/fare_predicted_vs_actual.png`
3. `reports/figures/duration_mae_by_distance_bucket.png`
4. `reports/figures/demand_forecast.png`
5. `reports/figures/hotspot_zones.png` and `reports/figures/od_flows.png`
6. Dashboard at the local Streamlit URL
7. AI Mobility Assistant at its local Streamlit URL
8. `reports/figures/MergeConflicts_Architecture_Diagram.png`

Before recording, launch the applications in separate terminals:

```text
python -m streamlit run dashboard/app.py
python -m streamlit run assistant/app.py
```

Wait for both applications and all chart assets to load. Enter the four assistant questions in advance if the interface supports preserving query history, but leave the first question ready for the live sequence.

## Pre-recording checklist

- [ ] Final notebook opens correctly.
- [ ] Technical report is ready for reference.
- [ ] Architecture diagram opens correctly.
- [ ] Dashboard launches successfully.
- [ ] AI assistant launches successfully.
- [ ] All figures load.
- [ ] Browser tabs are prepared in the recommended order.
- [ ] Dashboard is already loaded before recording.
- [ ] Assistant is already loaded before recording.
- [ ] Terminal errors are cleared or hidden.
- [ ] Raw or confidential dataset filenames are not displayed unnecessarily.
- [ ] Private paths and personal desktop details are hidden where possible.
- [ ] Notifications are disabled.
- [ ] Microphone level and clarity are checked.
- [ ] Screen resolution keeps notebook text and charts readable.
- [ ] Browser zoom is suitable for the recording resolution.
- [ ] Cursor movement is slow and deliberate.
- [ ] Trial run finishes within 3–5 minutes.
- [ ] Final recording finishes within 3–5 minutes.
- [ ] Final video is uploaded to YouTube as **unlisted**.
- [ ] Unlisted YouTube link is copied for the final submission.

## Video quality guidelines

- Speak naturally; do not read the technical report word-for-word.
- Focus narration on verified results and their operational meaning.
- Avoid showing code unless it is needed to explain a result.
- Scroll slowly and pause on each result.
- Keep charts visible long enough for judges to understand their message.
- Present mandatory modelling, forecasting, and spatial work before bonus features.
- Present the dashboard and assistant as value-add delivery layers rather than the core submission.
- Do not expose competition datasets, confidential filenames, private paths, or personal information.
- Do not claim savings, return on investment, causal effects, unmet demand, or required fleet quantities.
- Use only assistant responses displayed by the running application; do not rehearse fabricated output values.
