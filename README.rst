==================================================
Open Energy Family - Open Metadata Integration OMI
==================================================

A library to process and translate and work with the open energy metadata.

* Free software: AGPL-3.0

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

.. |Automated Test| image:: https://github.com/OpenEnergyPlatform/omi/actions/workflows/automated-testing.yml/badge.svg
    :target: https://github.com/OpenEnergyPlatform/omi/actions/workflows/automated-testing.yml
    :alt: Test status

.. |codecov| image:: https://codecov.io/github/OpenEnergyPlatform/omi/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/OpenEnergyPlatform/omi

.. |version| image:: https://img.shields.io/pypi/v/omi.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/omi

.. |commits-since| image:: https://img.shields.io/github/commits-since/OpenEnergyPlatform/omi/v0.2.1.svg
    :alt: Commits since latest release
    :target: https://github.com/OpenEnergyPlatform/omi/compare/v0.2.1...master

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

Installation
============

::

    pip install omi

Documentation
=============

Documentation for OMI versions up to 0.2:
https://omi.readthedocs.io/

Documentation for reworked OMI versions starting from 1.0 you can find in the README document. Later on we migrate the documentation to mkdocs.

Usage
=====

You can use omi as python module and import its functionality into your codebase or use the cli capabilities. OMI provides tooling for validation
of oemetdata JSON documents using JSON-Schema. It also include helpers to generate the tabular data resource definition to seep up the metadata
creation and helps to select a open license by checking the license identifier against the SPDX license list.

As the oemetadata is updated from time to time we provides conversion functionality to convert metadata documents that use an earlier version
of the oemetadata-specification to help users stick with the latest enhancements the latest oemetadata version offers.

**Conversion**

To ease the conversion of oemetadata from the outdated version 1.4 to the latest version, we provide
conversion functionality. The following example shows how to convert the oemetadata from v1.4 to v1.5
by using a CLI command.

CLI - oemetadata conversion from v1.4 to v1.5::

    omi convert -i {input/path} -o {output/path}

**Validation**

The validation is based on `jsonschema`. We release a schema with each `oemetadata` release, that schema
can be used to validate the user metadata. The dialect currently does not support direct access on to the
validation. This will be updated soon.
This will create a report.json containing information to debug possible errors. The parser.validate() takes
two arguments the first one is the metadata and the second optional one is the schmea. By default (if no schema is passed)
the validation will try to get the matching schema for the current metadata.

Module usage::

    # You can import the JSONParser directly like this:
    import json
    from omi import validation

    with open("tests/data/metadata_v15.json", "r", encoding="utf-8") as f:
        metadata = json.load(f)

    result = validation(metadata)
    # TBD

**Additional Fields - not related to the OEMetadata specification**

Sometimes it is necessary to store additional key-value pairs along with the keys included in the OEMetadata specification.
OMI's compiler methods are capable of handling additional arguments or key-value arguments, but this must be
be explicitly specified.

To add additional key-value pairs, you must:

    NOTE: If you save the renderer return value in a json file and try to parse the file, the extra field is not included.
          You must read the json file using Python and then add the extra field back oemetadata object as shown below.

1 Parse the oemetadata from json file / variable into omis internal structure::

    from omi.dialects.oep.dialect import OEP_V_1_5_Dialect

    min_inp = '{"id":"unique_id"} # or read from json file
    minimal_oemetadata15 = OEP_V_1_5_Dialect.parse(min_inp)

2 Now you can get(from json file)/define the additional data::

    data = "test"

3 And add it to the OEMetadata object that was parsed in step 1 by ading a key-value argument::

    compiled = OEP_V_1_5_Dialect.compile(minimal_oemetadata15, _additionalField=data)
    rendered = OEP_V_1_5_Dialect.render(compiled)

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
