"""Copy the approved small reporting inputs from the pinned Member 3 commit."""
from pathlib import Path
import hashlib
import json
import subprocess

SOURCE_BRANCH = 'feature/forecasting-spatial'
SOURCE_COMMIT = '8b3cdee641b59d27ff4ce9cd037bd5e46ccd7096'
NAMES = [
    'member3_pickup_zone_totals.csv', 'member3_dropoff_zone_totals.csv',
    'member3_pickup_borough_totals.csv', 'member3_demand_by_hour.csv',
    'member3_demand_by_weekday.csv', 'member3_od_zone_pairs.csv',
    'member3_od_borough_pairs.csv', 'member3_od_zone_time_top.csv',
    'member3_od_borough_time.csv', 'member3_spatial_pickup_by_time.csv',
    'member3_spatial_time_summary.csv', 'member3_forecast_metrics.csv',
    'forecast_24h.csv', 'forecast_48h.csv', 'forecast_72h.csv',
    'demand_spatial_findings.md',
]


def main():
    root = Path(__file__).parents[2]
    destination = Path(__file__).parents[1] / 'data'
    destination.mkdir(parents=True, exist_ok=True)
    entries = []
    for name in NAMES:
        source_path = 'reports/' + name
        content = subprocess.check_output(['git', 'show', f'{SOURCE_COMMIT}:{source_path}'], cwd=root)
        (destination / name).write_bytes(content)
        entries.append({'file': name, 'source_path': source_path, 'bytes': len(content),
                        'sha256': hashlib.sha256(content).hexdigest()})
    manifest = {'source_branch': SOURCE_BRANCH, 'source_commit': SOURCE_COMMIT, 'files': entries}
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print(f'Bundled {len(entries)} unchanged reports, {sum(e["bytes"] for e in entries):,} bytes; no datasets or models.')


if __name__ == '__main__':
    main()
