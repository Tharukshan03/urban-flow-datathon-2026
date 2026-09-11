"""Load and validate the small immutable dashboard reporting snapshot."""
from pathlib import Path
import hashlib
import json
import re

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).parents[1] / 'data'
TABLES = {
    'pickups': 'member3_pickup_zone_totals.csv',
    'destinations': 'member3_dropoff_zone_totals.csv',
    'boroughs': 'member3_pickup_borough_totals.csv',
    'hours': 'member3_demand_by_hour.csv',
    'weekdays': 'member3_demand_by_weekday.csv',
    'od': 'member3_od_zone_pairs.csv',
    'borough_od': 'member3_od_borough_pairs.csv',
    'time_od': 'member3_od_zone_time_top.csv',
    'borough_time_od': 'member3_od_borough_time.csv',
    'zone_time': 'member3_spatial_pickup_by_time.csv',
    'time_summary': 'member3_spatial_time_summary.csv',
    'metrics': 'member3_forecast_metrics.csv',
    **{f'forecast_{h}': f'forecast_{h}h.csv' for h in (24, 48, 72)},
}
WINDOWS = {
    'morning_peak': 'Morning · 06:00–10:00', 'midday': 'Midday · 10:00–16:00',
    'evening_peak': 'Evening · 16:00–20:00', 'late_night': 'Late night · 20:00–06:00',
}
MODEL_NAMES = {'baseline': 'Seasonal baseline', 'improved': 'Gradient boosting'}


class DataError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise DataError(message)


def load_data(directory=DATA_DIR):
    directory = Path(directory)
    required = [*TABLES.values(), 'manifest.json', 'demand_spatial_findings.md']
    missing = [name for name in required if not (directory/name).is_file()]
    if missing:
        raise DataError('Missing dashboard inputs: '+', '.join(missing)+'. Restore dashboard/data from the repository snapshot; no trip-data rebuild is needed.')
    manifest = json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
    require(manifest['source_commit'] == '8b3cdee641b59d27ff4ce9cd037bd5e46ccd7096', 'Unexpected source commit in dashboard manifest.')
    require({e['file'] for e in manifest['files']} == set(required)-{'manifest.json'}, 'Snapshot manifest does not match required reporting files.')
    for entry in manifest['files']:
        payload = (directory/entry['file']).read_bytes()
        require(hashlib.sha256(payload).hexdigest() == entry['sha256'], f"Snapshot checksum mismatch: {entry['file']}. Restore the unchanged reporting snapshot.")
    data = {key: pd.read_csv(directory/name) for key, name in TABLES.items()}
    total = int(data['pickups'].pickup_count.sum())
    require(total == 45_533_334, 'Unexpected retained-trip total.')
    for key, column in [('destinations','dropoff_count'), ('boroughs','pickup_count'),
                        ('hours','pickup_count'), ('weekdays','pickup_count'),
                        ('borough_od','trip_count'), ('borough_time_od','trip_count'),
                        ('zone_time','trip_count'), ('time_summary','trip_count')]:
        require(data[key][column].sum() == total, f'{key} totals do not reconcile.')
    tests = data['metrics'].loc[data['metrics'].split.eq('test')].sort_values('horizon_hours')
    require(tests.horizon_hours.tolist() == [24,48,72], 'Expected one test metric row per horizon.')
    for h in (24,48,72):
        f = data[f'forecast_{h}']
        for name in ('pickup_hour','forecast_origin'):
            f[name] = pd.to_datetime(f[name], errors='raise')
        require(len(f) == h*10 and f.pickup_zone_name.nunique()==10, f'Incomplete {h}h forecast.')
        require(f.pickup_hour.is_monotonic_increasing and not f.duplicated(['pickup_hour','pickup_zone_name']).any(), 'Invalid forecast ordering or duplicate zone-hours.')
        require(f.forecast_origin.eq(pd.Timestamp('2026-04-01')).all(), 'Unexpected saved forecast origin.')
        expected = pd.date_range('2026-04-01', periods=h, freq='h')
        require(all(pd.DatetimeIndex(group.pickup_hour).equals(expected) for _,group in f.groupby('pickup_zone_name')), 'Incomplete saved forecast time grid.')
        require(np.isfinite(f[['baseline_forecast','improved_forecast']]).all().all(), 'Non-finite forecast value.')
    report = (directory/'demand_spatial_findings.md').read_text(encoding='utf-8')
    section = report.split('## 7. Operational recommendations\n', 1)[1].split('\n## Member 3 completion summary',1)[0]
    recommendations = [s.strip() for s in re.findall(r'(?ms)^\d+\.\s+(.*?)(?=^\d+\.\s+|\Z)', section)]
    require(len(recommendations)==5, 'Expected five source recommendations.')
    data.update(total=total, test_metrics=tests, recommendations=recommendations, report=report, manifest=manifest)
    return data


def preferred_model(metric_row):
    return 'improved' if metric_row.improved_mae < metric_row.baseline_mae else 'baseline'


def route_view(data, bucket):
    """Bundled top-pair summaries do not contain every possible route."""
    if bucket == 'All day':
        return data['od'].copy(), 'Top 100 directed pairs across the full year'
    return data['time_od'].loc[data['time_od'].time_bucket.eq(bucket)].copy(), 'Top 25 directed pairs within this time window'
