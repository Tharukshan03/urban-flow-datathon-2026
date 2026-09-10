"""Safe analytics helpers for the mobility assistant."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import re
from typing import Any

import pandas as pd

from .router import route_question
from .utils import DATA_DIR, join_phrases

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
    'forecast_24': 'forecast_24h.csv',
    'forecast_48': 'forecast_48h.csv',
    'forecast_72': 'forecast_72h.csv',
}

WINDOWS = {
    'morning_peak': 'Morning · 06:00–10:00',
    'midday': 'Midday · 10:00–16:00',
    'evening_peak': 'Evening · 16:00–20:00',
    'late_night': 'Late night · 20:00–06:00',
}

MODEL_NAMES = {
    'baseline': 'Seasonal baseline',
    'improved': 'Gradient boosting',
}


class DataError(ValueError):
    """Raised when the bundled assistant snapshot is missing or altered."""


@dataclass(frozen=True)
class AssistantBundle:
    data_dir: Path
    tables: dict[str, pd.DataFrame]
    report: str
    recommendations: tuple[str, ...]
    manifest: dict[str, Any]
    zone_names: tuple[str, ...]
    borough_names: tuple[str, ...]
    forecast_zones: tuple[str, ...]


@dataclass(frozen=True)
class AssistantAnswer:
    title: str
    body: str
    kind: str
    table: pd.DataFrame | None = None
    suggestions: tuple[str, ...] = ()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DataError(message)


def _load_table(directory: Path, name: str) -> pd.DataFrame:
    return pd.read_csv(directory / name)


def _ranked(frame: pd.DataFrame, label: str, value: str, n: int) -> pd.DataFrame:
    selected = frame.dropna(subset=[label]).sort_values([value, label], ascending=[False, True]).head(n).copy()
    return selected[[label, value]]


def _format_ranking(frame: pd.DataFrame, label: str, value: str, unit: str, n: int) -> str:
    rows = _ranked(frame, label, value, n)
    parts = [f"{row[label]} ({int(row[value]):,} {unit})" for _, row in rows.iterrows()]
    return join_phrases(parts)


def _source_recommendations(report: str) -> tuple[str, ...]:
    section = report.split('## 7. Operational recommendations\n', 1)[1].split('\n## Member 3 completion summary', 1)[0]
    values = [s.strip() for s in re.findall(r'(?ms)^\d+\.\s+(.*?)(?=^\d+\.\s+|\Z)', section)]
    return tuple(values)


def load_bundle(data_dir: Path = DATA_DIR) -> AssistantBundle:
    directory = Path(data_dir)
    manifest_path = directory / 'manifest.json'
    report_path = directory / 'demand_spatial_findings.md'
    required = [*TABLES.values(), 'manifest.json', 'demand_spatial_findings.md']
    missing = [name for name in required if not (directory / name).is_file()]
    if missing:
        raise DataError('Missing assistant inputs: ' + ', '.join(missing) + '. Copy the verified Track 6 bundle into assistant/data.')
    _require(not list(directory.glob('*.parquet')), 'Assistant snapshot must not include parquet files.')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    _require(manifest['source_commit'] == '87289841914a8a45aec18e665d3be51838ea89b4', 'Unexpected source commit in assistant manifest.')
    _require({entry['file'] for entry in manifest['files']} == set(required) - {'manifest.json'}, 'Assistant manifest does not match the required reporting files.')
    for entry in manifest['files']:
        payload = (directory / entry['file']).read_bytes()
        _require(hashlib.sha256(payload).hexdigest() == entry['sha256'], f"Checksum mismatch for {entry['file']}.")
    tables = {key: _load_table(directory, name) for key, name in TABLES.items()}
    total = int(tables['pickups'].pickup_count.sum())
    _require(total == 45_533_334, 'Unexpected retained-trip total in assistant snapshot.')
    for key, column in [
        ('destinations', 'dropoff_count'),
        ('boroughs', 'pickup_count'),
        ('hours', 'pickup_count'),
        ('weekdays', 'pickup_count'),
        ('borough_od', 'trip_count'),
        ('borough_time_od', 'trip_count'),
        ('zone_time', 'trip_count'),
        ('time_summary', 'trip_count'),
    ]:
        _require(int(tables[key][column].sum()) == total, f'{key} totals do not reconcile.')
    tests = tables['metrics'].loc[tables['metrics'].split.eq('test')].sort_values('horizon_hours')
    _require(tests.horizon_hours.tolist() == [24, 48, 72], 'Expected test metrics for 24, 48 and 72 hours.')
    for horizon in (24, 48, 72):
        forecast = tables[f'forecast_{horizon}']
        for name in ('pickup_hour', 'forecast_origin'):
            forecast[name] = pd.to_datetime(forecast[name], errors='raise')
        _require(len(forecast) == horizon * 10 and forecast.pickup_zone_name.nunique() == 10, f'Incomplete {horizon}h forecast bundle.')
        _require(forecast.pickup_hour.is_monotonic_increasing and not forecast.duplicated(['pickup_hour', 'pickup_zone_name']).any(), f'Invalid {horizon}h forecast ordering.')
        _require(forecast.forecast_origin.eq(pd.Timestamp('2026-04-01')).all(), 'Unexpected saved forecast origin.')
        expected = pd.date_range('2026-04-01', periods=horizon, freq='h')
        _require(all(pd.DatetimeIndex(group.pickup_hour).equals(expected) for _, group in forecast.groupby('pickup_zone_name')), f'Incomplete {horizon}h forecast grid.')
    report = report_path.read_text(encoding='utf-8')
    recommendations = _source_recommendations(report)
    _require(len(recommendations) == 5, 'Expected five operational recommendations.')
    zone_names = sorted({
        *tables['pickups'].pickup_zone_name.dropna().astype(str).tolist(),
        *tables['destinations'].dropoff_zone_name.dropna().astype(str).tolist(),
        *tables['od'].pickup_zone_name.dropna().astype(str).tolist(),
        *tables['od'].dropoff_zone_name.dropna().astype(str).tolist(),
        *tables['time_od'].pickup_zone_name.dropna().astype(str).tolist(),
        *tables['time_od'].dropoff_zone_name.dropna().astype(str).tolist(),
        *tables['zone_time'].pickup_zone_name.dropna().astype(str).tolist(),
        *tables['forecast_24'].pickup_zone_name.dropna().astype(str).tolist(),
        *tables['forecast_48'].pickup_zone_name.dropna().astype(str).tolist(),
        *tables['forecast_72'].pickup_zone_name.dropna().astype(str).tolist(),
    })
    borough_names = sorted({
        *tables['boroughs'].pickup_borough_name.dropna().astype(str).tolist(),
        *tables['borough_od'].pickup_borough_name.dropna().astype(str).tolist(),
        *tables['borough_od'].dropoff_borough_name.dropna().astype(str).tolist(),
        *tables['borough_time_od'].pickup_borough_name.dropna().astype(str).tolist(),
        *tables['borough_time_od'].dropoff_borough_name.dropna().astype(str).tolist(),
    })
    forecast_zones = tuple(sorted(tables['forecast_24'].pickup_zone_name.dropna().astype(str).unique().tolist()))
    return AssistantBundle(directory, tables, report, recommendations, manifest, tuple(zone_names), tuple(borough_names), forecast_zones)


def preferred_model(metric_row: pd.Series) -> str:
    return 'improved' if metric_row.improved_mae < metric_row.baseline_mae else 'baseline'


def answer_top_pickups(bundle: AssistantBundle, top_n: int = 5) -> AssistantAnswer:
    table = _ranked(bundle.tables['pickups'], 'pickup_zone_name', 'pickup_count', top_n)
    body = f"The busiest pickup zones are {_format_ranking(bundle.tables['pickups'], 'pickup_zone_name', 'pickup_count', 'retained pickups', top_n)}."
    return AssistantAnswer('Top pickup zones', body, 'ranking', table)


def answer_top_destinations(bundle: AssistantBundle, top_n: int = 5) -> AssistantAnswer:
    table = _ranked(bundle.tables['destinations'], 'dropoff_zone_name', 'dropoff_count', top_n)
    body = f"The busiest destination zones are {_format_ranking(bundle.tables['destinations'], 'dropoff_zone_name', 'dropoff_count', 'retained dropoffs', top_n)}."
    return AssistantAnswer('Top destination zones', body, 'ranking', table)


def answer_borough_demand(bundle: AssistantBundle, borough_name: str | None = None, top_n: int = 5) -> AssistantAnswer:
    frame = bundle.tables['boroughs']
    if borough_name:
        matched = frame.loc[frame.pickup_borough_name.eq(borough_name)]
        if matched.empty:
            return AssistantAnswer('Borough demand', f'I could not find borough demand for {borough_name}.', 'not_found')
        row = matched.sort_values('pickup_count', ascending=False).iloc[0]
        body = f"{borough_name} has {int(row.pickup_count):,} retained pickups in the bundled snapshot."
        return AssistantAnswer('Borough demand', body, 'single', matched[['pickup_borough_name', 'pickup_count']].sort_values('pickup_count', ascending=False).head(top_n))
    top_row = frame.sort_values('pickup_count', ascending=False).iloc[0]
    body = f"{top_row.pickup_borough_name} has the most pickup demand, with {int(top_row.pickup_count):,} retained pickups."
    return AssistantAnswer('Borough demand', body, 'ranking', _ranked(frame, 'pickup_borough_name', 'pickup_count', top_n))


def answer_hourly_demand(bundle: AssistantBundle) -> AssistantAnswer:
    frame = bundle.tables['hours'].copy()
    frame['Mean pickups per day'] = frame.pickup_count / 365
    peak = frame.sort_values('pickup_count', ascending=False).iloc[0]
    body = f"Demand is highest at {int(peak.hour_of_day):02d}:00, with {int(peak.pickup_count):,} retained pickups in the year, or {peak['Mean pickups per day']:.2f} pickups per day."
    return AssistantAnswer('Hourly demand', body, 'single', frame[['hour_of_day', 'pickup_count', 'Mean pickups per day']].sort_values('hour_of_day'))


def answer_weekday_demand(bundle: AssistantBundle) -> AssistantAnswer:
    frame = bundle.tables['weekdays'].sort_values('pickup_count', ascending=False)
    peak = frame.iloc[0]
    body = f"{peak.weekday} has the highest retained demand, with {int(peak.pickup_count):,} pickups."
    return AssistantAnswer('Weekday demand', body, 'single', frame[['weekday', 'pickup_count']])


def _choose_od_frame(bundle: AssistantBundle, time_bucket: str | None) -> pd.DataFrame:
    if time_bucket:
        return bundle.tables['time_od'].loc[bundle.tables['time_od'].time_bucket.eq(time_bucket)].copy()
    return bundle.tables['od'].copy()


def answer_od_overall(bundle: AssistantBundle, top_n: int = 5) -> AssistantAnswer:
    frame = bundle.tables['od'].sort_values('trip_count', ascending=False)
    top = frame.iloc[0]
    body = f"The strongest route is {top.pickup_zone_name} to {top.dropoff_zone_name}, with {int(top.trip_count):,} retained trips."
    display = frame[['pickup_zone_name', 'dropoff_zone_name', 'trip_count']].head(top_n)
    return AssistantAnswer('OD routes', body, 'ranking', display)


def answer_od_from_zone(bundle: AssistantBundle, zone_name: str, time_bucket: str | None = None, top_n: int = 5) -> AssistantAnswer:
    frame = _choose_od_frame(bundle, time_bucket)
    frame = frame.loc[frame.pickup_zone_name.eq(zone_name)]
    if frame.empty:
        return AssistantAnswer('OD routes', f'I could not find any OD routes for {zone_name}.', 'not_found')
    frame = frame.sort_values('trip_count', ascending=False)
    top = frame.iloc[0]
    prefix = f"In the {WINDOWS.get(time_bucket, time_bucket)} window, " if time_bucket else ''
    body = f"{prefix}trips from {zone_name} usually go to {top.dropoff_zone_name}, with {int(top.trip_count):,} retained trips."
    display = frame[['pickup_zone_name', 'dropoff_zone_name', 'trip_count']].head(top_n)
    return AssistantAnswer('OD routes', body, 'ranking', display)


def answer_od_time(bundle: AssistantBundle, time_bucket: str, top_n: int = 5) -> AssistantAnswer:
    frame = bundle.tables['time_od'].loc[bundle.tables['time_od'].time_bucket.eq(time_bucket)].sort_values('trip_count', ascending=False)
    top = frame.iloc[0]
    body = f"The strongest {WINDOWS.get(time_bucket, time_bucket).lower()} route is {top.pickup_zone_name} to {top.dropoff_zone_name}, with {int(top.trip_count):,} retained trips."
    display = frame[['pickup_zone_name', 'dropoff_zone_name', 'trip_count']].head(top_n)
    return AssistantAnswer('OD routes by time window', body, 'ranking', display)


def answer_forecast_metrics(bundle: AssistantBundle, horizon_hours: int) -> AssistantAnswer:
    frame = bundle.tables['metrics'].loc[bundle.tables['metrics'].split.eq('test') & bundle.tables['metrics'].horizon_hours.eq(horizon_hours)]
    if frame.empty:
        return AssistantAnswer('Forecast metrics', f'I could not find forecast metrics for {horizon_hours} hours.', 'not_found')
    row = frame.iloc[0]
    model = preferred_model(row)
    other = 'baseline' if model == 'improved' else 'improved'
    body = (
        f"For {horizon_hours}-hour planning, {MODEL_NAMES[model]} performed better in backtesting, "
        f"with MAE {row[model + '_mae']:.2f} pickups per zone-hour versus {row[other + '_mae']:.2f} for the other method."
    )
    display = frame[['horizon_hours', 'baseline_mae', 'improved_mae', 'baseline_rmse', 'improved_rmse']]
    return AssistantAnswer('Forecast metrics', body, 'metrics', display)


def answer_saved_forecast(bundle: AssistantBundle, horizon_hours: int, zone_name: str | None = None) -> AssistantAnswer:
    frame = bundle.tables[f'forecast_{horizon_hours}'].copy()
    if zone_name and zone_name != 'All 10 forecast zones':
        frame = frame.loc[frame.pickup_zone_name.eq(zone_name)]
        if frame.empty:
            return AssistantAnswer('Saved forecast', f'I could not find a saved forecast for {zone_name}.', 'not_found')
    summary = frame.groupby('pickup_zone_name', as_index=False)[['baseline_forecast', 'improved_forecast']].sum()
    if zone_name and zone_name != 'All 10 forecast zones':
        zone_frame = frame.sort_values('pickup_hour').head(3)
        total_baseline = float(frame['baseline_forecast'].sum())
        total_improved = float(frame['improved_forecast'].sum())
        first_hour = zone_frame.iloc[0]
        body = (
            f"The archived {horizon_hours}-hour forecast for {zone_name} runs from {frame.pickup_hour.min():%Y-%m-%d %H:%M} to {frame.pickup_hour.max():%Y-%m-%d %H:%M}. "
            f"Baseline totals {total_baseline:.1f} expected pickups and gradient boosting totals {total_improved:.1f}. "
            f"The first target hour is {first_hour.pickup_hour:%Y-%m-%d %H:%M}."
        )
        return AssistantAnswer('Saved forecast', body, 'forecast', zone_frame[['pickup_hour', 'pickup_zone_name', 'baseline_forecast', 'improved_forecast']])
    body = (
        f"The archived {horizon_hours}-hour forecast covers 10 zones from {frame.pickup_hour.min():%Y-%m-%d %H:%M} to {frame.pickup_hour.max():%Y-%m-%d %H:%M}. "
        f"Baseline totals {summary['baseline_forecast'].sum():.1f} expected pickups and gradient boosting totals {summary['improved_forecast'].sum():.1f}."
    )
    return AssistantAnswer('Saved forecast', body, 'forecast', summary)


def answer_recommendations(bundle: AssistantBundle) -> AssistantAnswer:
    body = 'The verified report includes five operational recommendations.'
    table = pd.DataFrame({'Recommendation': list(bundle.recommendations)})
    return AssistantAnswer('Operational recommendations', body, 'recommendations', table)


def answer_unsupported(message: str) -> AssistantAnswer:
    return AssistantAnswer('Unsupported question', message, 'unsupported')


def answer_clarification(message: str) -> AssistantAnswer:
    return AssistantAnswer('Clarification needed', message, 'clarify')


def answer_not_found(message: str, suggestions: tuple[str, ...] = ()) -> AssistantAnswer:
    return AssistantAnswer('Not found', message, 'not_found', suggestions=suggestions)


def answer_question(question: str, bundle: AssistantBundle | None = None) -> AssistantAnswer:
    bundle = bundle or load_bundle()
    routed = route_question(question, bundle)
    if routed.kind == 'clarify':
        return answer_clarification(routed.clarification or 'Please clarify your question.')
    if routed.kind == 'unsupported':
        return answer_unsupported(routed.unsupported_message or 'Unsupported question.')
    if routed.kind == 'unknown_zone':
        suggestions = routed.suggestions or ()
        if suggestions:
            suggestion_text = ', '.join(suggestions)
            return answer_not_found(f'I could not find that zone. Try one of these nearby zone names: {suggestion_text}.', suggestions)
        return answer_not_found(routed.clarification or 'I could not find that zone.')
    if routed.kind == 'top_pickups':
        return answer_top_pickups(bundle, routed.top_n)
    if routed.kind == 'top_destinations':
        return answer_top_destinations(bundle, routed.top_n)
    if routed.kind == 'borough_demand':
        return answer_borough_demand(bundle, routed.borough_name, routed.top_n)
    if routed.kind == 'hourly_demand':
        return answer_hourly_demand(bundle)
    if routed.kind == 'weekday_demand':
        return answer_weekday_demand(bundle)
    if routed.kind == 'od_overall':
        return answer_od_overall(bundle, routed.top_n)
    if routed.kind == 'od_from_zone':
        return answer_od_from_zone(bundle, routed.zone_name or '', routed.time_bucket, routed.top_n)
    if routed.kind == 'od_time':
        return answer_od_time(bundle, routed.time_bucket or 'evening_peak', routed.top_n)
    if routed.kind == 'forecast_metrics':
        return answer_forecast_metrics(bundle, routed.horizon_hours or 24)
    if routed.kind == 'saved_forecast':
        return answer_saved_forecast(bundle, routed.horizon_hours or 24, routed.zone_name)
    if routed.kind == 'recommendations':
        return answer_recommendations(bundle)
    return answer_unsupported('I could not map that request to a supported analytics intent.')


def question_examples() -> tuple[str, ...]:
    return (
        'What are the top 5 pickup zones?',
        'Which destination zone is busiest?',
        'What time is demand highest?',
        'What is the strongest OD route?',
        'What are the strongest evening routes?',
        'Which forecasting model should we use for 24 hours?',
        'What about 72 hours?',
        'What is the forecast for JFK Airport?',
        'What should fleet managers do during evening peaks?',
    )
