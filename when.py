# -*- coding: utf-8 -*-

""" Friendly Dates and Times """

# Disable pylint's invalid name warning. 'tz' is used in a few places and it
# should be the only thing causing pylint to include the warning.
# pylint: disable-msg=C0103

import calendar
import datetime
import locale
import os
import pytz
import random

# Some functions may take a parameter to designate a return value in UTC
# instead of local time.  This will be used to force them to return UTC
# regardless of the paramter's value.
_FORCE_UTC = False


class _FormatsMetaClass(type):
    """Allows the formats class to be treated as an iterable.

    It is important to understand has this class works.
    ``hasattr(formats, 'DATE')`` is true. ``'DATE' in formats` is false.
    ``hasattr(formats, 'D_FMT')`` is false. ``'D_FMT' in formats` is true.

    This is made possible through the ``__contains__`` and ``__getitem__``
    methods. ``__getitem__`` checks for the name of the attribute within
    the ``formats`` class. ``__contains__``, on the other hand, checks for
    the specified value assigned to an attribute of the class.
        pass
    """
    DATE = 'D_FMT'
    DATETIME = 'D_T_FMT'

    TIME = 'T_FMT'
    TIME_AMPM = 'T_FMT_AMPM'

    def __contains__(self, value):
        index = 0
        for attr in dir(_FormatsMetaClass):
            if not attr.startswith('__') and attr != 'mro' and \
                    getattr(_FormatsMetaClass, attr) == value:
                index = attr
                break
        return index

    def __getitem__(self, attr):
        return getattr(_FormatsMetaClass, attr)

    def __iter__(self):
        for attr in dir(_FormatsMetaClass):
            if not attr.startswith('__') and attr != 'mro':
                yield attr

formats = _FormatsMetaClass('formats', (object,), {})
formats.__doc__ = """A set of predefined datetime formats.

    .. versionadded:: 0.3.0
    """


def _add_time(value, years=0, months=0, weeks=0, days=0,
              hours=0, minutes=0, seconds=0, milliseconds=0, microseconds=0):
    assert _is_date_type(value)

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


def _is_date_type(value):
    # Acceptible types must be or extend:
    #    datetime.date
    #    datetime.time
    return isinstance(value, (datetime.date, datetime.time))


def all_timezones():
    """Get a list of all time zones.

    This is a wrapper for ``pytz.all_timezones``.

    :returns: list -- all time zones.

    .. versionadded:: 0.1.0
    """
    return pytz.all_timezones


def all_timezones_set():
    """Get a set of all time zones.

    This is a wrapper for ``pytz.all_timezones_set``.

    :returns: set -- all time zones.

    .. versionadded:: 0.1.0
    """
    return pytz.all_timezones_set


def common_timezones():
    """Get a list of common time zones.

    This is a wrapper for ``pytz.common_timezones``.

    :returns: list -- common time zones.

    .. versionadded:: 0.1.0
    """
    return pytz.common_timezones


def common_timezones_set():
    """Get a set of common time zones.

    This is a wrapper for ``pytz.common_timezones_set``.

    :returns: set -- common time zones.

    .. versionadded:: 0.1.0
    """
    return pytz.common_timezones_set


def ever():
    """Get a random datetime.

    Instead of using ``datetime.MINYEAR`` and ``datetime.MAXYEAR`` as the
    bounds, the current year +/- 100 is used. The thought behind this is that
    years that are too extreme will not be as useful.

    :returns: datetime.datetime -- a random datetime.

    .. versionadded:: 0.3.0
    """
    # Get the year bounds
    min_year = max(datetime.MINYEAR, today().year - 100)
    max_year = min(datetime.MAXYEAR, today().year + 100)

    # Get the random values
    year = random.randint(min_year, max_year)
    month = random.randint(1, 12)
    day = random.randint(1, calendar.mdays[month])
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    microsecond = random.randint(0, 1000000)

    return datetime.datetime(year=year, month=month, day=day, hour=hour,
                             minute=minute, second=second,
                             microsecond=microsecond)


def format(value, format_string):
    """Get a formatted version of a datetime.

    This is a wrapper for ``strftime()``. The full list of directives that can
    be used can be found at
    http://docs.python.org/library/datetime.html#strftime-strptime-behavior.
    Predefined formats are exposed through ``when.formats``:

    .. data:: when.formats.DATE

       Date in locale-based format.

    .. data:: when.formats.DATETIME

       Date and time in locale-based format.

    .. data:: when.formats.TIME

       Time in locale-based format.

    .. data:: when.formats.TIME_AMPM

       12-hour time in locale-based format.

    :param value: A datetime object.
    :type value: datetime.datetime, datetime.date, datetime.time.
    :param format_string: A string specifying formatting the directives or
                          to use.
    :type format_string: str.
    :returns: str -- the formatted datetime.
    :raises: AssertionError

    .. versionadded:: 0.3.0
    """

    assert _is_date_type(value)

    # Check to see if `format_string` is a value from the `formats` class. If
    # it is, obtain the real value from `locale.nl_langinfo()`.
    if format_string in formats:
        format_string = locale.nl_langinfo(getattr(locale, format_string))

    return value.strftime(format_string)


def future(years=0, months=0, weeks=0, days=0,
           hours=0, minutes=0, seconds=0, milliseconds=0, microseconds=0,
           utc=False):
    """Get a datetime in the future.

    ``future()`` accepts the all of the parameters of ``datetime.timedelta``,
    plus includes the parameters ``years`` and ``months``. ``years`` and
    ``months`` will add their respective units of time to the datetime.

    By default ``future()`` will return the datetime in the system's local
    time. If the ``utc`` parameter is set to ``True`` or ``set_utc()`` has been
    called, the datetime will be based on UTC instead.

    :param years: The number of years to add.
    :type years: int.
    :param months: The number of months to add.
    :type months: int.
    :param weeks: The number of weeks to add.
    :type weeks: int.
    :param days: The number of days to add.
    :type days: int.
    :param hours: The number of hours to add.
    :type hours: int.
    :param minutes: The number of minutes to add.
    :type minutes: int.
    :param seconds: The number of seconds to add.
    :type seconds: int.
    :param milliseconds: The number of milliseconds to add.
    :type milliseconds: int.
    :param microseconds: The number of microseconds to add.
    :type microseconds: int.
    :param utc: Whether or not to use UTC instead of local time.
    :type utc: bool.
    :returns: datetime.datetime -- the calculated datetime.

    .. versionadded:: 0.1.0
    """
    return _add_time(now(utc), years=years, months=months, weeks=weeks,
                     days=days, hours=hours, minutes=minutes, seconds=seconds,
                     milliseconds=milliseconds, microseconds=microseconds)


def how_many_leap_days(from_date, to_date):
    """Get the number of leap days between two dates

    :param from_date: A datetime object. If only a year is specified, will use
        January 1.
    :type from_date: datetime.datetime, datetime.date
    :param to_date: A datetime object.. If only a year is specified, will use
        January 1.
    :type to_date: datetime.datetime, datetime.date
    :returns: int -- the number of leap days.

    .. versionadded:: 0.3.0
    """
    if isinstance(from_date, int):
        from_date = datetime.date(from_date, 1, 1)

    if isinstance(to_date, int):
        to_date = datetime.date(to_date, 1, 1)

    assert _is_date_type(from_date) and \
        not isinstance(from_date, datetime.time)
    assert _is_date_type(to_date) and not isinstance(to_date, datetime.time)

    # Both `from_date` and `to_date` need to be of the same type. Since both
    # `datetime.date` and `datetime.datetime` will pass the above assertions,
    # cast any `datetime.datetime` values to `datetime.date`.
    if isinstance(from_date, datetime.datetime):
        from_date = from_date.date()
    if isinstance(to_date, datetime.datetime):
        to_date = to_date.date()

    assert from_date <= to_date

    number_of_leaps = calendar.leapdays(from_date.year, to_date.year)

    # `calendar.leapdays()` calculates the number of leap days by using
    # January 1 for the specified years. If `from_date` occurs after
    # February 28 in a leap year, remove one leap day from the total. If
    # `to_date` occurs after February 28 in a leap year, add one leap day to
    # the total.
    if calendar.isleap(from_date.year):
        month, day = from_date.month, from_date.day
        if month > 2 or (month == 2 and day > 28):
            number_of_leaps -= 1

    if calendar.isleap(to_date.year):
        month, day = to_date.month, to_date.day
        if month > 2 or (month == 2 and day > 28):
            number_of_leaps += 1

    return number_of_leaps


def is_5_oclock():
    # Congratulations, you've found an easter egg!
    #
    # Returns a `datetime.timedelta` object representing how much time is
    # remaining until 5 o'clock. If the current time is between 5pm and
    # midnight, a negative value will be returned. Keep in mind, a `timedelta`
    # is considered negative when the `days` attribute is negative; the values
    # for `seconds` and `microseconds` will always be positive.
    #
    # All values will be `0` at 5 o'clock.

    # Because this method deals with local time, the force UTC flag will need
    # to be turned off and back on if it has been set.
    force = _FORCE_UTC
    if force:
        unset_utc()

    # A `try` is used here to ensure that the UTC flag will be restored
    # even if an exception is raised when calling `now()`. This should never
    # be the case, but better safe than sorry.
    try:
        the_datetime = now()
    finally:
        if force:
            set_utc()

    five = datetime.time(17)

    return datetime.datetime.combine(the_datetime.date(), five) - the_datetime


def is_timezone_aware(value):
    """Check if a datetime is time zone aware.

    `is_timezone_aware()` is the inverse of `is_timezone_naive()`.

    :param value: A valid datetime object.
    :type value: datetime.datetime, datetime.time
    :returns: bool -- if the object is time zone aware.

    .. versionadded:: 0.3.0
    """
    assert hasattr(value, 'tzinfo')
    return value.tzinfo is not None and \
        value.tzinfo.utcoffset(value) is not None


def is_timezone_naive(value):
    """Check if a datetime is time zone naive.

    `is_timezone_naive()` is the inverse of `is_timezone_aware()`.

    :param value: A valid datetime object.
    :type value: datetime.datetime, datetime.time
    :returns: bool -- if the object is time zone naive.

    .. versionadded:: 0.3.0
    """
    assert hasattr(value, 'tzinfo')
    return value.tzinfo is None or value.tzinfo.utcoffset(value) is None


def now(utc=False):
    """Get a datetime representing the current date and time.

    By default ``now()`` will return the datetime in the system's local time.
    If the ``utc`` parameter is set to ``True`` or ``set_utc()`` has been
    called, the datetime will be based on UTC instead.

    :param utc: Whether or not to use UTC instead of local time.
    :type utc: bool.
    :returns: datetime.datetime -- the current datetime.

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

    :param years: The number of years to subtract.
    :type years: int.
    :param months: The number of months to subtract.
    :type months: int.
    :param weeks: The number of weeks to subtract.
    :type weeks: int.
    :param days: The number of days to subtract.
    :type days: int.
    :param hours: The number of hours to subtract.
    :type hours: int.
    :param minutes: The number of minutes to subtract.
    :type minutes: int.
    :param seconds: The number of seconds to subtract.
    :type seconds: int.
    :param milliseconds: The number of milliseconds to subtract.
    :type milliseconds: int.
    :param microseconds: The number of microseconds to subtract.
    :type microseconds: int.
    :param utc: Whether or not to use UTC instead of local time.
    :type utc: bool.
    :returns: datetime.datetime -- the calculated datetime.

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

    ``value`` will be converted from its time zone (when it is time zone aware)
    or the time zone specified by ``from_tz`` (when it is time zone naive) to
    the time zone specified by ``to_tz``. These values can either be strings
    containing the name of the time zone (see ``pytz.all_timezones`` for a list
    of all supported values) or a ``datetime.tzinfo`` object.

    If no value is provided for either ``from_tz`` (when ``value`` is time zone
    naive) or ``to_tz``, the current system time zone will be used. If the
    ``utc`` parameter is set to ``True`` or ``set_utc()`` has been called,
    however, UTC will be used instead.

    :param value: A datetime object.
    :type value: datetime.datetime, datetime.time.
    :param from_tz: The time zone to shift from.
    :type from_tz: datetime.tzinfo, str.
    :param to_tz: The time zone to shift to.
    :type to_tz: datetime.tzinfo, str.
    :param utc: Whether or not to use UTC instead of local time.
    :type utc: bool.
    :returns: datetime.datetime -- the calculated datetime.
    :raises: AssertionError

    .. versionchanged:: 0.3.0
       Added AssertionError for invalid values of ``value``
    """
    assert hasattr(value, 'tzinfo')

    # Check for a from timezone
    # If the datetime is time zone aware, its time zone should be used. If it's
    # naive, from_tz must be supplied.
    if is_timezone_aware(value):
        from_tz = value.tzinfo
    else:
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

    # If the datetime is time zone naive, pytz provides a convenient way to
    # covert it to time zone aware. Using replace() directly on the datetime
    # results in losing an hour when converting ahead.
    if is_timezone_naive(value):
        value = from_tz.localize(value)

    return value.astimezone(to_tz).replace(tzinfo=None)


def timezone():
    """Get the name of the current system time zone.

    :returns: str -- the name of the system time zone.

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
        localtime = pytz.tzfile.build_tzinfo('/etc/localtime',
                                             file('/etc/localtime'))

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

    :param tz_name: The name of the time zone.
    :type tz_name: str.
    :returns: datetime.tzinfo -- the time zone, defaults to system time zone.

    .. versionadded:: 0.1.0
    """
    return pytz.timezone(tz_name if tz_name else timezone())


def today():
    """Get a date representing the current date.

    :returns: datetime.date -- the current date.

    .. versionadded:: 0.1.0
    """
    return datetime.date.today()


def tomorrow():
    """Get a date representing tomorrow's date.

    :returns: datetime.date -- the current date plus one day.

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

    :returns: datetime.date -- the current date minus one day.

    .. versionadded:: 0.1.0
    """
    return datetime.date.today() - datetime.timedelta(days=1)
