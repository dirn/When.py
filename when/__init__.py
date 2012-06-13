# -*- coding: utf-8 -*-

""" Friendly Dates and Times """

# Disable pylint's invalid name warning. 'tz' is used in a few places and it
# should be the only thing causing pylint to include the warning.
# pylint: disable-msg=C0103

import calendar
import datetime
import os
import pytz

# Some functions may take a parameter to designate a return value in UTC
# instead of local time.  This will be used to force them to return UTC
# regardless of the paramter's value.
_FORCE_UTC = False


def _add_time(value, years=0, months=0, weeks=0, days=0,
              hours=0, minutes=0, seconds=0, milliseconds=0, microseconds=0):
    # If any of the standard timedelta values are used, use timedelta for them.
    if seconds or minutes or hours or days or weeks:
        delta = datetime.timedelta(weeks=weeks, days=days, hours=hours,
                                   minutes=minutes, seconds=seconds,
                                   milliseconds=milliseconds,
                                   microseconds=microseconds)
        value += delta

    # Months are tricky. If the current month plus the requested number of
    # months is greater than 12 (or less than 1), we'll get a ValueError. After
    # figuring out the number of years and months from the number of months,
    # shift the values so that we get a valid month.
    if months:
        more_years, months = divmod(months, 12)
        years += more_years

        if not (1 <= months + value.month <= 12):
            more_years, months = divmod(months + value.month, 12)
            months -= value.month
            years += more_years

    if months or years:
        year = value.year + years
        month = value.month + months

        # When converting from a day in amonth that doesn't exist in the
        # ending month, a ValueError will be raised. What follows is an ugly,
        # ugly hack to get around this.
        try:
            value = value.replace(year=year, month=month)
        except ValueError:
            # When the day in the origin month isn't in the destination month,
            # the total number of days in the destination month is needed.
            # calendar.mdays would be a nice way to do this except it doesn't
            # account for leap years at all; February always has 28 days.
            _, destination_days = calendar.monthrange(year, month)

            # I am reluctantly writing this comment as I fear putting the
            # craziness of the hack into writing, but I don't want to forget
            # what I was doing here so I can fix it later.
            #
            # The new day will either be 1, 2, or 3. It will be determined by
            # the difference in days between the day value of the datetime
            # being altered and the number of days in the destination month.
            # After that, month needs to be incremented. If that puts the new
            # date into January (the value will be 13), year will also need to
            # be incremented (with month being switched to 1).
            #
            # Once all of that has been figured out, a simple replace will do
            # the trick.
            day = value.day - destination_days
            month += 1
            if month > 12:
                month = 1
                year += 1
            value = value.replace(year=year, month=month, day=day)

    return value


def how_many_leap_days(t1, t2):
    """Returns the number of leap days included in the range that especified
    by the arguments

    t1 -- datetime
    t2 -- datetime

    Returns integer counter
    """
    """Returns the number of leap days in a range.

    ``how_many_leap_days()`` accepts two datetime objects and will return
    an integer counter containing the number of leap days in the range that
    is contained within the two dates, limits included.

    .. versionadded:: 0.1.x
    """

    _is_leap_year = lambda x: (x % 4 == 0 and x % 100 != 0) or x % 400 == 0

    count = 0

    if t1.month <= 2 and t1.day <= 28:
        if _is_leap_year(t1.year):
            count += 1

    if t2.month >= 2 and t2.day > 28 and t1.year != t2.year:
        if _is_leap_year(t1.year):
            count += 1

    for year in xrange(t1.year + 1, t2.year):
        if _is_leap_year(year):
            count += 1

    return count


def all_timezones():
    """Get a list of all time zones.

    This is a wrapper for ``pytz.all_timezones``.

    .. versionadded:: 0.1.0
    """
    return pytz.all_timezones


def all_timezones_set():
    """Get a set of all time zones.

    This is a wrapper for ``pytz.all_timezones_set``.

    .. versionadded:: 0.1.0
    """
    return pytz.all_timezones_set


def common_timezones():
    """Get a list of common time zones.

    This is a wrapper for ``pytz.common_timezones``.

    .. versionadded:: 0.1.0
    """
    return pytz.common_timezones


def common_timezones_set():
    """Get a set of common time zones.

    This is a wrapper for ``pytz.common_timezones_set``.

    .. versionadded:: 0.1.0
    """
    return pytz.common_timezones_set


def future(years=0, months=0, weeks=0, days=0,
           hours=0, minutes=0, seconds=0, milliseconds=0, microseconds=0,
           utc=False):
    """Get a datetime in the future.

    ``future()`` accepts the all of the parameters of ``datetime.timedelta``,
    plus includes the parameters ``years`` and ``months``. ``years`` and
    ``months`` will add their respective units of time to the datetime.

    By default ``future()`` will return the datetime in the system's local time.
    If the ``utc`` parameter is set to ``True`` or ``set_utc()`` has been
    called, the datetime will be based on UTC instead.

    .. versionadded:: 0.1.0
    """
    return _add_time(now(utc), years=years, months=months, weeks=weeks,
                     days=days, hours=hours, minutes=minutes, seconds=seconds,
                     milliseconds=milliseconds, microseconds=microseconds)


def now(utc=False):
    """Get a datetime representing the current date and time.

    By default ``now()`` will return the datetime in the system's local time.
    If the ``utc`` parameter is set to ``True`` or ``set_utc()`` has been
    called, the datetime will be based on UTC instead.

    .. versionadded:: 0.1.0
    """
    if _FORCE_UTC or utc:
        return datetime.datetime.utcnow()
    else:
        return datetime.datetime.now()


def past(years=0, months=0, weeks=0, days=0,
           hours=0, minutes=0, seconds=0, milliseconds=0, microseconds=0,
           utc=False):
    """Get a datetime in the past.

    ``past()`` accepts the all of the parameters of ``datetime.timedelta``,
    plus includes the parameters ``years`` and ``months``. ``years`` and
    ``months`` will add their respective units of time to the datetime.

    By default ``past()`` will return the datetime in the system's local time.
    If the ``utc`` parameter is set to ``True`` or ``set_utc()`` has been
    called, the datetime will be based on UTC instead.

    .. versionadded:: 0.1.0
    """
    return _add_time(now(utc), years=-years, months=-months, weeks=-weeks,
                     days=-days, hours=-hours, minutes=-minutes,
                     seconds=-seconds, milliseconds=milliseconds,
                     microseconds=microseconds)


def set_utc():
    """Set all datetimes to UTC.

    The ``utc`` parameter of other methods will be ignored, with the global
    setting taking precedence.

    This can be reset by calling ``unset_utc()``.

    .. versionadded:: 0.1.0
    """
    global _FORCE_UTC  # Causes pylint W0603
    _FORCE_UTC = True


def shift(value, from_tz=None, to_tz=None, utc=False):
    """Convert a datetime from one time zone to another.

    ``value`` will be converted from the time zone specified by ``from_tz`` to
    the time zone specified by ``to_tz``. This values can either be strings
    containing the name of the time zone (see ``pytz.all_timezones`` for a list
    of all supported values) or a ``datetime.tzinfo`` object.

    If no value is provided for either ``from_tz`` or ``to_tz``, the current
    system time zone will be used. If the ``utc`` parameter is set to ``True``
    or ``set_utc()`` has been called, however, UTC will be used instead.

    At this time, time zone aware datetimes are not supported.

    .. versionadded:: 0.1.0
    """
    # Check for a from timezone
    if not from_tz:
        if _FORCE_UTC or utc:
            from_tz = pytz.UTC
        else:
            from_tz = timezone_object()  # Use the system's time zone
    else:
        if not isinstance(from_tz, datetime.tzinfo):
            # This will raise pytz.UnknownTimeZoneError
            from_tz = pytz.timezone(from_tz)

    # Check for a to timezone
    if not to_tz:
        if _FORCE_UTC or utc:
            to_tz = pytz.UTC
        else:
            to_tz = timezone_object()  # Use the system's time zone
    else:
        if not isinstance(to_tz, datetime.tzinfo):
            # This will raise pytz.UnknownTimeZoneError
            to_tz = pytz.timezone(to_tz)

    if from_tz == to_tz:
        return value

    return from_tz.localize(value).astimezone(to_tz).replace(tzinfo=None)


def timezone():
    """Get the name of the current system time zone.

    .. versionadded:: 0.1.0
    """
    def _inner():
        """ check for the time zone:
            1. as an environment setting (most likely not)
            2. in /etc/timezone (hopefully)
            3. in /etc/localtime (last chance)

        """
        tz = _timezone_from_env()  # 1
        if tz is not None:
            return tz

        tz = _timezone_from_etc_timezone()  # 2
        if tz is not None:
            return tz

        tz = _timezone_from_etc_localtime()  # 3
        if tz is not None:
            return tz

    return '{0}'.format(_inner())


def _timezone_from_env():
    """ get the system time zone from os.environ """
    if 'TZ' in os.environ:
        try:
            return pytz.timezone(os.environ['TZ'])
        except pytz.UnknownTimeZoneError:
            pass

    return None


def _timezone_from_etc_localtime():
    """ get the system time zone from /etc/loclatime """
    matches = []
    if os.path.exists('/etc/localtime'):
        localtime = pytz.tzfile.build_tzinfo('/etc/localtime', file('/etc/localtime'))

        for tzname in pytz.all_timezones:
            tz = pytz.timezone(tzname)

            if dir(tz) != dir(localtime):
                continue

            for attr in dir(tz):
                if callable(getattr(tz, attr)) or attr.startswith('__'):
                    continue

                if attr == 'zone' or attr == '_tzinfos':
                    continue

                if getattr(tz, attr) != getattr(localtime, attr):
                    break

            else:
                matches.append(tzname)

        if matches:
            return pytz.timezone(matches[0])
        else:
            # Causes pylint W0212
            pytz._tzinfo_cache['/etc/localtime'] = localtime
            return localtime


def _timezone_from_etc_timezone():
    """ get the system time zone from /etc/timezone """
    if os.path.exists('/etc/timezone'):
        tz = file('/etc/timezone').read().strip()
        try:
            return pytz.timezone(tz)
        except pytz.UnknownTimeZoneError:
            pass

    return None


def timezone_object(tz_name=None):
    """Get the current system time zone.

    This returns a ``datetime.tzinfo`` instance.

    .. versionadded:: 0.1.0
    """
    return pytz.timezone(tz_name if tz_name else timezone())


def today():
    """Get a date representing the current date.

    .. versionadded:: 0.1.0
    """
    return datetime.date.today()


def tomorrow():
    """Get a date representing tomorrow's date.

    .. versionadded:: 0.1.0
    """
    return datetime.date.today() + datetime.timedelta(days=1)


def unset_utc():
    """Set all datetimes to system time.

    The ``utc`` parameter of other methods will be used.

    This can be changed by calling ``set_utc()``.

    .. versionadded:: 0.1.0
    """
    global _FORCE_UTC  # Causes pylint W0603
    _FORCE_UTC = False


def yesterday():
    """Get a date representing yesterday's date.

    .. versionadded:: 0.1.0
    """
    return datetime.date.today() - datetime.timedelta(days=1)
