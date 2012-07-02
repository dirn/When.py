=================================
When.py: Friendly Dates and Times
=================================

.. image:: https://secure.travis-ci.org/dirn/When.py.png?branch=develop

User-friendly functions to help perform common date and time actions.

Usage
=====

To get the system time zone's name::

    when.timezone()

To get the current date::

    when.today()

To get tomorrow's date::

    when.tomorrow()

To get yesterday's date::

    when.yesterday()

To get a datetime one year from now::

    when.future(years=1)

To convert to a different time zone::

    when.shift(value, from_tz='America/New_York', to_tz='UTC')

To get the current time::

    when.now()

Full documentation can be found on `Read the Docs`_.

.. _Read the Docs: http://readthedocs.org/docs/whenpy/en/latest/

Installation
============

Installing When.py is easy::

    pip install whenpy

or download the source and run::

    python setup.py install
