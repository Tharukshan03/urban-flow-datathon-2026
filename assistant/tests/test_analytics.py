import unittest

from assistant.analytics import answer_question, load_bundle, preferred_model


class AnalyticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_bundle()

    def test_top_pickup_zone_answer(self):
        answer = answer_question('What are the top 5 pickup zones?', self.bundle)
        self.assertIn('Upper East Side South', answer.body)
        self.assertEqual(answer.kind, 'ranking')

    def test_top_destination_answer(self):
        answer = answer_question('Which destination zone is busiest?', self.bundle)
        self.assertIn('Upper East Side North', answer.body)

    def test_borough_demand_answer(self):
        answer = answer_question('Which borough has the most pickup demand?', self.bundle)
        self.assertIn('Manhattan', answer.body)

    def test_hourly_and_weekday_answers(self):
        hourly = answer_question('What time of day is demand highest?', self.bundle)
        weekday = answer_question('Which weekday has the highest demand?', self.bundle)
        self.assertEqual(hourly.kind, 'single')
        self.assertEqual(weekday.kind, 'single')
        self.assertIn('highest retained demand', weekday.body)

    def test_od_routes_and_time_window(self):
        overall = answer_question('What is the strongest OD route?', self.bundle)
        evening = answer_question('What are the strongest evening routes?', self.bundle)
        zone = answer_question('Where do trips from Upper East Side South usually go?', self.bundle)
        self.assertIn('Upper East Side South', overall.body)
        self.assertIn('evening', evening.body.lower())
        self.assertIn('Upper East Side South', zone.body)

    def test_forecast_model_comparison(self):
        answer_24 = answer_question('Which forecasting model should we use for 24 hours?', self.bundle)
        answer_72 = answer_question('What about 72 hours?', self.bundle)
        self.assertIn('24-hour planning', answer_24.body)
        self.assertIn('72-hour planning', answer_72.body)

    def test_saved_forecast(self):
        answer = answer_question('What is the 24-hour forecast for JFK Airport?', self.bundle)
        self.assertIn('JFK Airport', answer.body)
        self.assertEqual(answer.kind, 'forecast')

    def test_recommendations(self):
        answer = answer_question('What should fleet managers do during evening peaks?', self.bundle)
        self.assertEqual(answer.kind, 'recommendations')
        self.assertEqual(len(self.bundle.recommendations), 5)

    def test_unsupported_and_clarification(self):
        unsupported = answer_question('Predict revenue next month', self.bundle)
        vague = answer_question('How busy is it?', self.bundle)
        self.assertEqual(unsupported.kind, 'unsupported')
        self.assertEqual(vague.kind, 'clarify')

    def test_unknown_zone_suggestions(self):
        answer = answer_question('What is demand in Springfield?', self.bundle)
        self.assertIn('could not find', answer.body.lower())

    def test_forecast_model_matches_track_6(self):
        metrics = self.bundle.tables['metrics'].loc[self.bundle.tables['metrics'].split.eq('test')].sort_values('horizon_hours')
        winners = [preferred_model(row) for row in metrics.itertuples()]
        self.assertEqual(winners, ['improved', 'baseline', 'baseline'])


if __name__ == '__main__':
    unittest.main()
