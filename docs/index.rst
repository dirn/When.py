When.py 0.2.0
===================================

When.py provides user-friendly functions to help perform common date and time
actions.

.. toctree::
   :maxdepth: 2

Usage
-----

.. automodule:: when
   :synopsis: Friendly Dates and Times
   :members:

A note about ``future`` and ``past``
------------------------------------

When changing a datetime from one month (or year) to another, it is often the
case that the new month will have fewer days than the original, resulting in an
invalid date. When this happens, the days will be adjusted into the future.
This is consistent with implementations found elsewhere.

    >>> when.today()
    datetime.date(2012, 2, 29)
    >>>
    >>> when.future(years=1)
    datetime.datetime(2013, 3, 1, 19, 0, 23, 76878)

    >>> when.today()
    datetime.date(2012, 3, 31)
    >>>
    >>> when.past(months=1)
    datetime.datetime(2012, 3, 2, 19, 7, 36, 317653)

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

