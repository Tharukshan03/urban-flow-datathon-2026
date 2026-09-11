# Member 3 — Demand and spatial findings

## 1. Demand overview

The official processed dataset contains **45,533,334 retained pickups** from **2025-04-01 00:00:00 through 2026-03-31 23:59:59**. This report describes retained records, not all raw demand. No preprocessing, Phase 2 aggregation or forecasting was rerun. Existing full OD tables reconcile to the retained total. The new destination report uses one column-only DuckDB scan and matches full OD destination marginals exactly.

The busiest clock hour is **18:00–19:00**, with **3,211,841** annual pickups, or **8,799.56** per calendar day. Source: `member3_demand_by_hour.csv`; chart: [demand_by_hour.png](figures/demand_by_hour.png).

Time buckets are half-open: morning [06:00,10:00), midday [10:00,16:00), evening [16:00,20:00), late night [20:00,24:00) plus [00:00,06:00). Normalized intensity divides counts by 365 days and the nominal window length; it is not active-service-hour intensity. The documented absent hour **2026-03-08 02:00** remains zero. No timezone or daylight-saving correction is inferred.

Null pickup and destination labels account for **68,352** and **82,030** records respectively. All full totals retain these groups; top-zone/pair displays require readable endpoints. Existing borough labels such as `Unknown` and `EWR` remain as supplied; `(missing label)` is a display marker, not invented geography. Source: pickup/dropoff total CSVs and full OD Parquet tables.

## 2. Top pickup hotspots

| pickup_zone_name | pickup_count |
| --- | --- |
| Upper East Side South | 2,014,915 |
| JFK Airport | 1,923,134 |
| Midtown Center | 1,922,045 |
| Upper East Side North | 1,770,798 |
| Penn Station/Madison Sq West | 1,433,926 |
| Midtown East | 1,408,405 |
| Times Sq/Theatre District | 1,364,421 |
| Lincoln Square East | 1,295,316 |
| LaGuardia Airport | 1,213,660 |
| Murray Hill | 1,202,194 |

Source: `member3_pickup_zone_totals.csv`; chart: [hotspot_zones.png](figures/hotspot_zones.png).

## 3. Top destination hotspots

| dropoff_zone_name | dropoff_count |
| --- | --- |
| Upper East Side North | 1,835,816 |
| Upper East Side South | 1,825,726 |
| Midtown Center | 1,591,040 |
| Times Sq/Theatre District | 1,302,813 |
| Murray Hill | 1,251,418 |
| Midtown East | 1,194,074 |
| East Chelsea | 1,149,412 |
| Lincoln Square East | 1,148,423 |
| Upper West Side South | 1,143,692 |
| Lenox Hill West | 1,096,437 |

**Upper East Side North** ranks first with **1,835,816** dropoffs. Source: `member3_dropoff_zone_totals.csv`; chart: [hotspot_zones.png](figures/hotspot_zones.png).

## 4. Major OD flows

| pickup_zone_name | dropoff_zone_name | trip_count |
| --- | --- | --- |
| Upper East Side South | Upper East Side North | 290,297 |
| Upper East Side North | Upper East Side South | 247,748 |
| Upper East Side South | Upper East Side South | 202,435 |
| Upper East Side North | Upper East Side North | 186,379 |
| Midtown Center | Upper East Side South | 135,074 |
| Upper East Side South | Midtown Center | 126,222 |
| Midtown Center | Upper East Side North | 108,494 |
| Upper East Side South | Midtown East | 101,001 |
| Lincoln Square East | Upper West Side South | 100,044 |
| Upper West Side South | Upper West Side North | 96,591 |

Directions are pickup → dropoff. A same-zone pair means endpoints share a zone, not that a vehicle stayed at one physical location. Source: full `data/processed/member3_od_zone_pairs.parquet` (top 100 also in `member3_od_zone_pairs.csv`); chart: [od_flows.png](figures/od_flows.png).

| pickup_borough_name | dropoff_borough_name | trip_count |
| --- | --- | --- |
| Manhattan | Manhattan | 36,234,761 |
| Queens | Manhattan | 2,179,301 |
| Queens | Queens | 1,263,970 |
| Manhattan | Queens | 1,142,770 |
| Manhattan | Brooklyn | 1,063,484 |
| Brooklyn | Brooklyn | 938,334 |
| Queens | Brooklyn | 690,624 |
| Brooklyn | Manhattan | 542,898 |
| Manhattan | Bronx | 285,729 |
| Brooklyn | Queens | 215,584 |

The largest borough-label flow is **Manhattan → Manhattan**, with **36,234,761** trips (79.58% of all retained records). Source: `member3_od_borough_pairs.csv`; chart: [member3_borough_flows.png](figures/member3_borough_flows.png).

## 5. Morning, evening and late-night differences

| time_bucket | trip_count | window_hours_per_day | share_percent | mean_pickups_per_nominal_hour |
| --- | --- | --- | --- | --- |
| morning_peak | 5,724,154 | 4 | 12.571 | 3,920.653 |
| midday | 14,045,862 | 6 | 30.847 | 6,413.636 |
| evening_peak | 11,883,847 | 4 | 26.099 | 8,139.621 |
| late_night | 13,879,471 | 10 | 30.482 | 3,802.595 |

Evening intensity is **2.08 times** morning intensity. Late night has more total trips than evening (13,879,471 versus 11,883,847), but less demand per nominal hour because it spans ten hours rather than four. Source: `member3_spatial_time_summary.csv`, reconciled independently to the hour-of-day aggregate.

Leading directed readable pair within each bucket:

| time_bucket | pickup_zone_name | dropoff_zone_name | trip_count |
| --- | --- | --- | --- |
| morning_peak | Upper East Side North | Midtown Center | 35,293 |
| midday | Upper East Side South | Upper East Side North | 126,637 |
| evening_peak | Upper East Side South | Upper East Side North | 83,859 |
| late_night | Upper East Side South | Upper East Side North | 46,364 |

Source: full `member3_od_zone_time.parquet`; selected top five per bucket in `member3_spatial_top_time_pairs.csv`. Chart: [member3_od_by_time.png](figures/member3_od_by_time.png). These are volume patterns, not proof of commute purpose or unmet demand.

## 6. Forecasting summary

| horizon_hours | baseline_mae | improved_mae | baseline_rmse | improved_rmse | winner |
| --- | --- | --- | --- | --- | --- |
| 24 | 33.604 | 32.303 | 53.827 | 52.090 | Improved |
| 48 | 33.574 | 34.268 | 53.773 | 55.025 | Baseline |
| 72 | 33.571 | 35.189 | 53.752 | 56.370 | Baseline |

The improved model wins at 24h; the seasonal baseline wins at 48h and 72h. Metrics are pickups per zone-hour over 53 daily test origins and each horizon’s first H predictions. Recursive paths do not use future observed demand. Test windows overlap, and the ten zones were selected retrospectively in Phase 2; results are conditional on that cohort. Source: `member3_forecast_metrics.csv` (full precision) and [demand_forecast.png](figures/demand_forecast.png). No models were rerun in Phase 4.

## 7. Operational recommendations

1. Prioritize a staging-capacity review in **Upper East Side South**, the first-ranked pickup zone with **2,014,915** retained pickups (4.43% of all retained trips). Use observed queues and utilization to size any deployment; the counts alone do not establish a vehicle shortage. Evidence: `member3_pickup_zone_totals.csv` and `figures/hotspot_zones.png`.

2. Plan an **evening 16:00–20:00** dispatch emphasis in **Midtown Center**, which records **629,425** pickups in that window (431.11 per nominal hour). Network-wide evening intensity is **8,139.62** pickups/hour versus **3,920.65** in the morning. Evidence: `member3_spatial_pickup_by_time.csv`, `member3_spatial_time_summary.csv`, `figures/demand_by_hour.png`.

3. Keep **20:00–06:00** dispatch coverage under review for **Upper East Side South → Upper East Side North**, the leading readable late-night pair with **46,364** trips. Late-night network volume is **13,879,471**, but its ten-hour window averages only **3,802.59** pickups/hour; avoid allocating staff from window totals alone. Evidence: `member3_spatial_top_time_pairs.csv` and `figures/member3_od_by_time.png`.

4. Monitor both directions of **Upper East Side South ↔ Upper East Side North** when planning repositioning. The leading direction carries **290,297** trips versus **247,748** in reverse, a difference of **42,549** over the year. Check time-specific vehicle availability before moving empty vehicles: these are occupied-trip counts, not a fleet balance. Evidence: `member3_od_zone_pairs.csv` and `figures/od_flows.png`.

5. Use the **24h gradient-boosting forecast** as the starting point for next-day dispatch and the **seasonal baseline at 48h/72h** for longer-range staffing, subject to ongoing monitoring. Held-out MAE favors those methods at each horizon (values in Section 6). This choice is suggested by the observed test results, not an independently validated deployment policy. Evidence: `member3_forecast_metrics.csv` and `figures/demand_forecast.png`.

## Member 3 completion summary

Delivered validated hourly demand, baseline/candidate forecasts for 24/48/72h, pickup/destination hotspots, directed zone and borough flows, time-window comparisons and five evidence-linked recommendations. All conclusions concern the official retained-trip dataset. No unsupported savings, vehicle quantities or geographic coordinates are inferred.
