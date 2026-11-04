import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.daybook_today import today_view, tomorrow_view

NOW = datetime(2026, 11, 4, 9, 30)
CACHE = {
    'fetched_at': '2026-11-04T08:15', 'date': '2026-11-04',
    'agenda': {'overdue': [{'title': 'Renew licence'}], 'today': [{'title': 'Pack chargers'}],
               'birthdays': [{'name': 'Anna', 'days_until': 0}, {'name': 'Joan', 'days_until': 3}]},
    'weather': [{'date': '2026-11-04', 'temp_min': 9.6, 'temp_max': 17.2, 'condition': 'rainy'},
                {'date': '2026-11-05', 'temp_min': 11, 'temp_max': 19, 'condition': 'sunny'}],
    'roster': {'2026-11-04': {'duty_type': 'day_off', 'stretch': {'day': 2, 'of': 4}},
               '2026-11-05': {'duty_type': 'flying_duty', 'report_time': '06:15:00'}},
    'trip_days': {'2026-11-05': {'trip': 'Taiwan', 'note': 'Taipei → Hualien by train'}},
    'on_this_day': {'years': [{'date': '2026-11-04', 'notes': 'today'}, {'date': '2019-11-04', 'trip_city': 'Taipei'},
                              {'date': '2021-11-04', 'notes': 'Quiet day\nsecond line'}]},
}


class TodayViewTest(unittest.TestCase):
    def test_fresh_cache(self):
        v = today_view(CACHE, NOW)
        self.assertEqual((v['weekday'], v['day'], v['month']), ('Wednesday', '4', 'November'))
        self.assertEqual(v['weather'], '10–17° rain')
        self.assertEqual(v['duty'], 'Day off · 2 of 4')
        self.assertEqual(v['tasks'], [('overdue', 'Renew licence'), ('today', 'Pack chargers')])
        self.assertEqual(v['birthdays'], ['Anna'])
        self.assertEqual(v['on_this_day'], '2021 · Quiet day')   # newest past year first, current year skipped
        self.assertEqual(v['updated'], '08:15')
        self.assertFalse(v['stale'])

    def test_yesterdays_cache_shows_no_tasks(self):
        v = today_view(dict(CACHE, date='2026-11-03'), NOW)
        self.assertEqual(v['tasks'], [])
        self.assertTrue(v['stale'])
        self.assertEqual(v['updated'], '')

    def test_empty_cache(self):
        v = today_view({}, NOW)
        self.assertFalse(v['stale'])
        self.assertEqual(v['tasks'], [])


class TomorrowViewTest(unittest.TestCase):
    def test_duty_trip_weather(self):
        t = tomorrow_view(CACHE, NOW)
        self.assertEqual(t['label'], 'Thursday 5 November')
        self.assertEqual(t['duty'], 'Flying · report 06:15')
        self.assertEqual(t['trip'], {'trip': 'Taiwan', 'note': 'Taipei → Hualien by train'})
        self.assertEqual(t['weather'], '11–19° sunny')

    def test_nothing_tomorrow(self):
        cache = dict(CACHE, roster={}, trip_days={})
        self.assertIsNone(tomorrow_view(cache, NOW))

    def test_old_cache_is_ignored(self):
        self.assertIsNone(tomorrow_view(dict(CACHE, date='2026-10-30'), NOW))


if __name__ == '__main__':
    unittest.main()
