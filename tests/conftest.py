"""Test fixtures."""

import datetime
import os

import pytest


@pytest.fixture
def now():
    """Return the current datetime."""
    return datetime.datetime.now()


@pytest.fixture
def one_day():
    """Return a timedelta representing one day."""
    return datetime.timedelta(days=1)


@pytest.fixture
def timezone():
    """Return the name of the current time zone."""
    try:
        timezone = os.environ['TIMEZONE']
    except KeyError:
        timezone = 'America/New_York'

    return timezone


@pytest.fixture
def today():
    """Return today's date."""
    return datetime.date.today()
