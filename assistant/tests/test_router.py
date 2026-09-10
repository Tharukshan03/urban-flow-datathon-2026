import unittest

from assistant.analytics import load_bundle
from assistant.router import route_question


class RouterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_bundle()

    def test_top_pickup_routing(self):
        routed = route_question('What are the top 5 pickup zones?', self.bundle)
        self.assertEqual(routed.kind, 'top_pickups')

    def test_top_destination_routing(self):
        routed = route_question('Which destination zone is busiest?', self.bundle)
        self.assertEqual(routed.kind, 'top_destinations')

    def test_forecast_horizon_routing(self):
        routed = route_question('Which forecasting model should we use for 24 hours?', self.bundle)
        self.assertEqual(routed.kind, 'forecast_metrics')
        self.assertEqual(routed.horizon_hours, 24)

    def test_saved_forecast_routing(self):
        routed = route_question('What is the 24-hour forecast for JFK Airport?', self.bundle)
        self.assertEqual(routed.kind, 'saved_forecast')
        self.assertEqual(routed.zone_name, 'JFK Airport')

    def test_time_window_routing(self):
        routed = route_question('What are the strongest evening routes?', self.bundle)
        self.assertEqual(routed.kind, 'od_time')
        self.assertEqual(routed.time_bucket, 'evening_peak')

    def test_unknown_zone_routing(self):
        routed = route_question('What is demand in Springfield?', self.bundle)
        self.assertEqual(routed.kind, 'unknown_zone')

    def test_ambiguous_routing(self):
        routed = route_question('How busy is it?', self.bundle)
        self.assertEqual(routed.kind, 'clarify')

    def test_unsupported_routing(self):
        routed = route_question('Predict revenue next month', self.bundle)
        self.assertEqual(routed.kind, 'unsupported')

    def test_recommendation_routing(self):
        routed = route_question('What should fleet managers do during evening peaks?', self.bundle)
        self.assertEqual(routed.kind, 'recommendations')


if __name__ == '__main__':
    unittest.main()
