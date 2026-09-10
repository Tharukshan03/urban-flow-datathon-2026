"""Phase 3: chronological, recursive demand forecasts from Phase 2 aggregates."""
from pathlib import Path
import json
import time

import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

INPUT = Path('data/processed/member3_top_zone_hourly.parquet')
TRAIN_END = pd.Timestamp('2025-12-11')
TEST_START = pd.Timestamp('2026-02-05')
MISSING_HOUR = pd.Timestamp('2026-03-08 02:00:00')
FEATURES = ['lag_1', 'lag_24', 'lag_48', 'lag_168', 'rolling_mean_3h',
            'rolling_mean_24h', 'hour', 'weekday', 'is_weekend', 'zone_code']


def load_data():
    data = pd.read_parquet(INPUT)
    ranking = pd.read_csv('reports/member3_top_zones.csv').sort_values('rank')
    assert len(data) == 87_600 and len(ranking) == 10, 'STOP: input size mismatch'
    assert data['filled_zero'].sum() == 718, 'STOP: zero-fill mismatch'
    assert not data.duplicated(['pickup_hour', 'pickup_zone_name']).any(), 'STOP: duplicate zone-hours'
    assert data['pickup_count'].notna().all() and data['pickup_count'].ge(0).all(), 'STOP: invalid demand'
    assert data.loc[data.filled_zero, 'pickup_count'].eq(0).all(), 'STOP: zero-fill values mismatch'
    zones = ranking.pickup_zone_name.tolist()
    assert set(data.pickup_zone_name) == set(zones), 'STOP: zone mismatch'
    wide = data.pivot(index='pickup_hour', columns='pickup_zone_name', values='pickup_count').sort_index()[zones]
    expected = pd.date_range('2025-04-01', '2026-03-31 23:00:00', freq='h')
    assert wide.index.equals(expected) and not wide.isna().any().any(), 'STOP: incomplete time grid'
    assert wide.sum().to_numpy().tolist() == ranking.pickup_count.tolist(), 'STOP: ranking totals mismatch'
    assert wide.loc[MISSING_HOUR].eq(0).all(), 'STOP: documented missing-hour mismatch'
    print(f'Validated compact input: {len(data):,} rows, {len(zones)} zones, {len(wide):,} consecutive hours.')
    return wide


def feature_frame(wide):
    frames = []
    for code, zone in enumerate(wide.columns):
        y = wide[zone]
        f = pd.DataFrame(index=wide.index)
        for lag in (1, 24, 48, 168):
            f[f'lag_{lag}'] = y.shift(lag)
        for window in (3, 24):
            f[f'rolling_mean_{window}h'] = y.shift(1).rolling(window).mean()
        f['hour'] = f.index.hour
        f['weekday'] = f.index.dayofweek
        f['is_weekend'] = (f.index.dayofweek >= 5).astype(int)
        f['zone_code'] = code
        f['target'] = y
        frames.append(f)
    return pd.concat(frames).dropna().sort_index(kind='stable')


def fit(wide, frame, cutoff):
    train = frame.loc[frame.index < cutoff]
    assert train.index.max() < cutoff
    model = HistGradientBoostingRegressor(
        learning_rate=0.08, max_iter=120, max_leaf_nodes=15,
        min_samples_leaf=30, l2_regularization=1.0,
        categorical_features=[False] * 9 + [True],
        early_stopping=False, random_state=2026,
    )
    with threadpool_limits(limits=2):
        model.fit(train[FEATURES].to_numpy(), train.target.to_numpy())
    history = wide.loc[wide.index < cutoff]
    seasonal = history.groupby([history.index.dayofweek, history.index.hour]).mean()
    assert len(seasonal) == 168, 'STOP: incomplete baseline weekday/hour groups'
    print(f'Fit through {history.index.max()}: {len(train):,} lag-feature rows.')
    return model, seasonal


def recursive_path(model, history, dates):
    """Accept ONLY pre-origin observations; append predictions after the origin."""
    assert len(history) >= 168
    state = np.vstack([np.asarray(history[-168:], dtype=float), np.zeros((len(dates), history.shape[1]))])
    result = []
    for step, stamp in enumerate(dates):
        end = 168 + step
        n = history.shape[1]
        x = np.column_stack([
            state[end-1], state[end-24], state[end-48], state[end-168],
            state[end-3:end].mean(axis=0), state[end-24:end].mean(axis=0),
            np.full(n, stamp.hour), np.full(n, stamp.dayofweek),
            np.full(n, int(stamp.dayofweek >= 5)), np.arange(n),
        ])
        prediction = np.maximum(model.predict(x), 0.0)
        state[end] = prediction
        result.append(prediction)
    return np.asarray(result)


def baseline_path(seasonal, dates):
    return np.vstack([seasonal.loc[(d.dayofweek, d.hour)].to_numpy() for d in dates])


def backtest(wide, model, seasonal, start, end, split):
    # Common daily origins for every horizon, with the entire 72h target window inside the split.
    origins = pd.date_range(start, end - pd.Timedelta(hours=72), freq='24h')
    results = []
    with threadpool_limits(limits=2):
        for origin in origins:
            dates = pd.date_range(origin, periods=72, freq='h')
            past = wide.loc[wide.index < origin].to_numpy()
            improved = recursive_path(model, past, dates)
            baseline = baseline_path(seasonal, dates)
            actual = wide.loc[dates].to_numpy()
            results.append(pd.DataFrame({
                'split': split, 'forecast_origin': origin,
                'pickup_hour': np.repeat(dates.to_numpy(), len(wide.columns)),
                'pickup_zone_name': np.tile(wide.columns.to_numpy(), 72),
                'lead_hour': np.repeat(np.arange(1, 73), len(wide.columns)),
                'actual': actual.ravel(), 'baseline_forecast': baseline.ravel(),
                'improved_forecast': improved.ravel(),
            }))
    print(f'{split}: {len(origins)} daily origins, {origins.min()} through {origins.max()}.')
    return pd.concat(results, ignore_index=True)


def score(backtests):
    rows = []
    for split, group in backtests.groupby('split', sort=False):
        for horizon in (24, 48, 72):
            block = group.loc[group.lead_hour <= horizon]
            row = {'split': split, 'horizon_hours': horizon, 'n_predictions': len(block),
                   'n_origins': block.forecast_origin.nunique()}
            for label in ('baseline', 'improved'):
                error = block[f'{label}_forecast'] - block.actual
                row[f'{label}_mae'] = float(error.abs().mean())
                row[f'{label}_rmse'] = float(np.sqrt(np.mean(error.to_numpy() ** 2)))
            row['winner'] = ('Improved' if row['improved_mae'] < row['baseline_mae'] else
                             'Baseline' if row['baseline_mae'] < row['improved_mae'] else 'Tie')
            rows.append(row)
    return pd.DataFrame(rows)


def evaluate(wide):
    started = time.perf_counter()
    frame = feature_frame(wide)
    model, seasonal = fit(wide, frame, TRAIN_END)
    validation = backtest(wide, model, seasonal, TRAIN_END, TEST_START, 'validation')
    print(score(validation).to_string(index=False, float_format=lambda x: f'{x:.9f}'))
    # Configuration was fixed in advance; no test-based tuning or random early-stopping split.
    model, seasonal = fit(wide, frame, TEST_START)
    test = backtest(wide, model, seasonal, TEST_START, wide.index.max()+pd.Timedelta(hours=1), 'test')
    backtests = pd.concat([validation, test], ignore_index=True)
    metrics = score(backtests)
    print(metrics.loc[metrics.split.eq('test')].to_string(index=False, float_format=lambda x: f'{x:.9f}'))
    return frame, backtests, metrics, time.perf_counter() - started


def save_outputs(wide, frame, backtests, metrics, evaluation_seconds):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    reports = Path('reports')
    figures = reports / 'figures'
    figures.mkdir(exist_ok=True)
    metrics.to_csv(reports / 'member3_forecast_metrics.csv', index=False)
    sensitivity = score(backtests.loc[backtests.pickup_hour.ne(MISSING_HOUR)])
    sensitivity.to_csv(reports / 'member3_forecast_metrics_excluding_missing_hour.csv', index=False)
    backtests.to_parquet('data/processed/member3_forecast_backtest.parquet', index=False, compression='zstd')

    test = backtests.loc[backtests.split.eq('test')]
    origin = test.forecast_origin.max()
    example = test.loc[test.forecast_origin.eq(origin)].groupby('pickup_hour')[['actual', 'baseline_forecast', 'improved_forecast']].sum()
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), constrained_layout=True)
    for ax, horizon in zip(axes, (24, 48, 72)):
        view = example.iloc[:horizon]
        for column, label, color in [('actual', 'Observed', '#263238'), ('baseline_forecast', 'Seasonal mean', '#D97706'), ('improved_forecast', 'Gradient boosting', '#007C91')]:
            ax.plot(view.index, view[column], label=label, color=color, linewidth=1.7)
        ax.set_title(f'{horizon}-hour path — aggregate of the fixed top 10 zones', loc='left')
        ax.set_ylabel('Pickups / hour')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d\n%H:%M'))
        ax.grid(alpha=0.2)
    axes[0].legend(ncol=3)
    fig.suptitle(f'Held-out test example: forecast starts {origin:%Y-%m-%d %H:%M}\nMetrics are computed per zone-hour across all daily test origins', fontsize=13)
    fig.savefig(figures / 'demand_forecast.png', dpi=150)
    plt.close(fig)

    origin = wide.index.max() + pd.Timedelta(hours=1)
    model, seasonal = fit(wide, frame, origin)
    dates = pd.date_range(origin, periods=72, freq='h')
    with threadpool_limits(limits=2):
        future = recursive_path(model, wide.to_numpy(), dates)
    baseline = baseline_path(seasonal, dates)
    future_frame = pd.DataFrame({
        'forecast_origin': origin, 'pickup_hour': np.repeat(dates.to_numpy(), 10),
        'pickup_zone_name': np.tile(wide.columns.to_numpy(), 72),
        'lead_hour': np.repeat(np.arange(1, 73), 10),
        'baseline_forecast': baseline.ravel(), 'improved_forecast': future.ravel(),
    })
    inventory = []
    for horizon in (24, 48, 72):
        path = reports / f'forecast_{horizon}h.csv'
        subset = future_frame.loc[future_frame.lead_hour <= horizon]
        subset.to_csv(path, index=False)
        inventory.append({'path': path.as_posix(), 'rows': len(subset), 'bytes': path.stat().st_size})
    summary = {
        'evaluation_seconds': evaluation_seconds, 'sklearn_version': sklearn.__version__,
        'features': FEATURES, 'train_end_exclusive': str(TRAIN_END), 'test_start': str(TEST_START),
        'forecast_start': str(origin), 'forecast_end': str(dates[-1]),
        'metrics': metrics.to_dict(orient='records'), 'forecast_files': inventory,
        'test_missing_hour_sensitivity': sensitivity.loc[sensitivity.split.eq('test')].to_dict(orient='records'),
    }
    (reports / 'member3_forecasting_summary.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(inventory, indent=2))
    print(f'Evaluation runtime: {evaluation_seconds:.1f} seconds. Future forecasts start {origin}.')
    return summary
