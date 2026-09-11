"""Boundary checks for multi-step leakage and held-out metric accounting."""
import unittest
import numpy as np
import pandas as pd
from src.member3_forecasting import recursive_path, feature_frame, score


class ForecastChecks(unittest.TestCase):
    def test_recursive_lags_use_predictions_and_keep_history_unchanged(self):
        class IncrementModel:
            def __init__(self):
                self.inputs = []

            def predict(self, x):
                self.inputs.append(x.copy())
                return x[:, 0] + 1

        model = IncrementModel()
        history = np.zeros((168, 2))
        prediction = recursive_path(model, history, pd.date_range('2026-01-01', periods=72, freq='h'))
        np.testing.assert_array_equal(prediction[:, 0], np.arange(1, 73))
        np.testing.assert_array_equal(history, np.zeros((168, 2)))
        self.assertEqual(model.inputs[24][0, 1], 1)  # lag_24 now comes from a prediction
        self.assertEqual(model.inputs[48][0, 2], 1)  # lag_48 now comes from a prediction
        self.assertEqual(model.inputs[3][0, 4], 2)  # rolling mean uses predicted 1,2,3

    def test_features_at_origin_ignore_current_and_future_targets(self):
        dates = pd.date_range('2025-01-01', periods=220, freq='h')
        original = pd.DataFrame({'zone': np.arange(220, dtype=float)}, index=dates)
        changed = original.copy()
        changed.loc[dates[190]:, 'zone'] = 1e9
        before = feature_frame(original)
        after = feature_frame(changed)
        columns = before.columns.drop('target')
        pd.testing.assert_frame_equal(before.loc[:dates[190], columns], after.loc[:dates[190], columns])

    def test_horizons_include_only_their_requested_leads(self):
        data = pd.DataFrame({'split': 'test', 'forecast_origin': pd.Timestamp('2026-01-01'),
            'lead_hour': np.arange(1, 73), 'actual': 0,
            'baseline_forecast': np.r_[np.ones(24), np.full(48, 3)], 'improved_forecast': 2})
        metrics = score(data).set_index('horizon_hours')
        self.assertEqual(metrics.loc[24, 'baseline_mae'], 1)
        self.assertEqual(metrics.loc[24, 'winner'], 'Baseline')
        self.assertEqual(metrics.loc[72, 'winner'], 'Improved')
        self.assertEqual(metrics.loc[48, 'n_predictions'], 48)


if __name__ == '__main__':
    unittest.main()
