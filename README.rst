=================================
When.py: Friendly Dates and Times
=================================

User-friendly functions to help perform common date and time actions.

Usage
=====

To get the system time zone's name::

    when.timezone()

To get the system time zone as an object::

    when.timezone_object()

To get the current date::

    when.today()

To get tomorrow's date::

    when.tomorrow()

To get yesterday's date::

    when.yesterday()

To convert to a different timezone::

    when.travel(value, from_tz='America/New_York')  # to UTC
    when.travel(value, to_tz='America/New_York')  # from UTC

To get the current time::

    when.now()
    when.now(utc=True)

Times can be forced to UTC with::

    when.set_utc()

To go back to the system's timezone::

    when.unset_utc()

Installation
============

Installing When.py is easy::

    pip install when

or download the source and run::

    python setup.py install
