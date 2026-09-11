# Member 2 Duration Prediction Handover

## A. Objective

Predict `trip_duration_minutes` before trip start.

## B. Final model

`LinearRegression` inside an sklearn `Pipeline`, using the route-estimate configuration.

## C. Final features

Numeric:

- `pickup_hour`
- `month`
- `distance_miles`

Categorical:

- `provider_code`
- `day_of_week`
- `weekend`
- `origin_loc_id`
- `dest_loc_id`

## D. Preprocessing

- Median numeric imputation
- Most-frequent categorical imputation
- `OneHotEncoder(handle_unknown="ignore")`
- `ColumnTransformer`

## E. Validation results

- MAE: 6.367238 minutes
- RMSE: 23.700579 minutes
- R²: 0.177008
- Rows: 6,814,901

## F. Test results

- MAE: 5.802654 minutes
- RMSE: 22.259013 minutes
- R²: 0.206474
- Rows: 6,730,257

The duration test split was evaluated once after model selection. No modelling decision changed afterward.

## G. Training data used

- Sampled train rows: 445,000
- Sampled validation rows: 97,500
- Total final-training rows: 542,500
- Final training time: 5.472 seconds

## H. Model comparisons

| Model | Validation MAE | Validation RMSE | Validation R² | Training Time |
|---|---:|---:|---:|---:|
| Median baseline | 9.756819 | 26.446473 | -0.024739 | n/a |
| LinearRegression without distance | 8.566630 | 24.971912 | 0.086347 | 3.630s |
| RandomForestRegressor | 8.708620 | 25.046847 | 0.080855 | 152.079s |
| ExtraTreesRegressor | 8.696595 | 25.090268 | 0.077666 | 144.491s |
| LinearRegression with conditional distance | 6.367238 | 23.700579 | 0.177008 | 4.286s |

## I. Feature experiments

- `route_id` was excluded because one-hot preprocessing produced 22,392 encoded features, exceeding the 5,000-feature safety threshold.
- Conditional `distance_miles` improved validation MAE by 2.199392 minutes (25.674%) and RMSE by 1.271333 minutes (5.091%).

## J. Error analysis

### MAE by pickup hour

| Pickup hour | MAE (minutes) |
|---|---:|
| 00:00 | 5.330875 |
| 01:00 | 4.946503 |
| 02:00 | 4.798572 |
| 03:00 | 5.123812 |
| 04:00 | 7.120411 |
| 05:00 | 8.602170 |
| 06:00 | 8.450204 |
| 07:00 | 7.502794 |
| 08:00 | 6.754376 |
| 09:00 | 6.459382 |
| 10:00 | 6.306112 |
| 11:00 | 6.340954 |
| 12:00 | 6.335752 |
| 13:00 | 6.289624 |
| 14:00 | 6.615331 |
| 15:00 | 7.071030 |
| 16:00 | 7.748571 |
| 17:00 | 7.209050 |
| 18:00 | 6.288214 |
| 19:00 | 5.691292 |
| 20:00 | 5.303603 |
| 21:00 | 5.392191 |
| 22:00 | 5.705263 |
| 23:00 | 6.231215 |

Lowest hourly MAE occurred at 2:00 (4.798572 minutes); highest occurred at 5:00 (8.602170 minutes).

### MAE by estimated distance

| Distance bucket | MAE (minutes) |
|---|---:|
| 0–2 miles | 5.028460 |
| 2–5 miles | 5.707983 |
| 5–10 miles | 8.448617 |
| 10–20 miles | 14.183513 |
| 20+ miles | 22.991634 |

The strongest distance bucket was 0–2 miles; the weakest was 20+ miles.

### Long-duration observations

- p50: 14.000000 minutes
- p90: 33.883333 minutes
- p95: 44.600000 minutes
- p99: 74.833333 minutes
- p99.5: 88.833333 minutes
- p99.9: 129.350000 minutes
- Maximum: 8611.866667 minutes
- Trips over 120 minutes: 9,158 (0.134382%)

These observations were retained unchanged. Their large residuals strongly influence RMSE.

## K. Important limitations

- `distance_miles` is valid only when it represents an estimated route distance available before departure. Completed-trip mileage must not be treated as a pre-trip input.
- Long-duration outliers strongly affect RMSE.
- Traffic, congestion, weather, incidents, and road conditions are not represented by the current pre-trip features.

## L. Output artifacts

- `models/duration_pipeline.pkl`
- `notebooks/03_DurationPrediction.ipynb`
- `reports/figures/duration_predicted_vs_actual.png`
- `reports/figures/duration_residual_distribution.png`
- `reports/figures/duration_mae_by_hour.png`
- `reports/figures/duration_mae_by_distance_bucket.png`
