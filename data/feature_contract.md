# Step 8: Feature Contract

**Dataset:** `data/processed/clean_trips.parquet`  
**Purpose:** define leakage-safe inputs for Member 2's fare and duration models.  
**Targets:** `base_fare` and `trip_duration_minutes`.

This contract is based on the processed Parquet schema: 45 columns, inspected from Parquet metadata and a small sample of the first row group. The full 45+ million row dataset was not loaded. A feature is allowed only when its value is known at the prediction timestamp, before the trip starts. If the team cannot document that timing, the feature is forbidden until reviewed.

## A. Prediction targets

| Target | Data type | Meaning | Model use |
|---|---|---|---|
| `base_fare` | `double` | Recorded base fare | Fare prediction target; never an input |
| `trip_duration_minutes` | `double` | Dropoff minus pickup in minutes | Duration prediction target; never an input |

Do not use either target to construct features, filters, encoders, normalizers, or missing-value rules for the other model. Training rows may be selected according to an approved target-specific policy, but the target value itself must not be available to the feature-building code.

## B. Allowed pre-trip candidate features

These are candidates, not an instruction to use every field. Member 2 must confirm that each value is present in the serving or request record at prediction time.

| Exact column | Data type/category | Why it can be known before trip start | Intended model |
|---|---|---|---|
| `provider_code` | `int64`; categorical code | The provider or dispatch source can be assigned before a trip begins. | Fare and duration |
| `pickup_hour` | `int8`; cyclical/categorical time feature | Derived from the pickup/request time, which is available at prediction time. | Fare and duration |
| `day_of_week` | `large_string`; categorical | Derived from the pickup/request date. | Fare and duration |
| `month` | `int8`; categorical or ordered time feature | Derived from the pickup/request date. | Fare and duration |
| `weekend` | `bool` | Derived from the pickup/request date; no completed-trip information is needed. | Fare and duration |
| `pickup_date` | `date32[day]`; date/calendar feature | The planned or requested pickup date is known before the trip starts. Use only the calendar information needed by the model; do not use it as a proxy for file order. | Fare and duration |
| `origin_loc_id` | `int64`; categorical location ID | The requested or dispatch pickup location is known before departure. | Fare and duration |
| `dest_loc_id` | `int64`; categorical location ID | The requested destination is known before departure when the trip is booked or dispatched with a destination. | Fare and duration |
| `pickup_borough_name` | `large_string`; categorical location label | Derived from the pre-trip origin location. Use only if the same reference lookup is available at serving time. | Fare and duration |
| `pickup_zone_name` | `large_string`; categorical location label | Derived from the pre-trip origin location. | Fare and duration |
| `pickup_service_zone` | `large_string`; categorical location label | Derived from the pre-trip origin location. | Fare and duration |
| `dropoff_borough_name` | `large_string`; categorical location label | Derived from the pre-trip destination location. | Fare and duration |
| `dropoff_zone_name` | `large_string`; categorical location label | Derived from the pre-trip destination location. | Fare and duration |
| `dropoff_service_zone` | `large_string`; categorical location label | Derived from the pre-trip destination location. | Fare and duration |
| `route_id` | `large_string`; categorical route ID | Concatenation of the origin and destination IDs; safe only when both locations are known before departure. It must not encode any completed-trip aggregate. | Fare and duration |

`pickup_timestamp` is not recommended as a raw model feature. It may be used to reproduce the safe calendar features above, provided the timestamp is the request/planned pickup time available before the trip starts and not a post hoc event timestamp.

### Conditional features

The following fields may be used only after the stated availability assumption is explicitly approved and enforced in the prediction pipeline:

| Exact column | Data type/category | Required assumption | Intended model |
|---|---|---|---|
| `distance_miles` | `double`; numeric | **Assumption required:** this is an upfront route estimate or requested distance available before departure, not GPS/measured distance calculated after completion. If it is only recorded actual distance, forbid it. | Fare and duration |
| `rider_count` | `double`; numeric/count | **Assumption required:** this is the rider count supplied at booking or dispatch. If it is recorded by the provider after the trip, forbid it. Zero and missing values retain their source meaning; no imputation is approved here. | Fare and duration |
| `rate_class_id` | `double`; categorical code | **Assumption required:** the rate class is selected or known before the trip begins. If assigned after settlement, forbid it. | Fare and duration |
| `fare_settlement_method` | `int64`; categorical code | **Assumption required:** the payment/settlement method is selected before departure. If it describes post-trip settlement, forbid it. | Fare only; duration only if independently available pre-trip |
| `offline_record_flag` | `large_string`; categorical flag | **Assumption required:** the operational mode is known before departure. If it indicates that a completed trip was later uploaded or processed offline, forbid it. | Fare and duration only if pre-trip |

No imputation, recoding, or semantic interpretation of the numeric codes is approved by this contract. Unknown code meanings require confirmation from the competition documentation.

## C. Derived time and location features

The following derived features are safe when generated exclusively from pre-trip inputs:

- `pickup_hour`: pickup/request hour, 0-23.
- `day_of_week`: pickup/request weekday.
- `month`: pickup/request calendar month.
- `weekend`: pickup/request Saturday/Sunday indicator.
- `pickup_date`: pickup/request calendar date, subject to the same timing rule.
- `origin_loc_id`, `dest_loc_id`: requested origin and destination IDs.
- `pickup_borough_name`, `pickup_zone_name`, `pickup_service_zone`: labels looked up from the origin ID.
- `dropoff_borough_name`, `dropoff_zone_name`, `dropoff_service_zone`: labels looked up from the destination ID.
- `route_id`: deterministic origin-destination label, only when both endpoints are known before departure.

Do not calculate historical averages, target encodings, route statistics, or location statistics using the full dataset before a leakage-safe training split. Any aggregate encoding must be fit on training data only and applied to validation/test data without using their targets.

## D. Forbidden leakage fields

The following exact columns exist in the processed dataset but are forbidden as model inputs for these targets unless a separate review changes the contract. The reason is that they are targets, completed-trip outcomes, post-trip charges, post-trip audit results, or provenance rather than pre-trip information.

| Exact column(s) | Why forbidden |
|---|---|
| `base_fare` | It is the fare prediction target and would make fare prediction circular. It is also not an input to duration prediction. |
| `trip_duration_minutes` | It is the duration prediction target and is calculated from pickup and dropoff timestamps. |
| `speed_mph` | Calculated from completed-trip distance and duration; it requires post-trip information and directly leaks duration. |
| `dropoff_timestamp` | Known only when the trip finishes; it directly reveals elapsed time and leaks the duration target. |
| `charge_total` | Final settled charge is known after the trip and may include post-trip components; it leaks fare information. |
| `driver_tip_payment` | Tip is selected or recorded after the service and is part of completed-trip payment information. |
| `toll_total` | Actual tolls incurred during the trip are post-trip or route-completion information. |
| `surcharge_misc` | Recorded surcharge components may be assessed during or after the trip; use only a separately documented pre-trip quote, not this completed-trip field. |
| `transit_tax` | Completed-trip tax component; not a pre-trip feature as stored. |
| `service_improvement_fee` | Post-trip charge component as stored. |
| `zone_congestion_fee` | Stored charge component and known missingness; do not assume the completed-trip fee was known before departure. |
| `Airport_fee` | Stored final charge component; do not use the completed-trip value as a pre-trip airport indicator. Use a documented origin/destination location feature instead. |
| `congestion_relief_fee` | Stored post-trip fee component. |
| `pickup_timestamp` and `dropoff_timestamp` as raw unrestricted timestamps | `dropoff_timestamp` is post-trip; raw timestamps can also encode realized event timing. Use only the pre-trip pickup/request time to derive the approved calendar features. |
| `audit_zero_distance_nonzero_fare` | Audit outcome uses fare and distance observations, including target-related information; it is not a raw pre-trip input. |
| `audit_zero_riders` | Audit outcome derived from the recorded rider count; use `rider_count` only under the conditional assumption above. |
| `audit_speed_80_to_100` | Derived from completed-trip speed and therefore leaks duration/distance outcomes. |
| `audit_pickup_outside_source_month` | Post hoc source-file/date consistency outcome, not a serving-time feature. |
| `audit_dropoff_outside_source_month` | Uses the completed dropoff timestamp and is directly post-trip. |
| `audit_boundary_category` | Post hoc classification based on timestamp relationships, including dropoff timing. |
| `audit_pickup_incomplete_zone_labels` | Data-quality outcome from the processed reference join, not a trip request attribute. Use the actual pre-trip location or documented missingness handling instead. |
| `audit_dropoff_incomplete_zone_labels` | Data-quality outcome from the processed reference join, not a trip request attribute. |
| `source_file` | Dataset provenance and source-month proxy; it can encode collection or split artifacts rather than trip information available at serving time. |
| `source_month` | File membership/provenance, not necessarily the requested trip month; using it can create artificial temporal or source leakage. |
| `source_row_1based` | Row position in the source file; it contains no legitimate pre-trip signal and can encode ordering artifacts. |

The following conditional fields are also forbidden whenever their stored value is known only after completion: `distance_miles`, `rider_count`, `rate_class_id`, `fare_settlement_method`, and `offline_record_flag`. The availability assumption must be tested in the data collection and serving process, not inferred from the column name.

## E. Missing-value notes

The processed schema contains known missingness in these fields:

| Column | Note | Contract treatment |
|---|---|---|
| `rider_count` | Missing values were observed in the source audit; zero is also an observed value. | Conditional feature only. Do not equate missing with zero and do not invent an imputation rule here. |
| `rate_class_id` | Missing values were observed, along with documented code values requiring interpretation. | Conditional feature only. Preserve missingness unless a separately approved policy exists. |
| `offline_record_flag` | Missing values were observed. | Conditional feature only if pre-trip operational status is documented; otherwise forbidden. No imputation rule is approved. |
| `zone_congestion_fee` | Missing values were observed; the field is a stored fee component. | Forbidden as stored post-trip charge. Do not impute it as a location feature. |
| `Airport_fee` | Missing values were observed; the field is a stored fee component. | Forbidden as stored post-trip charge. Use documented location fields instead of reconstructing this fee. |
| `pickup_borough_name`, `pickup_zone_name`, `pickup_service_zone`, `dropoff_borough_name`, `dropoff_zone_name`, `dropoff_service_zone` | Reference labels may be incomplete for specific location IDs. | Allowed only when the reference lookup is available pre-trip. Preserve missingness or use an approved category; no imputation is defined here. |

Missingness indicators must themselves satisfy the same timing rule. An indicator that a pre-trip request field was missing may be allowed; an indicator derived from a post-trip charge or audit result is forbidden.

## F. Final feature decision table

| Column | Allowed for Fare | Allowed for Duration | Reason |
|---|---:|---:|---|
| `provider_code` | Yes | Yes | Provider/dispatch assignment can be known before start. |
| `pickup_hour` | Yes | Yes | Derived from pre-trip pickup/request time. |
| `day_of_week` | Yes | Yes | Derived from pre-trip pickup/request date. |
| `month` | Yes | Yes | Derived from pre-trip pickup/request date. |
| `weekend` | Yes | Yes | Derived from pre-trip pickup/request date. |
| `pickup_date` | Yes | Yes | Calendar date is available before start; use carefully to avoid date-order artifacts. |
| `origin_loc_id` | Yes | Yes | Requested origin is pre-trip. |
| `dest_loc_id` | Yes | Yes | Requested destination is pre-trip when supplied at booking. |
| `pickup_borough_name` | Yes | Yes | Pre-trip lookup from origin, if available at serving time. |
| `pickup_zone_name` | Yes | Yes | Pre-trip lookup from origin, if available at serving time. |
| `pickup_service_zone` | Yes | Yes | Pre-trip lookup from origin, if available at serving time. |
| `dropoff_borough_name` | Yes | Yes | Pre-trip lookup from destination, if destination is known. |
| `dropoff_zone_name` | Yes | Yes | Pre-trip lookup from destination, if destination is known. |
| `dropoff_service_zone` | Yes | Yes | Pre-trip lookup from destination, if destination is known. |
| `route_id` | Yes | Yes | Safe deterministic combination of pre-trip origin and destination. |
| `distance_miles` | Conditional | Conditional | Allowed only if it is an upfront route estimate, never actual completed distance. |
| `rider_count` | Conditional | Conditional | Allowed only if supplied at booking/dispatch; preserve missingness and zero semantics. |
| `rate_class_id` | Conditional | Conditional | Allowed only if selected before departure. |
| `fare_settlement_method` | Conditional | Conditional | Allowed only if selected before departure; more naturally fare-related. |
| `offline_record_flag` | Conditional | Conditional | Allowed only if known before departure; otherwise it describes later processing. |
| `base_fare` | No | No | Target and completed fare value. |
| `trip_duration_minutes` | No | No | Target and completed-trip calculation. |
| `speed_mph` | No | No | Derived from completed-trip outcomes. |
| `dropoff_timestamp` | No | No | Post-trip timestamp and direct duration leakage. |
| `charge_total` | No | No | Final settled charge. |
| `driver_tip_payment` | No | No | Post-trip tip. |
| `toll_total` | No | No | Actual completed-trip tolls. |
| `surcharge_misc` | No | No | Stored completed-trip charge component. |
| `transit_tax` | No | No | Stored completed-trip charge component. |
| `service_improvement_fee` | No | No | Stored completed-trip charge component. |
| `zone_congestion_fee` | No | No | Stored completed-trip fee and missing value. |
| `Airport_fee` | No | No | Stored completed-trip fee. |
| `congestion_relief_fee` | No | No | Stored completed-trip fee. |
| `pickup_timestamp` | No as raw; derive approved calendar fields only | No as raw; derive approved calendar fields only | Raw event timestamp must represent an available pre-trip request time; do not use unrestricted timestamp values. |
| `source_file` | No | No | Provenance/source artifact. |
| `source_month` | No | No | Provenance/file membership. |
| `source_row_1based` | No | No | Source row-order artifact. |
| `audit_zero_distance_nonzero_fare` | No | No | Post hoc target/data-quality audit. |
| `audit_zero_riders` | No | No | Post hoc audit outcome. |
| `audit_speed_80_to_100` | No | No | Post hoc speed outcome. |
| `audit_pickup_outside_source_month` | No | No | Post hoc source/date audit. |
| `audit_dropoff_outside_source_month` | No | No | Post hoc dropoff/date audit. |
| `audit_boundary_category` | No | No | Post hoc timestamp classification. |
| `audit_pickup_incomplete_zone_labels` | No | No | Post hoc reference-data quality outcome. |
| `audit_dropoff_incomplete_zone_labels` | No | No | Post hoc reference-data quality outcome. |

## Step 8 boundary

This document defines features only. It does not create train/validation/test splits, modify `clean_trips.parquet`, apply imputation, train models, or start Step 9. Before modelling, Member 2 must verify that every selected feature is available in the intended pre-trip serving record and that any target encoding or aggregate feature is fit using training data only.
