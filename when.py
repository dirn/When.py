"""Friendly Dates and Times."""

import calendar
try:
    from contextlib import suppress
except ImportError:
    # The following is from the Python 3 source.
    class suppress:  # NOQA
        """Context manager to suppress specified exceptions
        After the exception is suppressed, execution proceeds with the next
        statement following the with statement.
            with suppress(FileNotFoundError):
                os.remove(somefile)
            # Execution still resumes here if the file was already removed
        """

        def __init__(self, *exceptions):  # NOQA
            self._exceptions = exceptions

        def __enter__(self):  # NOQA
            pass

        def __exit__(self, exctype, excinst, exctb):  # NOQA
            # Unlike isinstance and issubclass, CPython exception handling
            # currently only looks at the concrete type hierarchy (ignoring
            # the instance and subclass checking hooks). While Guido considers
            # that a bug rather than a feature, it's a fairly hard one to fix
            # due to various internal implementation details. suppress provides
            # the simpler issubclass based semantics, rather than trying to
            # exactly reproduce the limitations of the CPython interpreter.
            #
            # See http://bugs.python.org/issue12029 for more details
            return (
                exctype is not None and issubclass(exctype, self._exceptions))
import datetime
import locale
import os
import random
from warnings import warn

import pytz

__version__ = '0.4.0'

# Some functions may take a parameter to designate a return value in UTC
# instead of local time.  This will be used to force them to return UTC
# regardless of the paramter's value.
_FORCE_UTC = False


class _FormatsMetaClass(type):
    """An iterable formats class.

    It is important to understand how this class works.
    ``hasattr(formats, 'DATE')`` is true. ``'DATE' in formats` is false.
    ``hasattr(formats, 'D_FMT')`` is false. ``'D_FMT' in formats` is
    true.

    This is made possible through the ``__contains__`` and
    ``__getitem__`` methods. ``__getitem__`` checks for the name of the
    attribute within the ``formats`` class. ``__contains__``, on the
    other hand, checks for the specified value assigned to an attribute
    of the class.
    """

    DATE = 'D_FMT'
    DATETIME = 'D_T_FMT'

    TIME = 'T_FMT'
    TIME_AMPM = 'T_FMT_AMPM'

    def __contains__(self, value):
        index = 0
        for attr in dir(_FormatsMetaClass):
            if (not attr.startswith('__') and
                    attr != 'mro' and
                    getattr(_FormatsMetaClass, attr) == value):
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


def _add_time(value, years=0, months=0, weeks=0, days=0, hours=0, minutes=0,
              seconds=0, milliseconds=0, microseconds=0):
    """Return a datetime with units of time added to it.

    This function creates a :class:`~datetime.timedelta` instance from
    the parameters passed info it and adds it to ``value``. The
    parameters not supported by :class:`~datetime.timedelta`--``months``
    and ``years``--are then applied to ``value``.

    Args:
        value (datetime.datetime, datetime.date, datetime.time): The
            original value to which to add the units of time.
        years (Optional[int]): The number of years to add. Defaults to
            0.
        months (Optional[int]): The number of months to add. Defaults to
            0.
        weeks (Optional[int]): The number of weeks to add. Defaults to
            0.
        days (Optional[int]): The number of days to add. Defaults to 0.
        hours (Optional[int]): The number of hours to add. Defaults to
            0.
        minutes (Optional[int]): The number of minutes to add. Defaults
            to 0.
        seconds (Optional[int]): The number of seconds to add. Defaults
            to 0.
        milliseconds (Optional[int]): The number of milliseconds to add.
            Defaults to 0.
        microseconds (Optional[int]): The number of microseconds to add.
            Defaults to 0.

    Returns:
        datetime.datetime, datetime.date, datetime.time: The newly
            calculated value.

    Raises:
        TypeError: If ``value`` isn't a valid datetime type.
    """
    if not _is_date_type(value):
        message = "'{0}' object is not a valid date or time."
        raise TypeError(message.format(type(value).__name__))

    # If any of the standard timedelta values are used, use timedelta
    # for them.
    if seconds or minutes or hours or days or weeks:
        delta = datetime.timedelta(
            weeks=weeks,
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            milliseconds=milliseconds,
            microseconds=microseconds,
        )
        value += delta

    # Months are tricky. If the current month plus the requested number
    # of months is greater than 12 (or less than 1), we'll get a
    # ValueError. After figuring out the number of years and months from
    # the number of months, shift the values so that we get a valid
    # month.
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
        # ending month, a ValueError will be raised. What follows is an
        # ugly, ugly hack to get around this.
        try:
            value = value.replace(year=year, month=month)
        except ValueError:
            # When the day in the origin month isn't in the destination
            # month, the total number of days in the destination month
            # is needed. calendar.mdays would be a nice way to do this
            # except it doesn't account for leap years at all; February
            # always has 28 days.
            _, destination_days = calendar.monthrange(year, month)

            # I am reluctantly writing this comment as I fear putting
            # the craziness of the hack into writing, but I don't want
            # to forget what I was doing here so I can fix it later.
            #
            # The new day will either be 1, 2, or 3. It will be
            # determined by the difference in days between the day value
            # of the datetime being altered and the number of days in
            # the destination month. After that, month needs to be
            # incremented. If that puts the new date into January (the
            # value will be 13), year will also need to be incremented
            # (with month being switched to 1).
            #
            # Once all of that has been figured out, a simple replace
            # will do the trick.
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
    """Return a list of all time zones.

    This is a wrapper for ``pytz.all_timezones``.

    Returns:
        list: All time zones.
    """
    return pytz.all_timezones


def all_timezones_set():
    """Return a set of all time zones.

    This is a wrapper for ``pytz.all_timezones_set``.

    Returns:
        set: All time zones.
    """
    return pytz.all_timezones_set


def common_timezones():
    """Return a list of common time zones.

    This is a wrapper for ``pytz.common_timezones``.

    Returns:
        list: Common time zones.
    """
    return pytz.common_timezones


def common_timezones_set():
    """Return a set of common time zones.

    This is a wrapper for ``pytz.common_timezones_set``.

    Returns:
        set: Common time zones.
    """
    return pytz.common_timezones_set


def ever():
    """Return a random datetime.

    Instead of using ``datetime.MINYEAR`` and ``datetime.MAXYEAR`` as
    the bounds, the current year +/- 100 is used. The thought behind
    this is that years that are too extreme will not be as useful.

    Returns:
        datetime.datetime: A random datetime.

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
    """Return a formatted version of a datetime.

    This is a wrapper for :meth:`~datetime.datetime.strftime`. The full
    list of directives that can be used can be found at
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

    Args:
        value (datetime.datetime): A datetime object.
        format_string (str): A string specifying format directives to
            use.

    Returns:
        str: The formatted datetime.

    Raises:
        TypeError: If ``value`` isn't a valid datetime type.

    .. versionchanged:: 0.4.0

        ``TypeError`` is now raised for invalid datetime types.

    .. versionadded:: 0.3.0
    """
    if not _is_date_type(value):
        message = "'{0}' object is not a valid date or time."
        raise TypeError(message.format(type(value).__name__))

    # Check to see if `format_string` is a value from the `formats`
    # class. If it is, obtain the real value from
    # `locale.nl_langinfo()`.
    if format_string in formats:
        format_string = locale.nl_langinfo(getattr(locale, format_string))

    return value.strftime(format_string)


def future(years=0, months=0, weeks=0, days=0, hours=0, minutes=0,
           seconds=0, milliseconds=0, microseconds=0, utc=False):
    """Return a datetime in the future.

    :func:`~when.future` accepts the all of the parameters of
    :class:`~datetime.timedelta`, plus includes the parameters ``years``
    and ``months``. ``years`` and ``months`` will add their respective
    units of time to the datetime.

    By default :func:`~when.future` will return the datetime in the
    system's local time. If the ``utc`` parameter is set to ``True`` or
    :func:`~when.set_utc` has been called, the datetime will be based on
    UTC instead.

    Args:
        years (Optional[int]): The number of years to add. Defaults to
            0.
        months (Optional[int]): The number of months to add. Defaults to
            0.
        weeks (Optional[int]): The number of weeks to add. Defaults to
            0.
        days (Optional[int]): The number of days to add. Defaults to 0.
        hours (Optional[int]): The number of hours to add. Defaults to
            0.
        minutes (Optional[int]): The number of minutes to add. Defaults
            to 0.
        seconds (Optional[int]): The number of seconds to add. Defaults
            to 0.
        milliseconds (Optional[int]): The number of milliseconds to
            add. Defaults to 0.
        microseconds (Optional[int]): The number of microseconds to
            add. Defaults to 0.
        utc (Optional[bool]): Whether or not to use UTC instead of local
            time.  Defaults to False.

    Returns:
        datetime.datetime: The calculated datetime.
    """
    return _add_time(now(utc), years=years, months=months, weeks=weeks,
                     days=days, hours=hours, minutes=minutes, seconds=seconds,
                     milliseconds=milliseconds, microseconds=microseconds)


def how_many_leap_days(from_date, to_date):
    """Return the number of leap days between two dates.

    Args:
        from_date (datetime.datetime, datetime.date): The datetime at
            the beginning of the range.
        to_date (datetime.datetime, datetime.date): The datetime at the
            end of the range.

    Returns:
        int: The number of leap days.

    Raises:
        TypeError: If ``from_date`` or ``two_date`` isn't a valid
            datetime type.
        ValueError: If ``from_date`` occurs after ``to_date``.


    .. versionchanged:: 0.4.0

        ``TypeError`` and ``ValueError`` are now raised.

        A deprecation warning will be raised when ``from_date`` or
        ``to_date`` is an integer.

    .. versionadded:: 0.3.0
    """
    if isinstance(from_date, int):
        warn(
            "In the future 'from_date' must be a datetime.",
            DeprecationWarning,
        )
        from_date = datetime.date(from_date, 1, 1)

    if isinstance(to_date, int):
        warn("In the future 'to_date' must be a datetime.", DeprecationWarning)
        to_date = datetime.date(to_date, 1, 1)

    if not _is_date_type(from_date):
        message = "'{0}' object is not a valid date or time."
        raise TypeError(message.format(type(from_date).__name__))
    if not _is_date_type(to_date):
        message = "'{0}' object is not a valid date or time."
        raise TypeError(message.format(type(to_date).__name__))

    # Both `from_date` and `to_date` need to be of the same type.
    # Since both `datetime.date` and `datetime.datetime` will pass the
    # above assertions, cast any `datetime.datetime` values to
    # `datetime.date`.
    if isinstance(from_date, datetime.datetime):
        from_date = from_date.date()
    if isinstance(to_date, datetime.datetime):
        to_date = to_date.date()

    if from_date > to_date:
        raise ValueError(
            "The value of 'from_date' must be before the value of 'to_date'.")

    number_of_leaps = calendar.leapdays(from_date.year, to_date.year)

    # `calendar.leapdays()` calculates the number of leap days by using
    # January 1 for the specified years. If `from_date` occurs after
    # February 28 in a leap year, remove one leap day from the total. If
    # `to_date` occurs after February 28 in a leap year, add one leap
    # day to the total.
    if calendar.isleap(from_date.year):
        month, day = from_date.month, from_date.day
        if month > 2 or (month == 2 and day > 28):
            number_of_leaps -= 1

    if calendar.isleap(to_date.year):
        month, day = to_date.month, to_date.day
        if month > 2 or (month == 2 and day > 28):
            number_of_leaps += 1

    return number_of_leaps


def is_5_oclock():  # noqa
    # Congratulations, you've found an easter egg!
    #
    # Returns a `datetime.timedelta` object representing how much time
    # is remaining until 5 o'clock. If the current time is between 5pm
    # and midnight, a negative value will be returned. Keep in mind, a
    # `timedelta` is considered negative when the `days` attribute is
    # negative; the values for `seconds` and `microseconds` will always
    # be positive.
    #
    # All values will be `0` at 5 o'clock.

    # Because this method deals with local time, the force UTC flag will
    # need to be turned off and back on if it has been set.
    force = _FORCE_UTC
    if force:
        unset_utc()

    # A `try` is used here to ensure that the UTC flag will be restored
    # even if an exception is raised when calling `now()`. This should
    # never be the case, but better safe than sorry.
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

    Args:
        value (datetime.datetime): A datetime object.

    Returns:
        bool: Whether or not ``value`` is time zone aware.

    Raises:
        TypeError: If ``value`` isn't a valid datetime type.

    .. versionchanged:: 0.4.0

        ``TypeError`` is raised

    .. versionadded:: 0.3.0
    """
    if not hasattr(value, 'tzinfo'):
        message = "'{0}' object is not a valid time."
        raise TypeError(message.format(type(value).__name__))

    return not (value.tzinfo is None or value.tzinfo.utcoffset(value) is None)


def is_timezone_naive(value):
    """Check if a datetime is time zone naive.

    `is_timezone_naive()` is the inverse of `is_timezone_aware()`.

    Args:
        value (datetime.datetime): A datetime object.

    Returns:
        bool: Whether or not ``value`` is time zone naive.

    Raises:
        TypeError: If ``value`` isn't a valid datetime type.

    .. versionchanged:: 0.4.0

        ``TypeError`` is now raised

    .. versionadded:: 0.3.0
    """
    if not hasattr(value, 'tzinfo'):
        message = "'{0}' object is not a valid time."
        raise TypeError(message.format(type(value).__name__))

    return value.tzinfo is None or value.tzinfo.utcoffset(value) is None


def now(utc=False):
    """Return a datetime representing the current date and time.

    By default ``now()`` will return the datetime in the system's local
    time. If the ``utc`` parameter is set to ``True`` or ``set_utc()``
    has been called, the datetime will be based on UTC instead.

    Args:
        utc (Optional[bool]): Whether or not to use UTC instead of local
            time. Defaults to False.

    Returns:
        datetime.datetime: The current datetime.
    """
    if _FORCE_UTC or utc:
        return datetime.datetime.utcnow()
    else:
        return datetime.datetime.now()


def past(years=0, months=0, weeks=0, days=0, hours=0, minutes=0, seconds=0,
         milliseconds=0, microseconds=0, utc=False):
    """Return a datetime in the past.

    ``past()`` accepts the all of the parameters of
    ``datetime.timedelta``, plus includes the parameters ``years`` and
    ``months``. ``years`` and ``months`` will add their respective units
    of time to the datetime.

    By default ``past()`` will return the datetime in the system's local
    time. If the ``utc`` parameter is set to ``True`` or ``set_utc()``
    has been called, the datetime will be based on UTC instead.

        years (Optional[int]): The number of years to add. Defaults to
            0.
        months (Optional[int]): The number of months to add. Defaults to
            0.
        weeks (Optional[int]): The number of weeks to add. Defaults to
            0.
        days (Optional[int]): The number of days to add. Defaults to
            0.
        hours (Optional[int]): The number of hours to add. Defaults to
            0.
        minutes (Optional[int]): The number of minutes to add. Defaults
            to 0.
        seconds (Optional[int]): The number of seconds to add. Defaults
            to 0.
        milliseconds (Optional[int]): The number of milliseconds to add.
            Defaults to 0.
        microseconds (Optional[int]): The number of microseconds to add.
            Defaults to 0.
        utc (Optional[bool]): Whether or not to use UTC instead of local
            time. Defaults to False.

    Returns:
        datetime.datetime: The calculated datetime.
    """
    return _add_time(now(utc), years=-years, months=-months, weeks=-weeks,
                     days=-days, hours=-hours, minutes=-minutes,
                     seconds=-seconds, milliseconds=milliseconds,
                     microseconds=microseconds)


def set_utc():
    """Set all datetimes to UTC.

    The ``utc`` parameter of other methods will be ignored, with the
    global setting taking precedence.

    This can be reset by calling ``unset_utc()``.
    """
    global _FORCE_UTC  # Causes pylint W0603
    _FORCE_UTC = True


def shift(value, from_tz=None, to_tz=None, utc=False):
    """Return a datetime represented with a different time zone.

    ``value`` will be converted from its time zone (when it is time zone
    aware) or the time zone specified by ``from_tz`` (when it is time
    zone naive) to the time zone specified by ``to_tz``. These values
    can either be strings containing the name of the time zone (see
    :func:`when.all_timezones` for a list of all supported values) or a
    ``datetime.tzinfo`` object.

    If no value is provided for either ``from_tz`` (when ``value`` is
    time zone naive) or ``to_tz``, the current system time zone will be
    used. If the ``utc`` parameter is set to ``True`` or ``set_utc()``
    has been called, however, UTC will be used instead.

    Args:
        value (datetime.datetime, datetime.time): The original value
            that will be changed.
        from_tz (Optional[str]): The time zone to shift from when
            ``value`` is time zone naive.
        to_tz (Optional[str]): The time zone to shift to. Defaults to
            None.
        utc (Optional[bool]): Whether or not to use UTC instead of local
            time when ``to_tz`` isn't provided. Defaults to False.

    Returns:
        datetime.datetime: The datetime represented by the new time
            zone.

    Raises:
        TypeError: If ``value`` isn't a valid datetime type.

    .. versionchanged:: 0.4.0

        ``TypeError`` is now raised
    """
    if not hasattr(value, 'tzinfo'):
        message = "'{0}' object is not a valid time."
        raise TypeError(message.format(type(value).__name__))

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
    """Return the name of the current system time zone.

    Returns:
        str: The name of the system time zone.
    """
    # Check for the time zone:
    # 1. as an environment settings (most likely not)
    # 2. in /etc/timezone (hopefully)
    # 3. in /etc/localtime (last chance)
    tz = (
        _timezone_from_env() or
        _timezone_from_etc_timezone() or
        _timezone_from_etc_localtime()
    )

    return str(tz)


def _timezone_from_env():
    """Return the system time zone from os.environ."""
    if 'TZ' in os.environ:
        with suppress(pytz.UnknownTimeZoneError):
            return pytz.timezone(os.environ['TZ'])

    return None


def _timezone_from_etc_localtime():
    """Return the system time zone from /etc/localtime."""
    localtime_path = os.path.join(os.path.sep, 'etc', 'localtime')

    matches = []
    if os.path.exists(localtime_path):
        localtime_path = os.path.realpath(localtime_path)

        localtime = pytz.tzfile.build_tzinfo(
            localtime_path, open(localtime_path, 'rb'))

        for tzname in pytz.all_timezones:
            tz = pytz.timezone(tzname)

            if localtime.zone.endswith(tz.zone):
                # Continuing with the OS X 10.9.5 example,
                # the comparisons below continue incorrectly when
                # comparing localtime._transition_info with
                # tz._transition_info, as the tz version has one more
                # entry than the localtime version.
                matches.append(tz.zone)
                continue

            if dir(tz) != dir(localtime):
                continue

            for attr in dir(tz):
                if callable(getattr(tz, attr)) or attr.startswith('__'):
                    continue

                if attr in ('zone', '_tzinfos'):
                    continue

                if getattr(tz, attr) != getattr(localtime, attr):
                    break

            else:
                matches.append(tzname)

        if matches:
            return pytz.timezone(matches[0])
        else:
            pytz._tzinfo_cache[localtime_path] = localtime
            return localtime


def _timezone_from_etc_timezone():
    """Return the system time zone from /etc/timezone."""
    timezone_path = os.path.join(os.path.sep, 'etc', 'timezone')
    if os.path.exists(timezone_path):
        tz = open(timezone_path).read().strip()
        with suppress(pytz.UnknownTimeZoneError):
            return pytz.timezone(tz)

    return None


def timezone_object(tz_name=None):
    """Return a time zone.

    Args:
        tz_name (Optional[str]): The name of the time zone. If no value
            is provided, the system time zone will be used.

    Returns:
        datetime.tzinfo: The time zone.
    """
    return pytz.timezone(tz_name if tz_name else timezone())


def today():
    """Return the current date.

    Returns:
        datetime.date: The current date.
    """
    return datetime.date.today()


def tomorrow():
    """Return tomorrow's date.

    Returns:
        datetime.date: The current date plus one day.
    """
    return datetime.date.today() + datetime.timedelta(days=1)


def unset_utc():
    """Set all datetimes to system time.

    The ``utc`` parameter of other methods will be used.

    This can be changed by calling ``set_utc()``.
    """
    global _FORCE_UTC  # Causes pylint W0603
    _FORCE_UTC = False


def yesterday():
    """Return yesterday's date.

    Returns:
        datetime.date: The current date minus one day.
    """
    return datetime.date.today() - datetime.timedelta(days=1)
