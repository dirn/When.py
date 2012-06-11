#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

import datetime
import os
import sys
import pytz

import when

sys.path.insert(0, os.path.abspath('..'))
sys.path.append('.')


class WhenTest(unittest.TestCase):
    def setUp(self):
        when.unset_utc()

        self.one_day = datetime.timedelta(days=1)
        self.one_second = datetime.timedelta(seconds=1)

        self.today = datetime.date.today()

        self.now = datetime.datetime.now()
        self.utc = datetime.datetime.utcnow()

        self.timezone = os.getenv('TIMEZONE', 'America/New_York')

    def test__add_time(self):
        # Test change between months with dfferent number of days
        test_value = datetime.datetime(2012, 3, 31)

        expected_value = datetime.datetime(2012, 5, 1)
        result = when._add_time(test_value, months=1)
        self.assertEqual(result, expected_value)

        # Test values going back into February of a leap year
        expected_value = datetime.datetime(2012, 3, 2)
        result = when._add_time(test_value, months=-1)
        self.assertEqual(result, expected_value)

        test_value = datetime.datetime(2012, 3, 30)

        expected_value = datetime.datetime(2012, 3, 1)
        result = when._add_time(test_value, months=-1)
        self.assertEqual(result, expected_value)

        test_value = datetime.datetime(2011, 3, 31)

        expected_value = datetime.datetime(2011, 3, 3)
        result = when._add_time(test_value, months=-1)
        self.assertEqual(result, expected_value)

        # Test leap day specifically
        test_value = datetime.datetime(2012, 2, 29)

        expected_value = datetime.datetime(2013, 3, 1)
        result = when._add_time(test_value, years=1)
        self.assertEqual(result, expected_value)

        expected_value = datetime.datetime(2011, 3, 1)
        result = when._add_time(test_value, years=-1)
        self.assertEqual(result, expected_value)

    def test_now(self):
        now = when.now()
        utc = when.now(True)

        # Unfortunately the clock keeps ticking each time we capture a value
        # for now so we can't do a direct comparison with assertEqual.
        # It's probably safe to assume the now function is working as long as
        # the difference is less than a second. There's probably a better way
        # to test this, but for now it's sufficient.
        self.assertTrue(now - self.now < self.one_second)
        self.assertTrue(utc - self.utc < self.one_second)

    def test_set_utc(self):
        when.set_utc()
        self.assertEqual(when._FORCE_UTC, True)

    def test_shift(self):
        first = when.shift(self.utc, from_tz='UTC', to_tz='America/New_York')
        second = when.shift(first, from_tz='America/New_York', to_tz='UTC')

        self.assertNotEqual(first, second)
        self.assertNotEqual(first, self.utc)
        self.assertEqual(second, self.utc)

        # Local time
        if self.timezone == 'UTC':
            # This block is needed for tests run in an environment set to UTC.
            first = when.shift(self.now, to_tz='America/New_York')
            second = when.shift(first, from_tz='America/New_York')
        else:
            first = when.shift(self.now, to_tz='UTC')
            second = when.shift(first, from_tz='UTC')

        self.assertNotEqual(first, second)
        self.assertNotEqual(first, self.now)
        self.assertEqual(second, self.now)

        # Set utc parameter to true
        first = when.shift(self.utc, to_tz='America/New_York', utc=True)
        second = when.shift(first, from_tz='America/New_York', utc=True)

        self.assertNotEqual(first, second)
        self.assertNotEqual(first, self.utc)
        self.assertEqual(second, self.utc)

        # Force UTC
        when.set_utc()
        first = when.shift(self.utc, to_tz='America/New_York')
        second = when.shift(first, from_tz='America/New_York')

        self.assertNotEqual(first, second)
        self.assertNotEqual(first, self.utc)
        self.assertEqual(second, self.utc)

    def test_timezone(self):
        # This test is tricky. In order for it to pass, the time zone needs to
        # be known ahead of time. When I run these tests locally, that's
        # America/New_York. If I have the tests run on travis-ci.org, that's
        # UTC. I've added an optional environment setting called TIMEZONE to
        # all this to be manually set. By default, UTC will be used.
        self.assertEqual(when.timezone(), self.timezone)

    def test_timezone_object(self):
        # This test is tricky. In order for it to pass, the time zone needs to
        # be known ahead of time. When I run these tests locally, that's
        # America/New_York. If I have the tests run on travis-ci.org, that's
        # UTC. I've added an optional environment setting called TIMEZONE to
        # all this to be manually set. By default, UTC will be used.
        local_timezone = pytz.timezone(self.timezone)
        self.assertEqual(when.timezone_object(), local_timezone)

    def test_timezones(self):
        # Make sure all_timezones() matches pytz's versions
        all_timezones = when.all_timezones()
        self.assertEqual(all_timezones, pytz.all_timezones)
        all_timezones_set = when.all_timezones_set()
        self.assertEqual(all_timezones_set, pytz.all_timezones_set)

        # Make sure common_timezones() matches pytz's versions
        common_timezones = when.common_timezones()
        self.assertEqual(common_timezones, pytz.common_timezones)
        common_timezones_set = when.common_timezones_set()
        self.assertEqual(common_timezones_set, pytz.common_timezones_set)

    def test_today(self):
        self.assertEqual(when.today(), self.today)

    def test_tomorrow(self):
        self.assertEqual(when.tomorrow(), self.today + self.one_day)

    def test_unset_utc(self):
        when.unset_utc()
        self.assertEqual(when._FORCE_UTC, False)

    def test_yesterday(self):
        self.assertEqual(when.yesterday(), self.today - self.one_day)

if __name__ == '__main__':
    unittest.main()
