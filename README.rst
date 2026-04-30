==================================================
Open Energy Family - Open Metadata Integration OMI
==================================================

A library and command-line tool to work with Open Energy Metadata (`OEMetadata`_).

.. _OEMetadata: https://openenergyplatform.github.io/oemetadata/latest/

* Free software: AGPL-3.0

Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |Automated test| |codecov|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|

.. |docs| image:: https://readthedocs.org/projects/omi/badge/?style=flat
    :target: https://readthedocs.org/projects/omi
    :alt: Documentation Status

.. |Automated test| image:: https://github.com/OpenEnergyPlatform/omi/actions/workflows/automated-testing.yml/badge.svg
    :target: https://github.com/OpenEnergyPlatform/omi/actions/workflows/automated-testing.yml
    :alt: Test status

.. |codecov| image:: https://codecov.io/github/OpenEnergyPlatform/omi/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/OpenEnergyPlatform/omi

.. |version| image:: https://img.shields.io/pypi/v/omi.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/omi

.. |commits-since| image:: https://img.shields.io/github/commits-since/OpenEnergyPlatform/omi/v1.2.0.svg
    :alt: Commits since latest release
    :target: https://github.com/OpenEnergyPlatform/omi/compare/v1.2.0...master

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

Features
========

OMI provides robust tooling for managing Open Energy Metadata, whether you are using it as a Python library or via the Command Line Interface (CLI):

* **Validation**: Validate OEMetadata JSON documents using JSON-Schema and verify open license identifiers against the SPDX license list.
* **Version Conversion**: Easily upgrade metadata documents from older OEMetadata specifications to the latest releases.
* **YAML-Based Creation**: Scaffold, template, and assemble OEMetadata cleanly using a split-files YAML layout to keep your metadata DRY.
* **Inspection & Skeletons**: Automatically infer data schemas from CSV files or inspect SQL databases to generate metadata resource skeletons.
* **Schema Drift Detection**: Compare your documented metadata schemas against actual database tables to detect missing columns or type mismatches.
* **OEP Integration**: Directly push and pull metadata to and from tables on the Open Energy Platform (OEP).

Installation
============

You can install the package via `pip`_.

.. _pip: https://pypi.org/project/omi/

::

    pip install omi

**Note:** We recommend using the tool `uv`_ to manage your python environments.

.. _uv: https://docs.astral.sh/uv/

CLI Quickstart
==============

OMI comes with a powerful CLI to manage your metadata workflow without writing Python code. 

**Data Requirements:** OMI requires you to have your data ready in a tabular format. Currently, only CSV files and PostgreSQL database tables are supported data resources. 

When working with local files, OMI expects the structure defined by the Frictionless `datapackage`_ standard. Your local directory structure should look something like this:

.. _datapackage: https://datapackage.org/standard/data-package/#structure

::

    my_data_publication/
    ├── datapackage.json            # Optional: In case you already use Frictionless datapackage. Otherwise OMI will help you generate this file.
    ├── additional_scalars.csv
    └── data/
        ├── elements/
        │   ├── biomass_gas-bpchp_heat_high.csv
        │   ├── bus.csv
        │   └── ... (other element CSVs)
        └── sequences/
            ├── electricity-demand_cts_profile.csv
            ├── electricity-wind_profile.csv
            └── ... (other sequence CSVs)


**Get an overview of the CLI functionality:**

::

    omi --help
    omi init --help
    omi inspect --help

**1. Initialize a new metadata dataset:**
::

    omi init dataset ./metadata my_data_publication

**2. Inspect tabular data to create resource metadata:**

*From local CSV files (using the directory structure above):*
::

    omi init resources ./metadata my_data_publication my_data_publication/data/elements/*.csv

*Or, from a database table:*
::

    omi init db-resource ./metadata my_data_publication postgresql://user:pass@localhost:5432/db --schema public --table my_table

**3. Assemble split YAML files into a final JSON document:**
::

    omi assemble --base-dir ./metadata --dataset-id my_data_publication --output-file ./out/my_data_publication_metadata.json

**4. Push metadata directly to the OEP:**
Note: Make sure you already created all tables which are part of you dataset on the OEP. OMI will not do that, for smaller dataset you can use the Wizard on the OEP. 
For expert users we offer the tool oem2orm which uses the metadata descriptions to generate database tables on the OEP for you. This requires you to already have your
data format ready (data files and columns).

::

    omi push-oep-all --base-dir ./metadata --dataset-id my_data_publication --token YOUR_API_TOKEN

*For a full list of commands and options, run* ``omi --help``.

Documentation
=============

This README provides a minimal overview. For comprehensive guides, Python module API references, and advanced CLI usage, please refer to our official documentation:

* **Current Documentation:** Check the `docs/ <docs/>`_ directory in this repository.
* **Legacy Documentation (up to v0.2):** `omi.readthedocs.io <https://omi.readthedocs.io/>`_

*(Note: We are actively migrating our documentation to MkDocs).*

Development
===========

To install additional dependencies for development:

::

    pip install -e .[dev]

We encourage the use of pre-commit-hooks in this project. Those enforce formatting conventions (e.g., ``isort`` and ``black``). To enable hooks:

::

    pre-commit install

To run all tests:

::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    * - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    * - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
