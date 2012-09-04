#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

settings = dict()

# Publish
if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

settings.update(
    name='whenpy',
    version='0.3.0',
    description='Friendly Dates and Times',
    long_description=open('README.rst').read(),
    author='Andy Dirnberger',
    author_email='dirn@dirnonline.com',
    url='https://github.com/dirn/When.py',
    py_modules=['when'],
    package_data={'': ['LICENSE']},
    include_package_data=True,
    install_requires=['pytz'],
    tests_require=['coverage', 'mock', 'nose'],
    license=open('LICENSE').read(),
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ),
)

setup(**settings)
