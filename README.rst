==================================================
Open Energy Family - Open Metadata Integration OMI
==================================================

Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis| |appveyor| |requires|
        | |codecov|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|
.. |docs| image:: https://readthedocs.org/projects/omi/badge/?style=flat
    :target: https://readthedocs.org/projects/omi
    :alt: Documentation Status

.. |travis| image:: https://travis-ci.org/OpenEnergyPlatform/omi.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/OpenEnergyPlatform/omi

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/OpenEnergyPlatform/omi?branch=master&svg=true
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/OpenEnergyPlatform/omi

.. |requires| image:: https://requires.io/github/OpenEnergyPlatform/omi/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/OpenEnergyPlatform/omi/requirements/?branch=master

.. |codecov| image:: https://codecov.io/github/OpenEnergyPlatform/omi/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/OpenEnergyPlatform/omi

.. |version| image:: https://img.shields.io/pypi/v/omi.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/omi

.. |commits-since| image:: https://img.shields.io/github/commits-since/OpenEnergyPlatform/omi/v0.0.2.svg
    :alt: Commits since latest release
    :target: https://github.com/OpenEnergyPlatform/omi/compare/v0.0.2...master

.. |wheel| image:: https://img.shields.io/pypi/wheel/omi.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/omi

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/omi.svg
    :alt: Supported versions
    :target: https://pypi.org/project/omi

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/omi.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/omi


.. end-badges

A library to process and translate open energy metadata.

* Free software: AGPL-3.0

Installation
============

::

    pip install omi

Documentation
=============


https://omi.readthedocs.io/


Development
===========

To install additional dependencies for development::

    pip install -e .[dev]

We encourage the use of pre-commit-hooks in this project. Those enforce some
formatting conventions (e.g. the use of `isort` and `black`). To enable hooks::

    pre-commit install

To run the all tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
