"""Memory-safe Member 3 Phase 2 operations; never changes Member 1 outputs."""

from pathlib import Path
import csv
import json

import duckdb
import pyarrow.parquet as pq

SOURCE = Path('data/processed/clean_trips.parquet')
EXPECTED_ROWS = 45_533_334
OUT = Path('data/processed')
REPORTS = Path('reports')


def connect():
    con = duckdb.connect()
    con.execute("SET memory_limit='1GB'")
    con.execute('SET threads=2')
    con.execute("SET temp_directory='data/processed/member3_duckdb_tmp'")
    con.execute("CREATE VIEW trips AS SELECT pickup_timestamp, pickup_zone_name, pickup_borough_name, dropoff_zone_name, dropoff_borough_name FROM read_parquet('data/processed/clean_trips.parquet')")
    return con


def verify():
    meta = pq.read_metadata(SOURCE)
    names = meta.schema.to_arrow_schema().names
    required = ['pickup_timestamp', 'pickup_zone_name', 'pickup_borough_name', 'dropoff_zone_name', 'dropoff_borough_name']
    assert meta.num_rows == EXPECTED_ROWS, 'STOP: handover row mismatch'
    assert meta.num_columns == 45, 'STOP: handover column mismatch'
    assert all(name in names for name in required), 'STOP: missing documented field'
    print(f'Handover verified: {meta.num_rows:,} rows, {meta.num_columns} columns, {meta.num_row_groups} row groups.')


def validate_timestamps(con):
    print('Timestamp sample:', [r[0] for r in con.execute('SELECT pickup_timestamp FROM trips LIMIT 8').fetchall()])
    con.execute("CREATE VIEW parsed AS SELECT *, try_strptime(pickup_timestamp, '%Y-%m-%d %H:%M:%S') AS pickup_ts FROM trips")
    result = con.execute('''SELECT count(*) AS total_rows,
        count(*) FILTER (WHERE pickup_timestamp IS NULL) AS null_timestamps,
        count(*) FILTER (WHERE pickup_timestamp IS NOT NULL AND pickup_ts IS NULL) AS unparseable_timestamps,
        count(*) FILTER (WHERE pickup_ts IS NULL) AS invalid_timestamps,
        min(pickup_ts) AS min_pickup_timestamp, max(pickup_ts) AS max_pickup_timestamp
        FROM parsed''')
    summary = dict(zip([d[0] for d in result.description], result.fetchone()))
    summary['invalid_timestamp_percent'] = summary['invalid_timestamps'] / summary['total_rows'] * 100
    print(json.dumps(summary, indent=2, default=str))
    assert summary['total_rows'] == EXPECTED_ROWS, 'STOP: row count mismatch'
    assert summary['invalid_timestamps'] == 0, 'STOP: invalid timestamps; no records have been dropped'
    assert summary['min_pickup_timestamp'] is not None, 'STOP: no usable timestamps'
    print('All pickup timestamps parse; chronological ordering is possible with ORDER BY pickup_ts. Physical source order is not assumed.')
    return summary


def coverage(con, timestamps):
    result = con.execute('''SELECT count(DISTINCT pickup_zone_name) AS unique_pickup_zones,
        count(DISTINCT pickup_borough_name) AS unique_pickup_boroughs,
        count(*) FILTER (WHERE pickup_zone_name IS NULL) AS null_pickup_zone_name,
        count(*) FILTER (WHERE pickup_borough_name IS NULL) AS null_pickup_borough_name,
        count(*) FILTER (WHERE dropoff_zone_name IS NULL) AS null_dropoff_zone_name,
        count(*) FILTER (WHERE dropoff_borough_name IS NULL) AS null_dropoff_borough_name FROM trips''')
    summary = {**timestamps, **dict(zip([d[0] for d in result.description], result.fetchone()))}
    print(json.dumps(summary, indent=2, default=str))
    return summary


def hourly(con):
    con.execute('''CREATE TABLE hourly AS SELECT date_trunc('hour', pickup_ts) AS pickup_hour,
        pickup_zone_name, pickup_borough_name, count(*) AS pickup_count
        FROM parsed GROUP BY 1,2,3''')
    total, rows = con.execute('SELECT sum(pickup_count), count(*) FROM hourly').fetchone()
    assert total == EXPECTED_ROWS, 'STOP: hourly counts do not reconcile'
    print(f'Hourly aggregate: {rows:,} rows; {total:,} pickups reconciled.')


def top_zones(con):
    con.execute('''CREATE TABLE zone_totals AS SELECT pickup_zone_name, sum(pickup_count)::BIGINT AS pickup_count
        FROM hourly GROUP BY 1''')
    con.execute('''CREATE TABLE top_zones AS SELECT row_number() OVER (ORDER BY pickup_count DESC, pickup_zone_name) AS rank,
        pickup_zone_name, pickup_count FROM zone_totals WHERE pickup_zone_name IS NOT NULL
        ORDER BY pickup_count DESC, pickup_zone_name LIMIT 10''')
    # Refuse to assign a borough if a selected readable zone maps to multiple boroughs.
    ambiguity = con.execute('''SELECT h.pickup_zone_name FROM (SELECT DISTINCT pickup_zone_name, pickup_borough_name FROM hourly) h
        JOIN top_zones z USING(pickup_zone_name) GROUP BY 1 HAVING count(*) > 1''').fetchall()
    assert not ambiguity, f'STOP: ambiguous zone/borough labels: {ambiguity}'
    con.execute('''CREATE TABLE top_hourly AS WITH bounds AS (
        SELECT min(pickup_hour) AS lo, max(pickup_hour) AS hi FROM hourly), hours AS (
        SELECT unnest(generate_series(lo, hi, INTERVAL '1 hour')) AS pickup_hour FROM bounds), labels AS (
        SELECT DISTINCT h.pickup_zone_name, h.pickup_borough_name FROM hourly h JOIN top_zones z USING(pickup_zone_name))
        SELECT t.pickup_hour, z.pickup_zone_name, z.pickup_borough_name,
        coalesce(h.pickup_count, 0)::BIGINT AS pickup_count, h.pickup_count IS NULL AS filled_zero
        FROM hours t CROSS JOIN labels z LEFT JOIN hourly h ON h.pickup_hour=t.pickup_hour
        AND h.pickup_zone_name=z.pickup_zone_name AND h.pickup_borough_name IS NOT DISTINCT FROM z.pickup_borough_name''')
    expected = con.execute("SELECT (date_diff('hour', min(pickup_hour), max(pickup_hour))+1)*10 FROM hourly").fetchone()[0]
    n, zeroes, total = con.execute('SELECT count(*), count(*) FILTER (WHERE filled_zero), sum(pickup_count) FROM top_hourly').fetchone()
    assert n == expected, 'STOP: incomplete top-zone grid'
    assert total == con.execute('SELECT sum(pickup_count) FROM top_zones').fetchone()[0], 'STOP: top-zone counts mismatch'
    for row in con.execute('SELECT * FROM top_zones ORDER BY rank').fetchall():
        print(row)
    print(f'Complete top-zone series: {n:,} rows; {zeroes:,} absent zone-hours filled with zero.')
    print('Global hours with no records:', con.execute("SELECT date_diff('hour', min(pickup_hour), max(pickup_hour))+1-count(DISTINCT pickup_hour) FROM hourly").fetchone()[0])
    con.execute('''CREATE TABLE by_hour AS SELECT extract(hour FROM pickup_hour)::INTEGER AS hour_of_day,
        sum(pickup_count)::BIGINT AS pickup_count FROM hourly GROUP BY 1''')
    con.execute('''CREATE TABLE by_weekday AS SELECT extract(isodow FROM pickup_hour)::INTEGER AS iso_weekday,
        strftime(pickup_hour, '%A') AS weekday, sum(pickup_count)::BIGINT AS pickup_count FROM hourly GROUP BY 1,2''')
    con.execute('''CREATE TABLE by_borough AS SELECT pickup_borough_name, sum(pickup_count)::BIGINT AS pickup_count FROM hourly GROUP BY 1''')
    for table in ('zone_totals', 'by_hour', 'by_weekday', 'by_borough'):
        assert con.execute(f'SELECT sum(pickup_count) FROM {table}').fetchone()[0] == EXPECTED_ROWS, f'STOP: {table} count mismatch'


def od(con):
    con.execute('''CREATE TABLE od_zone AS SELECT pickup_zone_name, dropoff_zone_name, count(*) AS trip_count FROM trips GROUP BY 1,2''')
    con.execute('''CREATE TABLE od_borough AS SELECT pickup_borough_name, dropoff_borough_name, count(*) AS trip_count FROM trips GROUP BY 1,2''')
    con.execute('''CREATE VIEW bucketed AS SELECT *, CASE
        WHEN extract(hour FROM pickup_ts) >= 6 AND extract(hour FROM pickup_ts) < 10 THEN 'morning_peak'
        WHEN extract(hour FROM pickup_ts) >= 10 AND extract(hour FROM pickup_ts) < 16 THEN 'midday'
        WHEN extract(hour FROM pickup_ts) >= 16 AND extract(hour FROM pickup_ts) < 20 THEN 'evening_peak'
        ELSE 'late_night' END AS time_bucket FROM parsed''')
    for geography in ('zone', 'borough'):
        con.execute(f'''CREATE TABLE od_{geography}_time AS SELECT time_bucket, pickup_{geography}_name,
            dropoff_{geography}_name, count(*) AS trip_count FROM bucketed GROUP BY 1,2,3''')
    for table in ('od_zone', 'od_borough', 'od_zone_time', 'od_borough_time'):
        rows, total = con.execute(f'SELECT count(*), sum(trip_count) FROM {table}').fetchone()
        assert total == EXPECTED_ROWS, f'STOP: {table} count mismatch'
        print(f'{table}: {rows:,} aggregate rows; {total:,} trips reconciled.')


def save(con, summary):
    outputs = []
    queries = {
        'hourly_demand': 'SELECT * FROM hourly ORDER BY pickup_hour, pickup_zone_name, pickup_borough_name',
        'top_zone_hourly': 'SELECT * FROM top_hourly ORDER BY pickup_hour, pickup_zone_name',
        'od_zone_pairs': 'SELECT * FROM od_zone ORDER BY trip_count DESC, pickup_zone_name, dropoff_zone_name',
        'od_borough_pairs': 'SELECT * FROM od_borough ORDER BY trip_count DESC, pickup_borough_name, dropoff_borough_name',
        'od_zone_time': 'SELECT * FROM od_zone_time ORDER BY time_bucket, trip_count DESC, pickup_zone_name, dropoff_zone_name',
        'od_borough_time': 'SELECT * FROM od_borough_time ORDER BY time_bucket, trip_count DESC, pickup_borough_name, dropoff_borough_name',
    }
    for name, query in queries.items():
        path = OUT / f'member3_{name}.parquet'
        con.execute(f"COPY ({query}) TO '{path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)")
        outputs.append({'path': path.as_posix(), 'rows': pq.read_metadata(path).num_rows, 'bytes': path.stat().st_size})
    csv_queries = {
        'top_zones': 'SELECT * FROM top_zones ORDER BY rank',
        'demand_by_hour': 'SELECT * FROM by_hour ORDER BY hour_of_day',
        'demand_by_weekday': 'SELECT * FROM by_weekday ORDER BY iso_weekday',
        'pickup_zone_totals': 'SELECT * FROM zone_totals ORDER BY pickup_count DESC, pickup_zone_name',
        'pickup_borough_totals': 'SELECT * FROM by_borough ORDER BY pickup_count DESC, pickup_borough_name',
        'od_zone_pairs': queries['od_zone_pairs'] + ' LIMIT 100',
        'od_borough_pairs': queries['od_borough_pairs'],
        'od_borough_time': queries['od_borough_time'],
        'od_zone_time_top': '''SELECT * FROM od_zone_time QUALIFY row_number() OVER (
            PARTITION BY time_bucket ORDER BY trip_count DESC, pickup_zone_name, dropoff_zone_name) <= 25
            ORDER BY time_bucket, trip_count DESC, pickup_zone_name, dropoff_zone_name''',
    }
    for name, query in csv_queries.items():
        path = REPORTS / f'member3_{name}.csv'
        result = con.execute(query)
        rows = result.fetchall()  # Only compact reporting aggregates, never source trip rows.
        with path.open('w', newline='', encoding='utf-8') as handle:
            writer = csv.writer(handle)
            writer.writerow([d[0] for d in result.description])
            writer.writerows(rows)
        outputs.append({'path': path.as_posix(), 'rows': len(rows), 'bytes': path.stat().st_size})
    summary['outputs'] = outputs
    summary['top_zone_zero_filled_hours'] = con.execute('SELECT count(*) FROM top_hourly WHERE filled_zero').fetchone()[0]
    missing_hours = con.execute('''WITH bounds AS (SELECT min(pickup_hour) AS lo, max(pickup_hour) AS hi FROM hourly),
        hours AS (SELECT unnest(generate_series(lo, hi, INTERVAL '1 hour')) AS pickup_hour FROM bounds)
        SELECT pickup_hour FROM hours EXCEPT SELECT pickup_hour FROM hourly ORDER BY pickup_hour''').fetchall()
    summary['global_hours_without_records'] = [str(row[0]) for row in missing_hours]
    summary['timestamp_format'] = '%Y-%m-%d %H:%M:%S'
    summary['duckdb_version'] = duckdb.__version__
    print('Global hours without source records:', summary['global_hours_without_records'])
    (REPORTS / 'member3_phase2_summary.json').write_text(json.dumps(summary, indent=2, default=str)+'\n', encoding='utf-8')
    for output in outputs:
        print(f"{output['path']}: {output['rows']:,} rows; {output['bytes']:,} bytes")
    return outputs
