# Member 2 Fare Prediction Handover

## A. Objective

Predict `base_fare` before the trip starts. The model must use only information available at prediction time.

## B. Final model

`LinearRegression` inside a scikit-learn `Pipeline`, with preprocessing contained inside the pipeline.

The route-estimate configuration is the selected model when the distance-availability assumption below is satisfied. The strict pre-trip configuration without distance remains the fallback when no reliable pre-trip estimate exists.

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

Target: `base_fare`.

## D. Preprocessing

- Numeric missing values: `SimpleImputer(strategy="median")`
- Categorical missing values: `SimpleImputer(strategy="most_frequent")`
- Categorical encoding: `OneHotEncoder(handle_unknown="ignore")`
- Numeric and categorical branches: `ColumnTransformer`
- Preprocessing and `LinearRegression`: one scikit-learn `Pipeline`

## E. Validation results

| MAE | RMSE | R² | Rows |
|---:|---:|---:|---:|
| 5.737909 | 10.986343 | 0.643793 | 6,814,901 |

## F. Final test results

| MAE | RMSE | R² | Rows |
|---:|---:|---:|---:|
| 5.571799 | 10.324520 | 0.676153 | 6,730,257 |

The test split was opened once and streamed once for the final evaluation. No model or feature changes were made after observing these metrics.

## G. Training data used

- 445,000 deterministically sampled train rows
- 97,500 deterministically sampled validation rows
- 542,500 total final-training rows

The sampling method selected up to 2,500 evenly spaced positions from every Parquet row group. The final model was not fitted on all 38.8 million train-plus-validation rows.

## H. Model comparisons

| Model | MAE | RMSE | R² |
|---|---:|---:|---:|
| Median baseline | 11.713890 | 19.724010 | -0.148117 |
| LinearRegression without distance | 8.689478 | 13.928211 | 0.427485 |
| RandomForestRegressor | 9.209341 | 14.128331 | 0.410915 |
| ExtraTreesRegressor | 9.106238 | 14.121436 | 0.411490 |
| LinearRegression with conditional distance | 5.737909 | 10.986343 | 0.643793 |

LinearRegression was selected because the conditional-distance configuration produced the lowest validation MAE and RMSE and the highest validation R². Random Forest and Extra Trees did not beat strict LinearRegression in the fixed first-pass comparison and were not tuned.

## I. Feature experiments

- `route_id` was excluded because one-hot encoding produced 22,392 encoded features, exceeding the experiment's 5,000-feature safety limit. The route-inclusive model was not fitted.
- Adding `distance_miles` reduced validation MAE by 2.951569 (33.967%) and RMSE by 2.941868 (21.122%), while increasing R² from 0.427485 to 0.643793.

## J. Important limitation

`distance_miles` is valid only if it represents an estimated route distance available before departure. Completed-trip mileage must not be treated as a pre-trip feature. The stored distance was an experimental proxy, and performance must be checked with the actual production route estimator.

If a reliable pre-trip estimate is unavailable, use the strict seven-feature LinearRegression configuration without distance.

## K. Output artifacts

- `models/fare_pipeline.pkl` — fitted preprocessing and `LinearRegression` pipeline; 9,580 bytes.
- `notebooks/02_FarePrediction.ipynb`
- `reports/figures/fare_predicted_vs_actual.png`
- `reports/figures/fare_residual_distribution.png`
- `reports/figures/fare_mae_by_hour.png`
- `reports/figures/fare_mae_by_distance_bucket.png`

## Serialization verification

The final serialized pipeline was recreated deterministically from the documented 542,500-row train-plus-validation sample because the fitted in-memory Step 11 object was no longer available. The test set was not accessed during serialization.

The recreated fit used the exact Step 11 sampling logic: up to 2,500 evenly spaced row positions from each Parquet row group using `numpy.linspace(..., dtype=int64)`. Counts were verified before fitting: 445,000 train rows, 97,500 validation rows, and 542,500 total rows. The serialization-only fit took 9.559 seconds.

`joblib.load()` successfully reloaded `models/fare_pipeline.pkl`. The loaded object is a scikit-learn `Pipeline` with named steps `preprocessor` and `model`; the preprocessor is a `ColumnTransformer`, and the model is `LinearRegression`. Five training-sample predictions were numeric and finite, and matched the predictions made before serialization exactly.
