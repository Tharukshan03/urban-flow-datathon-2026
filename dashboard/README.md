# Urban Flow — Fleet positioning and staffing

A lightweight Streamlit management dashboard for Bonus Track 6, **Turning Taxi Data into Business Decisions**. It uses verified reporting outputs to connect demand hotspots, time patterns, OD flows and forecasting accuracy with fleet decisions.

## Run locally

From the repository root, with the project dependencies installed:

```powershell
python -m pip install -r requirements.txt
streamlit run dashboard/app.py
```

For an isolated dashboard-only environment using uv:

```powershell
python -m uv run --no-project --with streamlit==1.63.0 --with plotly==7.0.0 --with pandas==3.0.5 python -m streamlit run dashboard/app.py
```

The local URL is normally `http://localhost:8501`. The app requires no API key, account, raw datasets, Parquet files or model fitting. The only additions to the shared requirements are Streamlit and Plotly. Paths are located relative to the application files, so the data loader also works when launched from another working directory.

## Five management sections

| Section | Purpose and controls |
| --- | --- |
| Executive Overview | Retained-trip, hotspot, Manhattan-flow and forecast KPIs; normalized time-window comparison; problem → evidence → decision story |
| Demand and Hotspots | Top 10/15/20 pickup and destination zones, borough totals, hourly/weekday demand, and a zone selector for time-window intensity |
| OD and Time Patterns | All-day or morning/midday/evening/late-night route leaders; borough selector for the complete destination mix |
| Forecasting | 24/48/72h and zone selectors; both saved forecast paths, exact held-out MAE/RMSE, lower-error method and original CSV download |
| Recommendations | Five recommendations extracted directly from the verified report, with original evidence references and a report download |

## Reporting provenance

- **Source branch:** `feature/forecasting-spatial`
- **Pinned source commit:** `8b3cdee641b59d27ff4ce9cd037bd5e46ccd7096` (`8b3cdee`)
- **Bundled inputs:** 15 CSVs and the findings Markdown report, **223,042 bytes** combined.
- Each file in `data/` is copied **byte-for-byte unchanged** from `reports/` at that commit. `data/manifest.json` records the source path, byte count and SHA-256 for every input.
- `tools/bundle_inputs.py` reproduces the snapshot from the pinned commit using read-only `git show`. It never switches branches or writes to Member 3's original files. It requires that commit to exist locally; the app itself does not require Git.

No raw trips, Parquet aggregates, model binaries, original notebooks, intermediate files or original figure images are bundled. The interactive charts are generated from the small reports. Screenshots of the new dashboard are kept separately under `reports/figures/bonus_track6_*.png`.

To restore a missing or altered bundle, restore the tracked `dashboard/data/` files or run from the repository root:

```powershell
python dashboard/tools/bundle_inputs.py
```

Restart Streamlit after changing the snapshot so its data cache is refreshed. Missing files, changed checksums or inconsistent totals display an actionable error instead of silently replacing the analysis with sample data.

## Three distinct time contexts

1. **Historical analysis:** April 1, 2025–March 31, 2026; 45,533,334 retained pickups. These are processed records, not all raw or real-world demand.
2. **Backtest/evaluation:** the historical test period is February 5–March 31, 2026, with 53 eligible daily origins and separate 24/48/72h errors. Metrics are cohort-wide pickups per zone-hour. The zone selector does not imply zone-specific error measurements.
3. **Saved forecast outputs:** forecast origin April 1, 2026, with target hours through April 3, 2026. These archived predictions are not a live forecast and have no observed outcomes bundled. CSV downloads retain both methods and all ten zones.

Metrics and winning methods come from `data/member3_forecast_metrics.csv`, filtered to **test** rows. Gradient boosting has lower MAE at 24h; the seasonal baseline has lower MAE at 48h and 72h. No evaluation or model training runs inside the dashboard.

## Interpretation and filter limits

- All totals retain missing labels; hotspot rankings require readable names. Supplied `Unknown` and `EWR` borough labels are preserved. `(Missing label)` is only a display marker.
- OD zone reports contain the **top 100 overall pairs** and **top 25 pairs per time window**. The chart displays the strongest ten from that summary; an absent route is not zero demand. There is no misleading arbitrary origin-zone filter over these truncated reports.
- Borough OD tables are complete aggregates. The borough selector affects only the destination-mix chart. It does not infer zone-to-borough mappings.
- Windows are half-open: morning [06:00,10:00), midday [10:00,16:00), evening [16:00,20:00), late night [20:00,24:00) plus [00:00,06:00).
- Intensity uses counts / (365 × nominal window hours). Hour-of-day charts use 365 calendar days. Weekday charts show total volume, not exposure-adjusted rates.
- The documented absent hour, March 8, 2026 at 02:00, remains zero. No timezone or daylight-saving correction is inferred.
- The forecast cohort was selected retrospectively; evaluation windows overlap. The model ranking is evidence for a planning choice, not a proven deployment outcome.
- Occupied-trip OD flows do not measure empty-vehicle availability. No savings, idle-driving reduction, service-level improvement or causal trip-purpose explanation is claimed.

## Checks

Automated source-integrity and Streamlit interaction tests:

```powershell
python -m unittest discover -s dashboard/tests -p test_dashboard.py -v
```

The seven tests verify the pinned bytes, checksums, missing/corrupted inputs, exact metrics, unchanged recommendation wording, every section, five OD windows, demand controls and all 33 forecast horizon/zone combinations. Plotly chart specifications must contain data and titles.

Optional real-browser verification against a running local server uses Playwright only in the test environment, not the application requirements:

```powershell
python -m uv run --no-project --with playwright python dashboard/tests/browser_smoke.py --channel msedge
```

This opens headless Microsoft Edge, checks each section's rendered Plotly charts and browser errors, and saves executive/forecast screenshots. Use a locally available browser channel if Edge is unavailable.

## Files

- `app.py`: single Streamlit app and five management views.
- `utils/data_loader.py`: cached-app input loading support, integrity checks and source recommendation extraction.
- `data/`: immutable small reporting snapshot and manifest.
- `tools/bundle_inputs.py`: reproducible byte-preserving snapshot tool.
- `tests/test_dashboard.py`: reporting and Streamlit interaction checks.
- `tests/browser_smoke.py`: optional browser rendering check.
- `../reports/bonus_track6_summary.md`: business story, evidence and supported decisions.
