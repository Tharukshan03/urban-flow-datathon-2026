"""Phase 4: evidence-backed spatial analysis of existing Member 3 aggregates."""
from pathlib import Path
import json

import duckdb
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

TOTAL = 45_533_334
REPORTS = Path('reports')
FIGURES = REPORTS / 'figures'
BUCKETS = {
    'morning_peak': ('Morning peak 06:00–10:00', 4),
    'midday': ('Midday 10:00–16:00', 6),
    'evening_peak': ('Evening peak 16:00–20:00', 4),
    'late_night': ('Late night 20:00–06:00', 10),
}


def ranked(frame, count, names):
    return frame.sort_values([count, *names], ascending=[False, *([True] * len(names))], na_position='last').reset_index(drop=True)


def read_inputs():
    tables = {
        'pickup': pd.read_csv(REPORTS / 'member3_pickup_zone_totals.csv'),
        'borough_pickup': pd.read_csv(REPORTS / 'member3_pickup_borough_totals.csv'),
        'hour': pd.read_csv(REPORTS / 'member3_demand_by_hour.csv'),
        'metrics': pd.read_csv(REPORTS / 'member3_forecast_metrics.csv'),
    }
    for name in ('zone_pairs', 'borough_pairs', 'zone_time', 'borough_time'):
        tables[name] = pd.read_parquet(f'data/processed/member3_od_{name}.parquet')
        assert tables[name].trip_count.sum() == TOTAL, f'STOP: {name} count mismatch'
    for name in ('pickup', 'borough_pickup', 'hour'):
        assert tables[name].pickup_count.sum() == TOTAL, f'STOP: {name} count mismatch'
    assert set(tables['zone_time'].time_bucket) == set(BUCKETS), 'STOP: time bucket mismatch'
    # Full aggregate marginals must agree, including null labels.
    for endpoint in ('pickup', 'dropoff'):
        name = f'{endpoint}_zone_name'
        a = tables['zone_pairs'].groupby(name, dropna=False).trip_count.sum().sort_index()
        b = tables['zone_time'].groupby(name, dropna=False).trip_count.sum().sort_index()
        pd.testing.assert_series_equal(a, b)
    a = tables['zone_pairs'].groupby('pickup_zone_name', dropna=False).trip_count.sum().sort_index()
    b = tables['pickup'].set_index('pickup_zone_name').pickup_count.sort_index()
    pd.testing.assert_series_equal(a, b, check_names=False)
    print(f'Existing demand and OD totals reconcile to {TOTAL:,} retained trips.')
    return tables


def derive_destinations(tables):
    # Only the missing destination report is derived from the official source.
    with duckdb.connect() as con:
        con.execute("SET memory_limit='512MB'")
        con.execute('SET threads=2')
        result = con.execute('''SELECT dropoff_zone_name, count(*) AS dropoff_count
            FROM read_parquet('data/processed/clean_trips.parquet') GROUP BY 1
            ORDER BY 2 DESC, 1''').fetchdf()
    assert result.dropoff_count.sum() == TOTAL, 'STOP: destination counts mismatch'
    derived = tables['zone_pairs'].groupby('dropoff_zone_name', dropna=False).trip_count.sum().sort_index()
    pd.testing.assert_series_equal(result.set_index('dropoff_zone_name').dropoff_count.sort_index(), derived, check_names=False)
    result.to_csv(REPORTS / 'member3_dropoff_zone_totals.csv', index=False)
    tables['dropoff'] = result
    print(f'Destination report: {len(result)} groups; direct scan and full OD marginals agree exactly.')


def prepare(tables):
    ztime = tables['zone_time']
    summary = ztime.groupby('time_bucket').trip_count.sum().reindex(BUCKETS).rename('trip_count').reset_index()
    summary['window_hours_per_day'] = summary.time_bucket.map({k: v[1] for k, v in BUCKETS.items()})
    summary['share_percent'] = summary.trip_count / TOTAL * 100
    summary['mean_pickups_per_nominal_hour'] = summary.trip_count / (365 * summary.window_hours_per_day)
    hour = tables['hour'].copy()
    hour['mean_pickups_per_calendar_day'] = hour.pickup_count / 365
    zone_time = ztime.groupby(['time_bucket', 'pickup_zone_name'], dropna=False, as_index=False).trip_count.sum()
    zone_time['mean_pickups_per_nominal_hour'] = zone_time.trip_count / (365 * zone_time.time_bucket.map({k: v[1] for k, v in BUCKETS.items()}))
    bucket_for_hour = lambda h: 'morning_peak' if 6 <= h < 10 else 'midday' if 10 <= h < 16 else 'evening_peak' if 16 <= h < 20 else 'late_night'
    hourly_buckets = hour.assign(time_bucket=hour.hour_of_day.map(bucket_for_hour)).groupby('time_bucket').pickup_count.sum()
    pd.testing.assert_series_equal(summary.set_index('time_bucket').trip_count.sort_index(), hourly_buckets.sort_index(), check_names=False)
    pd.testing.assert_series_equal(tables['borough_time'].groupby('time_bucket').trip_count.sum().sort_index(), hourly_buckets.sort_index(), check_names=False)
    tables.update(bucket_summary=summary, hour_summary=hour, pickup_time=zone_time)
    summary.to_csv(REPORTS / 'member3_spatial_time_summary.csv', index=False)
    zone_time.to_csv(REPORTS / 'member3_spatial_pickup_by_time.csv', index=False)
    for name, count, keys in [('pickup', 'pickup_count', ['pickup_zone_name']), ('dropoff', 'dropoff_count', ['dropoff_zone_name']),
                               ('zone_pairs', 'trip_count', ['pickup_zone_name', 'dropoff_zone_name'])]:
        tables[f'top_{name}'] = ranked(tables[name].dropna(subset=keys), count, keys).head(10)
    tables['top_time_pairs'] = pd.concat([
        ranked(ztime.loc[ztime.time_bucket.eq(bucket)].dropna(subset=['pickup_zone_name', 'dropoff_zone_name']),
               'trip_count', ['pickup_zone_name', 'dropoff_zone_name']).head(5) for bucket in BUCKETS], ignore_index=True)
    tables['top_time_pairs'].to_csv(REPORTS / 'member3_spatial_top_time_pairs.csv', index=False)
    print(summary.to_string(index=False, float_format=lambda x: f'{x:,.2f}'))


def draw(tables):
    FIGURES.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size': 11, 'axes.titlesize': 13, 'axes.spines.top': False, 'axes.spines.right': False})
    def bars(ax, labels, counts, color, title, divisor=1):
        values = np.asarray(counts) / divisor
        ax.barh(list(labels)[::-1], values[::-1], color=color, height=0.72)
        ax.set_title(title, loc='left', pad=12)
        ax.set_xlim(0, max(values) * 1.23)
        ax.grid(axis='x', alpha=0.18)
        ax.set_axisbelow(True)
        for i, value in enumerate(values[::-1]):
            label = f'{value:.2f}' if divisor > 1 else f'{value:,.0f}'
            ax.text(value + max(values)*0.015, i, label, va='center', fontsize=10)
    fig, axes = plt.subplots(1, 2, figsize=(16, 7), constrained_layout=True)
    bars(axes[0], tables['top_pickup'].pickup_zone_name, tables['top_pickup'].pickup_count, '#087F8C', 'Top 10 pickup zones', 1e6)
    bars(axes[1], tables['top_dropoff'].dropoff_zone_name, tables['top_dropoff'].dropoff_count, '#6554A4', 'Top 10 destination zones', 1e6)
    for ax in axes: ax.set_xlabel('Retained trips (millions)')
    fig.suptitle('Pickup and destination hotspots | Apr 2025–Mar 2026\nRanked among readable labels; missing-label groups retained in source totals', fontsize=14)
    fig.savefig(FIGURES / 'hotspot_zones.png', dpi=160)
    plt.close(fig)

    top = tables['top_zone_pairs']
    fig, ax = plt.subplots(figsize=(14, 7), constrained_layout=True)
    bars(ax, top.pickup_zone_name + ' → ' + top.dropoff_zone_name, top.trip_count,
         '#087F8C', 'Top 10 directed zone pairs | Apr 2025–Mar 2026')
    ax.set_xlabel('Retained trips (pickups → destinations)')
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x/1000:,.0f}k'))
    fig.savefig(FIGURES / 'od_flows.png', dpi=160)
    plt.close(fig)

    hour = tables['hour_summary'].sort_values('hour_of_day')
    fig, ax = plt.subplots(figsize=(12, 5.5), constrained_layout=True)
    colors = ['#475569' if h < 6 or h >= 20 else '#E5A23C' if h < 10 else '#80B1A3' if h < 16 else '#087F8C' for h in hour.hour_of_day]
    ax.bar(hour.hour_of_day, hour.mean_pickups_per_calendar_day, color=colors)
    peak = hour.loc[hour.pickup_count.idxmax()]
    ax.annotate(f"Peak: {int(peak.hour_of_day):02}:00–{int(peak.hour_of_day)+1:02}:00\n{peak.mean_pickups_per_calendar_day:,.0f} pickups/day",
                xy=(peak.hour_of_day, peak.mean_pickups_per_calendar_day), xytext=(5, 8500),
                arrowprops={'arrowstyle': '->', 'color': '#334155'})
    ax.set(xticks=range(24), xlabel='Pickup clock hour (timezone-naive)', ylabel='Mean retained pickups per calendar day', ylim=(0, 11000))
    ax.set_title('Hourly pickup pattern | Apr 2025–Mar 2026\n365-day denominator; documented absent hour retained as zero', loc='left')
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=c, label=l) for c,l in [('#E5A23C','Morning 06–10'),('#80B1A3','Midday 10–16'),('#087F8C','Evening 16–20'),('#475569','Late night 20–06')]], ncol=4, loc='upper left', fontsize=9)
    ax.grid(axis='y', alpha=0.18)
    ax.set_axisbelow(True)
    fig.savefig(FIGURES / 'demand_by_hour.png', dpi=160)
    plt.close(fig)

    borough = tables['borough_pairs'].copy()
    borough[['pickup_borough_name','dropoff_borough_name']] = borough[['pickup_borough_name','dropoff_borough_name']].fillna('(missing label)')
    names = sorted(set(borough.pickup_borough_name) | set(borough.dropoff_borough_name))
    matrix = borough.pivot(index='pickup_borough_name',columns='dropoff_borough_name',values='trip_count').reindex(index=names,columns=names).fillna(0)
    fig, ax = plt.subplots(figsize=(10, 8), constrained_layout=True)
    from matplotlib.colors import LogNorm
    im = ax.imshow(matrix.to_numpy()+1, norm=LogNorm(vmin=1, vmax=matrix.to_numpy().max()+1), cmap='Blues')
    ax.set(xticks=range(len(names)), yticks=range(len(names)), xticklabels=names, yticklabels=names,
           xlabel='Dropoff label', ylabel='Pickup label', title='Borough-label flows | All retained trips\nCells show exact counts; color is log-scaled (count + 1)')
    plt.setp(ax.get_xticklabels(), rotation=40, ha='right')
    for i in range(len(names)):
        for j in range(len(names)):
            value = int(matrix.iloc[i,j])
            ax.text(j,i,f'{value:,}',ha='center',va='center',fontsize=8,color='white' if value > 100_000 else '#172554')
    fig.colorbar(im, ax=ax, label='Trip count + 1 (log scale)', shrink=0.8)
    fig.savefig(FIGURES / 'member3_borough_flows.png', dpi=160)
    plt.close(fig)

    fig, axes = plt.subplots(4, 1, figsize=(14, 15), constrained_layout=True)
    for ax, bucket in zip(axes, BUCKETS):
        subset = tables['top_time_pairs'].loc[lambda x: x.time_bucket.eq(bucket)]
        bars(ax, subset.pickup_zone_name+' → '+subset.dropoff_zone_name, subset.trip_count,
             '#087F8C', BUCKETS[bucket][0] + ' | Top 5 directed pairs')
        ax.set_xlabel('Retained trips in this window over the full year')
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x,_: f'{x/1000:,.0f}k'))
    fig.suptitle('Time-of-day OD leaders | Unequal window lengths; compare normalized rates in report', fontsize=14)
    fig.savefig(FIGURES / 'member3_od_by_time.png', dpi=160)
    plt.close(fig)


def markdown_table(frame):
    def value(x):
        if pd.isna(x): return '(missing label)'
        if isinstance(x, (int, np.integer)): return f'{x:,}'
        if isinstance(x, (float, np.floating)): return f'{x:,.3f}'
        return str(x).replace('|', '\\|')
    lines = ['| ' + ' | '.join(frame.columns) + ' |', '| ' + ' | '.join(['---']*len(frame.columns)) + ' |']
    lines += ['| ' + ' | '.join(value(x) for x in row) + ' |' for row in frame.itertuples(index=False, name=None)]
    return '\n'.join(lines)


def findings(t):
    pickup = t['top_pickup'].iloc[0]
    dest = t['top_dropoff'].iloc[0]
    peak = t['hour_summary'].loc[t['hour_summary'].pickup_count.idxmax()]
    pairs = t['top_zone_pairs']
    reverse = t['zone_pairs'].loc[
        t['zone_pairs'].pickup_zone_name.eq(pairs.iloc[0].dropoff_zone_name)
        & t['zone_pairs'].dropoff_zone_name.eq(pairs.iloc[0].pickup_zone_name), 'trip_count'].sum()
    bucket = t['bucket_summary'].set_index('time_bucket')
    time_leaders = t['top_time_pairs'].groupby('time_bucket', sort=False).head(1)
    by_time = t['pickup_time'].dropna(subset=['pickup_zone_name'])
    evening = ranked(by_time.loc[by_time.time_bucket.eq('evening_peak')], 'trip_count', ['pickup_zone_name']).iloc[0]
    late = time_leaders.loc[time_leaders.time_bucket.eq('late_night')].iloc[0]
    borough = ranked(t['borough_pairs'], 'trip_count', ['pickup_borough_name','dropoff_borough_name'])
    metrics = t['metrics'].loc[t['metrics'].split.eq('test')]
    assert metrics.winner.tolist() == ['Improved','Baseline','Baseline'], 'STOP: confirmed forecast winners mismatch'
    missing_pu = int(t['pickup'].loc[t['pickup'].pickup_zone_name.isna(), 'pickup_count'].sum())
    missing_do = int(t['dropoff'].loc[t['dropoff'].dropoff_zone_name.isna(), 'dropoff_count'].sum())
    recs = [
        f'Prioritize a staging-capacity review in **{pickup.pickup_zone_name}**, the first-ranked pickup zone with **{pickup.pickup_count:,}** retained pickups ({pickup.pickup_count/TOTAL*100:.2f}% of all retained trips). Use observed queues and utilization to size any deployment; the counts alone do not establish a vehicle shortage. Evidence: `member3_pickup_zone_totals.csv` and `figures/hotspot_zones.png`.',
        f'Plan an **evening 16:00–20:00** dispatch emphasis in **{evening.pickup_zone_name}**, which records **{evening.trip_count:,}** pickups in that window ({evening.mean_pickups_per_nominal_hour:,.2f} per nominal hour). Network-wide evening intensity is **{bucket.loc["evening_peak","mean_pickups_per_nominal_hour"]:,.2f}** pickups/hour versus **{bucket.loc["morning_peak","mean_pickups_per_nominal_hour"]:,.2f}** in the morning. Evidence: `member3_spatial_pickup_by_time.csv`, `member3_spatial_time_summary.csv`, `figures/demand_by_hour.png`.',
        f'Keep **20:00–06:00** dispatch coverage under review for **{late.pickup_zone_name} → {late.dropoff_zone_name}**, the leading readable late-night pair with **{late.trip_count:,}** trips. Late-night network volume is **{int(bucket.loc["late_night","trip_count"]):,}**, but its ten-hour window averages only **{bucket.loc["late_night","mean_pickups_per_nominal_hour"]:,.2f}** pickups/hour; avoid allocating staff from window totals alone. Evidence: `member3_spatial_top_time_pairs.csv` and `figures/member3_od_by_time.png`.',
        f'Monitor both directions of **{pairs.iloc[0].pickup_zone_name} ↔ {pairs.iloc[0].dropoff_zone_name}** when planning repositioning. The leading direction carries **{pairs.iloc[0].trip_count:,}** trips versus **{reverse:,}** in reverse, a difference of **{pairs.iloc[0].trip_count-reverse:,}** over the year. Check time-specific vehicle availability before moving empty vehicles: these are occupied-trip counts, not a fleet balance. Evidence: `member3_od_zone_pairs.csv` and `figures/od_flows.png`.',
        'Use the **24h gradient-boosting forecast** as the starting point for next-day dispatch and the **seasonal baseline at 48h/72h** for longer-range staffing, subject to ongoing monitoring. Held-out MAE favors those methods at each horizon (values in Section 6). This choice is suggested by the observed test results, not an independently validated deployment policy. Evidence: `member3_forecast_metrics.csv` and `figures/demand_forecast.png`.',
    ]
    sections = [
        '# Member 3 — Demand and spatial findings',
        '## 1. Demand overview',
        f'The official processed dataset contains **{TOTAL:,} retained pickups** from **2025-04-01 00:00:00 through 2026-03-31 23:59:59**. This report describes retained records, not all raw demand. No preprocessing, Phase 2 aggregation or forecasting was rerun. Existing full OD tables reconcile to the retained total. The new destination report uses one column-only DuckDB scan and matches full OD destination marginals exactly.',
        f'The busiest clock hour is **{int(peak.hour_of_day):02}:00–{int(peak.hour_of_day)+1:02}:00**, with **{int(peak.pickup_count):,}** annual pickups, or **{peak.mean_pickups_per_calendar_day:,.2f}** per calendar day. Source: `member3_demand_by_hour.csv`; chart: [demand_by_hour.png](figures/demand_by_hour.png).',
        'Time buckets are half-open: morning [06:00,10:00), midday [10:00,16:00), evening [16:00,20:00), late night [20:00,24:00) plus [00:00,06:00). Normalized intensity divides counts by 365 days and the nominal window length; it is not active-service-hour intensity. The documented absent hour **2026-03-08 02:00** remains zero. No timezone or daylight-saving correction is inferred.',
        f'Null pickup and destination labels account for **{missing_pu:,}** and **{missing_do:,}** records respectively. All full totals retain these groups; top-zone/pair displays require readable endpoints. Existing borough labels such as `Unknown` and `EWR` remain as supplied; `(missing label)` is a display marker, not invented geography. Source: pickup/dropoff total CSVs and full OD Parquet tables.',
        '## 2. Top pickup hotspots',
        markdown_table(t['top_pickup']),
        'Source: `member3_pickup_zone_totals.csv`; chart: [hotspot_zones.png](figures/hotspot_zones.png).',
        '## 3. Top destination hotspots',
        markdown_table(t['top_dropoff']),
        f'**{dest.dropoff_zone_name}** ranks first with **{dest.dropoff_count:,}** dropoffs. Source: `member3_dropoff_zone_totals.csv`; chart: [hotspot_zones.png](figures/hotspot_zones.png).',
        '## 4. Major OD flows',
        markdown_table(pairs),
        'Directions are pickup → dropoff. A same-zone pair means endpoints share a zone, not that a vehicle stayed at one physical location. Source: full `data/processed/member3_od_zone_pairs.parquet` (top 100 also in `member3_od_zone_pairs.csv`); chart: [od_flows.png](figures/od_flows.png).',
        markdown_table(borough.head(10)),
        f'The largest borough-label flow is **{borough.iloc[0].pickup_borough_name} → {borough.iloc[0].dropoff_borough_name}**, with **{borough.iloc[0].trip_count:,}** trips ({borough.iloc[0].trip_count/TOTAL*100:.2f}% of all retained records). Source: `member3_od_borough_pairs.csv`; chart: [member3_borough_flows.png](figures/member3_borough_flows.png).',
        '## 5. Morning, evening and late-night differences',
        markdown_table(t['bucket_summary']),
        f'Evening intensity is **{bucket.loc["evening_peak","mean_pickups_per_nominal_hour"]/bucket.loc["morning_peak","mean_pickups_per_nominal_hour"]:.2f} times** morning intensity. Late night has more total trips than evening ({int(bucket.loc["late_night","trip_count"]):,} versus {int(bucket.loc["evening_peak","trip_count"]):,}), but less demand per nominal hour because it spans ten hours rather than four. Source: `member3_spatial_time_summary.csv`, reconciled independently to the hour-of-day aggregate.',
        'Leading directed readable pair within each bucket:', markdown_table(time_leaders),
        'Source: full `member3_od_zone_time.parquet`; selected top five per bucket in `member3_spatial_top_time_pairs.csv`. Chart: [member3_od_by_time.png](figures/member3_od_by_time.png). These are volume patterns, not proof of commute purpose or unmet demand.',
        '## 6. Forecasting summary',
        markdown_table(metrics[['horizon_hours','baseline_mae','improved_mae','baseline_rmse','improved_rmse','winner']]),
        'The improved model wins at 24h; the seasonal baseline wins at 48h and 72h. Metrics are pickups per zone-hour over 53 daily test origins and each horizon’s first H predictions. Recursive paths do not use future observed demand. Test windows overlap, and the ten zones were selected retrospectively in Phase 2; results are conditional on that cohort. Source: `member3_forecast_metrics.csv` (full precision) and [demand_forecast.png](figures/demand_forecast.png). No models were rerun in Phase 4.',
        '## 7. Operational recommendations',
        '\n\n'.join(f'{i}. {r}' for i,r in enumerate(recs,1)),
        '## Member 3 completion summary',
        'Delivered validated hourly demand, baseline/candidate forecasts for 24/48/72h, pickup/destination hotspots, directed zone and borough flows, time-window comparisons and five evidence-linked recommendations. All conclusions concern the official retained-trip dataset. No unsupported savings, vehicle quantities or geographic coordinates are inferred.',
    ]
    text = '\n\n'.join(sections)+'\n'
    (REPORTS / 'demand_spatial_findings.md').write_text(text, encoding='utf-8')
    return text


def check_outputs(tables):
    required = ['hotspot_zones.png','od_flows.png','demand_by_hour.png','demand_forecast.png',
                'member3_borough_flows.png','member3_od_by_time.png']
    for name in required:
        path = FIGURES / name
        assert path.is_file() and path.stat().st_size > 0, f'STOP: missing figure {name}'
    assert (REPORTS / 'demand_spatial_findings.md').is_file()
    inventory = [REPORTS / 'member3_dropoff_zone_totals.csv', REPORTS / 'member3_spatial_time_summary.csv',
                 REPORTS / 'member3_spatial_pickup_by_time.csv', REPORTS / 'member3_spatial_top_time_pairs.csv',
                 REPORTS / 'demand_spatial_findings.md', *[FIGURES / n for n in required]]
    result = [{'path': p.as_posix(), 'bytes': p.stat().st_size} for p in inventory]
    (REPORTS / 'member3_spatial_output_inventory.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('All required figures and findings exist. Claims use the same reconciled tables as charts.')
    for name in ('top_pickup','top_dropoff','top_zone_pairs','top_time_pairs'):
        print('\n'+name+'\n'+tables[name].to_string(index=False))
