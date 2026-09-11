# Bonus Track 6 — Turning Taxi Data into Business Decisions

## Business problem

**How can taxi operations improve fleet positioning and staffing by using demand forecasts, pickup hotspots, origin-destination flows and time-of-day demand patterns?**

Managers need to decide where vehicles should stage, which time windows need attention, how to interpret directional passenger flows, and which forecast horizon should inform dispatch versus staffing. Reducing idle driving and improving positioning are business objectives; this analysis does not measure achieved operational or financial impact.

## Delivered dashboard

Run `streamlit run dashboard/app.py` from the repository root. The single Streamlit app provides five sections:

| Section | Management question answered |
| --- | --- |
| Executive Overview | Where are demand and movement concentrated, and what decisions does the evidence support? |
| Demand and Hotspots | Which pickup/destination zones lead, and when does demand rise? |
| OD and Time Patterns | Where do occupied trips travel, and how do leading routes change by operating window? |
| Forecasting | Which method has lower held-out error at 24/48/72h, and what do the saved zone forecasts show? |
| Recommendations | Which five practical actions are supported by the verified findings? |

Interactive controls include top-N hotspot rankings, a pickup-zone time-window view, OD operating-window and borough selectors, and forecast horizon/zone selectors. Plotly charts provide tooltips with counts and units. Original forecast CSVs and the findings report can be downloaded.

## Provenance and data scope

- **Source branch:** `feature/forecasting-spatial`
- **Pinned commit:** `8b3cdee641b59d27ff4ce9cd037bd5e46ccd7096` (`8b3cdee`)
- The dashboard bundles 15 small CSVs and `demand_spatial_findings.md` under `dashboard/data/`, copied unchanged from the source commit's `reports/` directory.
- Total input payload is **223,042 bytes**; `dashboard/data/manifest.json` records every source path, size and SHA-256.
- No original Member 1–4 files, branch contents or analysis outputs are changed. No preprocessing, expensive trip scan, Phase 2 aggregation or Phase 3 modelling is rerun.

The dashboard explicitly separates **historical results (April 2025–March 2026)**, **held-out forecast evaluation**, and **archived April 1–3, 2026 forecast outputs**. It does not present those saved forecasts as current operational predictions.

## Evidence and story

### Where and when demand concentrates

The historical reports cover **45,533,334 retained pickups**. Upper East Side South leads pickup zones with **2,014,915**, followed by JFK Airport with **1,923,134** and Midtown Center with **1,922,045**. Upper East Side North leads destinations with **1,835,816** dropoffs.

**Manhattan → Manhattan carries 36,234,761 trips, 79.58% of all retained trips.** The largest directed zone pair is Upper East Side South → Upper East Side North, with **290,297 trips**, compared with **247,748** in reverse.

Sources: bundled pickup/destination totals and borough/zone OD CSVs. Interactive figures: Executive Overview, Demand and Hotspots, and OD and Time Patterns.

| Operating window | Retained trips | Mean pickups per nominal hour |
| --- | ---: | ---: |
| Morning, 06:00–10:00 | 5,724,154 | 3,920.65 |
| Midday, 10:00–16:00 | 14,045,862 | 6,413.64 |
| Evening, 16:00–20:00 | 11,883,847 | 8,139.62 |
| Late night, 20:00–06:00 | 13,879,471 | 3,802.59 |

Evening intensity is **2.08 times morning intensity**. Late-night volume is larger than evening volume, but its ten-hour window has lower mean intensity. The all-zone clock-hour peak is **18:00–19:00**, with **3,211,841** annual pickups, or **8,799.56** per calendar day.

Sources: `dashboard/data/member3_spatial_time_summary.csv` and `member3_demand_by_hour.csv`. Intensity divides by 365 days and nominal window duration; it does not estimate active service hours.

### What this says about the business problem

Uniform fleet positioning or staffing would ignore pronounced spatial concentration and unequal time-window intensity. OD direction adds another relevant signal: occupied passenger movements are not symmetric. These are descriptive patterns, not proof of supply shortages or causal explanations of trip purpose. Airport schedules, employment activity, weather and fleet availability would be needed to investigate why the patterns occur and estimate the benefit of an intervention.

### Which forecast to use

| Horizon | Seasonal baseline MAE | Gradient boosting MAE | Lower-MAE method |
| --- | ---: | ---: | --- |
| 24h | 33.603788911 | 32.302992781 | Gradient boosting |
| 48h | 33.574418557 | 34.268282886 | Seasonal baseline |
| 72h | 33.571390821 | 35.188656381 | Seasonal baseline |

Source: **test** rows of `dashboard/data/member3_forecast_metrics.csv`; the dashboard reads its values directly. MAE is pickups per zone-hour over 53 daily origins and each horizon's first H predictions. The report also supplies RMSE. These metrics are distinct from the saved April forecasts and do not change when selecting an individual zone.

## Management decisions supported

The Recommendations section preserves the exact five recommendation texts from the bundled findings report:

1. **Hotspot staging review:** Upper East Side South, supported by 2,014,915 pickups; determine vehicle quantities from queue/utilization observations rather than counts alone.
2. **Evening dispatch emphasis:** Midtown Center, supported by 629,425 pickups during 16:00–20:00 and higher network evening intensity.
3. **Late-night coverage review:** Upper East Side South → Upper East Side North, supported by 46,364 late-night trips; account for the longer window.
4. **Directional repositioning checks:** compare the 290,297 versus 247,748 Upper East Side flows before moving empty vehicles; the annual difference is not an available-fleet estimate.
5. **Horizon-specific forecasting:** use gradient boosting as a next-day dispatch reference, and the seasonal baseline for 48h/72h staffing/planning, with ongoing monitoring.

No dollar savings, deployment quantities or operational improvement percentages are invented.

## How Track 6 is satisfied

- **Meaningful business problem:** fleet positioning and staffing under uneven demand.
- **Data analysis:** verified demand, destination, directed OD, time-window and forecast evidence reused with provenance.
- **Interactive dashboard:** five management views with purposeful selectors, tooltips and downloads.
- **Clear story:** decision problem → observed concentration/time differences → limits on causal interpretation → evidence-linked actions.
- **Practical recommendations:** the five source-backed actions above, including different forecast methods by horizon.

## Quality and limitations

The dashboard validates snapshot checksums, reconciled totals, forecast dates and recommendation extraction. Tests compare every copied input byte-for-byte against the pinned commit, exercise all sections and forecast combinations, and check missing/altered file handling. Browser checks exercise actual Plotly rendering. Setup and test commands are in `dashboard/README.md`.

OD zone inputs are truncated to the top 100 overall pairs and top 25 per window, clearly labelled in the app; borough inputs are complete aggregates. Missing geography remains in totals. The absent March 8, 2026 02:00 hour remains zero; no timezone correction is inferred. The ten-zone forecast cohort was selected retrospectively, and test windows overlap. These constraints limit interpretation of generalization and business impact.

Dashboard screenshots:

- [Executive overview](figures/bonus_track6_overview.png)
- [Forecasting](figures/bonus_track6_forecasting.png)
