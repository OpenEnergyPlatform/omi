========
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

.. |travis| image:: https://travis-ci.org/MGlauer/omi.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/MGlauer/omi

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/MGlauer/omi?branch=master&svg=true
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/MGlauer/omi

.. |requires| image:: https://requires.io/github/MGlauer/omi/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/MGlauer/omi/requirements/?branch=master

.. |codecov| image:: https://codecov.io/github/MGlauer/omi/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/MGlauer/omi

.. |version| image:: https://img.shields.io/pypi/v/metadata-tool.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/metadata-tool

.. |commits-since| image:: https://img.shields.io/github/commits-since/MGlauer/omi/v0.0.0.svg
    :alt: Commits since latest release
    :target: https://github.com/MGlauer/omi/compare/v0.0.0...master

.. |wheel| image:: https://img.shields.io/pypi/wheel/metadata-tool.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/metadata-tool

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/metadata-tool.svg
    :alt: Supported versions
    :target: https://pypi.org/project/metadata-tool

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/metadata-tool.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/metadata-tool


.. end-badges

A library to process and translate open energy metadata.

* Free software: BSD 2-Clause License

Installation
============

::

    pip install metadata-tool

Documentation
=============


https://omi.readthedocs.io/


Development
===========

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
