"""Reporting integrity and Streamlit control checks; no raw data or model runs."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest

import numpy as np
from streamlit.testing.v1 import AppTest
from dashboard.utils.data_loader import DATA_DIR, DataError, load_data, preferred_model


class ReportingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_data()

    def test_snapshot_is_byte_identical_to_pinned_commit(self):
        manifest = self.data['manifest']
        for entry in manifest['files']:
            with self.subTest(file=entry['file']):
                source = subprocess.check_output(['git','show',manifest['source_commit']+':'+entry['source_path']])
                self.assertEqual((DATA_DIR/entry['file']).read_bytes(),source)
                self.assertEqual(hashlib.sha256(source).hexdigest(),entry['sha256'])
        self.assertFalse(list(DATA_DIR.glob('*.parquet')))

    def test_missing_inputs_fail_with_useful_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(DataError,'Missing dashboard inputs'):
                load_data(tmp)

    def test_changed_snapshot_fails_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(DATA_DIR,Path(tmp)/'data')
            with (Path(tmp)/'data/member3_forecast_metrics.csv').open('a') as handle:
                handle.write('\n')
            with self.assertRaisesRegex(DataError,'checksum mismatch'):
                load_data(Path(tmp)/'data')

    def test_metrics_and_recommendations_are_source_values(self):
        d = self.data
        rows = d['test_metrics']
        self.assertEqual([preferred_model(r) for r in rows.itertuples()],['improved','baseline','baseline'])
        np.testing.assert_allclose(rows.baseline_mae,[33.60378891112382,33.574418556635536,33.57139082121],rtol=0,atol=1e-12)
        np.testing.assert_allclose(rows.improved_mae,[32.30299278081765,34.26828288603496,35.188656381453185],rtol=0,atol=1e-12)
        for recommendation in d['recommendations']:
            self.assertIn(recommendation,d['report'])
        self.assertEqual(len(d['recommendations']),5)


class AppTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file('../app.py').run(timeout=30)

    def check_charts(self, count):
        self.assertEqual([e.message for e in self.app.exception],[])
        self.assertEqual([e.value for e in self.app.error],[])
        charts = self.app.get('plotly_chart')
        self.assertEqual(len(charts),count)
        for chart in charts:
            spec = json.loads(chart.proto.spec)
            self.assertTrue(spec['data'])
            self.assertTrue(spec['layout']['title']['text'])

    def navigate(self, section):
        self.app.radio(key='section').set_value(section).run(timeout=30)

    def test_every_section_and_demand_controls(self):
        self.check_charts(1)
        self.navigate('Demand and Hotspots')
        self.check_charts(6)
        self.app.selectbox(key='hotspot_count').set_value(20).run()
        self.app.selectbox(key='demand_zone').set_value('JFK Airport').run()
        self.check_charts(6)
        self.navigate('Recommendations')
        self.check_charts(0)
        rendered = [m.value for m in self.app.markdown]
        for rec in load_data()['recommendations']:
            self.assertIn(rec,rendered)

    def test_all_od_windows_and_borough_filter(self):
        self.navigate('OD and Time Patterns')
        for bucket in ['All day','morning_peak','midday','evening_peak','late_night']:
            self.app.selectbox(key='od_window').set_value(bucket).run()
            self.app.selectbox(key='od_borough').set_value('Manhattan').run()
            self.check_charts(2)
            self.assertTrue(any('Top 100' in c.value if bucket=='All day' else 'Top 25' in c.value for c in self.app.caption))

    def test_all_forecast_horizons_and_zones(self):
        self.navigate('Forecasting')
        d = load_data()
        for h in [24,48,72]:
            self.app.selectbox(key='forecast_horizon').set_value(h).run()
            for zone in ['All 10 forecast zones',*sorted(d[f'forecast_{h}'].pickup_zone_name.unique())]:
                self.app.selectbox(key='forecast_zone').set_value(zone).run()
                self.check_charts(1)
                metric = d['test_metrics'].loc[lambda x:x.horizon_hours.eq(h)].iloc[0]
                self.assertEqual(self.app.metric[0].value,f'{metric.baseline_mae:.4f}')
                self.assertEqual(self.app.metric[1].value,f'{metric.improved_mae:.4f}')


if __name__ == '__main__':
    unittest.main()
