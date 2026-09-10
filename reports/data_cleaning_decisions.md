# Data cleaning decisions: Step 6

**Status: proposed policy, not applied.** Investigation covers all **48,601,782 rows** in 12 monthly files. Raw data and Steps 1-5 remain unchanged. No cleaned dataset, splits, models, imputation, or corrections were produced. Notebook: `notebooks/01_data_audit_and_cleaning.ipynb`.

## Decisions

| Anomaly | Count | Percent | Proposed Treatment | Justification |
|---|---:|---:|---|---|
| Negative base_fare | 2,400,031 | 4.93815433% | KEEP raw; FILTER FOR FARE MODELLING | Mixed signed-charge behavior, not verified refunds; exclude negative targets from a nonnegative gross-fare model. |
| Negative final charge (additional evidence) | 875,399 | 1.80116647% | KEEP raw; FILTER FOR FARE MODELLING | Includes 5,572 rows with nonnegative base fare. Combined base-or-final-negative rule affects 2,405,603 rows. |
| Negative distance | 0 | 0.00000000% | FILTER FOR DISTANCE/TIME MODELLING if present | No observed rows; negative physical distance would require review. |
| Zero distance with nonzero base fare | 1,471,746 | 3.02817292% | KEEP; FLAG FOR REVIEW | Waiting/short trips or incomplete distance readings are plausible; no blanket removal. |
| rider_count == 0 | 231,578 | 0.47648047% | KEEP; NO IMPUTATION | Likely provider-specific recording behavior; unknown/default is plausible but unproven. |
| Negative duration | 1,942 | 0.00399574% | KEEP raw; FILTER FOR TIME/SPEED MODELLING pending review | 1,431 repeated-hour candidates; do not automatically add an hour or delete trips. |
| Zero duration | 649,668 | 1.33671642% | KEEP raw; FILTER FOR TIME/SPEED MODELLING | 632,625 have positive distance. Elapsed time is not usable as recorded. |
| Speed >100 mph | 11,899 | 0.02448264% | FILTER FOR TIME/SPEED MODEL VIEW; retain raw | Proposed conservative ceiling. Retain 80-100 mph for review; no winsorization. |
| Historical pickup/dropoff 2008/2009 | 8 | 0.00001646% | QUARANTINE FROM ANALYSIS; retain raw | All eight full records conflict with the stated observation period; do not invent replacement years. |
| Other pickup outside observation interval | 6 | 0.00001235% | KEEP master; EXCLUDE FROM PERIOD-SCOPED VIEW ONLY | Four March 31, 2025 pickups and two April 1, 2026 pickups. Scope exclusions, not invalid trips. |
| Either timestamp outside source month | 19,646 | 0.04042239% | KEEP; partition and review | 19,251 short boundary examples; 374 other adjacent cases; 13 remaining mismatches; 8 historical. No blanket file-month rule. |

These are view-specific policies, not universal deletion rules. Keep an intact raw/master archive. Financial adjustments may remain useful for accounting, while unusable duration measurements should not enter duration/speed targets. Do not automatically exclude a valid trip from demand analysis solely because its fare is negative or a timestamp needs interpretation.

## Investigation supporting the decisions

### Negative base fares and final charges

All **2,400,031 negative-base-fare rows are provider code 2**. Payment code 0 accounts for **1,694,004 (70.58%)**; code 4 for **455,956 (19.00%)**; code 2 for **162,267 (6.76%)**; code 3 for **86,005 (3.58%)**; and code 1 for **1,799 (0.07%)**. Rate class and offline flag are missing in 1,694,004 of these rows. Detailed counts, within-group percentages, code-conditioned percentages, and payment/provider combinations are in the notebook.

Only **869,827 (36.24%)** have a negative final charge; **1,530,204 (63.76%)** have a positive final charge. Another monetary component is negative in **706,187 (29.42%)**. Most have positive duration: **2,399,838**; **2,195,395** have positive distance. Mean base fare is **-10.2942**, mean final charge **-6.5527**, and mean duration **18.1944 minutes**. Sample median duration is about **16 minutes**, versus **13.73** for nonnegative fares.

This is a mixture of signed financial records and apparently active trips, not evidence that all negatives are refunds or voids. No transaction identifiers or matched reversal evidence establish such a classification. The [TLC dictionary](https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf) describes flex-fare, dispute, no-charge, and other payment types in TLC data; **the competition mapping is unconfirmed**, so these names are hypotheses for the observed codes. Do not take absolute values, replace negative fares with zero, or infer code meanings as facts.

**Policy:** retain raw and accounting records; exclude `base_fare < 0 OR charge_total < 0` from a nonnegative gross-fare training view. This catches **2,405,603** rows, including **5,572** additional negative-final-charge rows. If the team instead models net signed charges, this exclusion is inappropriate and must be changed. Avoid applying it automatically to demand-only or duration-only tasks.

### Zero distance with nonzero fare

**1,455,127 (98.87%)** have positive duration; **405,252 (27.54%)** have equal origin/destination IDs. Equal IDs establish the same zone, not the same physical point. Mean duration is **15.0950 minutes**, sample median **12.9667**, and sample p95 **38.2842**. Mean base fare is **22.6166**, sample median **17.605**, and sample p95 **77.00**. Payment code 0 represents **67.93%**, provider 2 **89.78%**, and rate code 5 **10.95%**; rate code is missing for **67.93%**.

[TLC fare rules](https://www.nyc.gov/site/tlc/passengers/taxi-fare.page) permit time-based charging while waiting or moving slowly. This supports retaining possible waiting/short trips but does not explain every different-zone zero-distance record. **KEEP and flag; no distance imputation or blanket removal.** Distance-sensitive models need an explicit later decision about these measurements. Under the combined eligibility scenario below, **1,250,568** remain after other exclusions.

### Zero riders compared with positive riders

Provider 1 accounts for **215,567 (93.09%)** of zero-rider rows, versus **20.89%** of positive-rider rows. Payment code 1 accounts for **82.76%** versus **84.21%**. **222,846 (96.23%)** zero-rider rows have positive distance and **229,453 (99.08%)** positive duration.

| Measure | Zero riders | Positive riders |
|---|---:|---:|
| Mean base fare | 17.1411 | 19.3343 |
| Mean distance, miles | 2.5540 | 3.5770 |
| Mean duration, minutes | 14.5022 | 17.5126 |
| Approximate sample median duration, minutes | 11.30 | 12.775 |

Neither group has missing original source fields. This means zero-rider records do **not** simply reproduce the known broadly missing-field pattern. Provider concentration and otherwise trip-like values support a recording/default hypothesis, but do not prove that zero means unknown. **KEEP and flag; do not replace with 1, a median, or missing without confirmed semantics.** Exclude the rider-count field from passenger-count interpretation until clarified, rather than discarding otherwise useful trips. **228,606** such rows remain under the combined eligibility scenario.

### Negative and zero durations

There are **1,942 negative** and **649,668 zero** durations. Of the negative durations, **1,431 (73.69%)** fall on November 2, 2025 with both timestamps in the repeated 01:00 hour and a difference between -60 and 0 minutes. [NIST](https://www.nist.gov/pml/time-and-frequency-division/popular-links/daylight-saving-time-dst) documents the clock rollback on the first Sunday in November. This is compatible with a clock ambiguity **if** these are applicable local times, but the source is timezone-naive and does not prove that interpretation.

**632,625 zero-duration records have positive distance**, making their elapsed travel time unusable as recorded. **KEEP raw; exclude all 651,610 non-positive durations from duration/speed model eligibility until resolved.** Do not add an hour, invent a duration, or calculate speed for them. They need not be removed from unrelated accounting/demand views.

### Proposed speed ceiling: 100 mph

Use **strictly greater than 100 mph** as the proposed time/speed modelling exclusion. Values equal to 100 remain eligible. No capping or rewriting. Keep 80-100 mph for review.

The exact p99.9 is **46.8506 mph**; p99 is **34.2581 mph**, while the maximum is **4,816,614.8 mph**. [NY DMV guidance](https://dmv.ny.gov/brochure/mv21.pdf) describes expressways normally at 55 mph and some at 65 mph. A **100 mph trip average is about 54% above 65 mph and 2.13 times the observed p99.9**, leaving a large tolerance for short-trip timing/distance error and out-of-area travel. It is an operational modelling tolerance, not a legal limit for every route or a learned physical boundary.

Threshold sensitivity: >80 affects **13,589**, >100 **11,899**, and >120 **10,672** rows. Choosing 100 retains **1,690** rows in (80,100] while excluding **1,227** in (100,120] plus the extreme tail. Within (80,100], **488/1,690** last at most a minute; above 120, **6,512/10,672** do. Short-record instability and physically extreme samples support a generous ceiling rather than a percentile-only cutoff. The value is a judgement with explicit tolerance, **not justified merely by roundness**; team confirmation is still needed for target-specific use and out-of-area exceptions.

### Historical timestamps and month boundaries

All eight historical rows are printed with every original field. All are provider 2, have positive fares, and contain dates in 2008/2009. Seven have durations from roughly 0.17 to 68 minutes; one spans about 921.53 minutes. They may be real operational records with bad dates, but their years clearly conflict with the observation period. **Quarantine all eight from analysis views; retain raw and do not guess replacement dates.**

Of **19,646** rows with either timestamp outside its source month:

- **19,251** are nonhistorical short near-boundary cases (both timestamps within two hours of a source-month boundary, positive duration at most two hours). These are plausible boundary activity, not certified valid in every other field.
- **374** are other adjacent-boundary cases. Samples include roughly 18-24-hour durations for short distances; review separately without a blanket filename rule.
- **13** are remaining nonhistorical mismatches. Examples span several days for small distances, such as 0.49 miles over about 4,062 minutes; these look implausible as ordinary metered trips and need targeted adjudication.
- **8** are historical.

**Retain legitimate boundary crossings.** The two-hour grouping is an inspection convention, not a cleaning cutoff. Flag the 374 and 13 groups for review; no new maximum-duration rule is inferred from a file-month mismatch. Their final duration-specific treatment remains unresolved and is **not an additional exclusion in the count below**.

Define a proposed period-scoped view by pickup in **[2025-04-01, 2026-04-01)**, retaining dropoffs after midnight or after the period end when pickup is in scope. This scopes out the eight historical pickups and **six additional legitimate boundary pickups** (four March 31, two April 1). Keep those six in the master; excluding them from this interval is not cleaning them as bad records. Confirm the intended pickup-based period with the team.

## Exact overlap and affected-row accounting

| Proposed exclusion rule | Rows | Percent of all rows |
|---|---:|---:|
| Historical analysis quarantine | 8 | 0.00001646% |
| Other out-of-period pickups (scope only) | 6 | 0.00001235% |
| Negative base fare OR negative final charge | 2,405,603 | 4.94961893% |
| Negative distance | 0 | 0.00000000% |
| Non-positive duration | 651,610 | 1.34071216% |
| Speed >100 mph | 11,899 | 0.02448264% |


These rules overlap. The notebook contains the full pairwise anomaly matrix and monthly proposed union counts. Examples: **204,636** negative-fare rows also have zero distance/nonzero fare; **16,619** zero-distance charged rows have non-positive duration; **500** zero-rider rows exceed 100 mph; one historical row exceeds 100 mph. There are **4,554,053 (9.37013585%)** distinct rows meeting any measured anomaly (using >100 mph for the speed category), but many are intentionally retained.

For a conservative shared fare/time model view using the **OR of all six proposed exclusion rules**:

- **Unique rows excluded or affected by at least one proposed exclusion: 3,068,448 (6.31344752%).**
- **Remaining rows: 45,533,334.**
- Sum of individual rule counts is **3,069,126**; that is **678** larger than the distinct union and must not be used as the removed-row count.
- **Raw/master rows proposed for deletion: 0. Numeric values proposed for alteration/imputation: 0. Actual changes applied: 0.**

The 3,068,448 union is an explicit scenario, not a universal mandate for every task. Target-specific views should use the relevant subset; no exclusions should silently carry into demand counts or net-accounting analysis. The unresolved long-duration boundary review could change a future policy and would require recomputing its union. This report does not claim the remaining rows are fully clean.

## Team confirmations before implementation

1. Confirm competition code meanings and whether signed fares represent net accounting, adjustments, or a nonnegative gross-fare target.
2. Confirm task-specific model eligibility versus a single shared model view, including the 100 mph ceiling and route coverage.
3. Confirm timezone/clock conventions before any repeated-hour correction; the 1,431 candidates are not proven repairs.
4. Confirm zero-rider semantics; retain without imputation until documented.
5. Confirm pickup-based observation scope and adjudicate the 374 adjacent/13 other timestamp cases before treating the duration view as final.

No approval is being requested to perform further work here: this step stops at documented recommendations. Applying any rule is a later task.

## Method and verification

Counts, code percentages, missingness, means, extrema, overlaps, and union sizes are exact over all input rows. Subgroup medians/p95 are approximate from fixed-seed random-priority samples (up to 5,000 per group); full-dataset speed percentiles are the exact Step 5 results. Source file sizes and modification times remained unchanged. All Step 6 code completed without errors and Steps 1-5 were compared unchanged. No cleaned Parquet, splits, or models were created.
