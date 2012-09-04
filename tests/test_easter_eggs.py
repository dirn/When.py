#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

import datetime
import mock
import os
import sys

import when

sys.path.insert(0, os.path.abspath('..'))
sys.path.append('.')


class WhenEasterEggTest(unittest.TestCase):
    def test_is_5_oclock(self):
        """Testing an easter egg..."""
        # Test when.is_5_clock()

        with mock.patch('when.now') as mock_now:
            # Test that it's before 5 o'clock
            mock_now.return_value = datetime.datetime(2012, 9, 3, 16)
            countdown = when.is_5_oclock()
            self.assertTrue(countdown.days >= 0)

            # Test that it *is* 5 o'clock
            mock_now.return_value = datetime.datetime(2012, 9, 3, 17)
            countdown = when.is_5_oclock()
            self.assertTrue(countdown.days == 0)
            self.assertTrue(countdown.seconds == 0)
            self.assertTrue(countdown.microseconds == 0)

            # Test that it's after 5 o'clock
            mock_now.return_value = datetime.datetime(2012, 9, 3, 18)
            countdown = when.is_5_oclock()
            self.assertTrue(countdown.days < 0)

if __name__ == '__main__':
    unittest.main()
