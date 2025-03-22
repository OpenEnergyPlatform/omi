==================================================
Open Energy Family - Open Metadata Integration OMI
==================================================

A library to work with the open energy metadata. Its main features are validation, version conversion and infer data schemas from CSV to oemetadata.

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

.. |commits-since| image:: https://img.shields.io/github/commits-since/OpenEnergyPlatform/omi/v1.1.0.svg
    :alt: Commits since latest release
    :target: https://github.com/OpenEnergyPlatform/omi/compare/v1.1.0...master

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

To ease the conversion of oemetadata from any outdated version to the latest version, we provide a
conversion functionality. The following example shows how to convert the oemetadata from v1.6 to v2.0.

Starting form v2 we do not support conversions for patch versions. This means you can convert from v1.6 to v2.0 but not from v2.0.0 to v2.0.1.
The oemetadata release procedure requires to only add breaking changes to major or minor version. Only these changes will require a conversion.

CLI - oemetadata conversion::

    # Not implemented yet
    omi convert -i {input/path} -o {output/path}

Module usage - In python scripts you can use the conversion::

    from omi.conversion import convert_metadata

    import json

    # you a function like this one to read you oemetadata json file
    def read_json_file(file_path: str) -> dict:
        with open(file_path, "r") as file:
            data = json.load(file)
        return data

    # for example you can use the oemetdata example.json for version 1.6.0
    # find it here https://github.com/OpenEnergyPlatform/oemetadata/blob/develop/metadata/v160/example.json
    # make sure to provide a valid path relative to where you store the python environment
    file_path = "example_v16.json"

    # read the metadata document
    meta = read_json_file(file_path)

    # use omi to convert it to the latest release
    converted = convert_metadata(meta, "OEMetadata-2.0")

    # now you can store the result as json file
    with open("result.json", "w", encoding="utf-8") as json_file:
    json.dump(converted, json_file, ensure_ascii=False, indent=4)  # `indent=4` makes the JSON file easier to read


**Validation**

The validation is based on `jsonschema`. We release a schema with each `oemetadata` release, that schema
can be used to validate the user metadata. The dialect currently does not support direct access on to the
validation. This will be updated soon.
This will create a report.json containing information to debug possible errors. The parser.validate() takes
two arguments the first one is the metadata and the second optional one is the schmea. By default (if no schema is passed)
the validation will try to get the matching schema for the current metadata.


CLI - oemetadata validation::

    # Not implemented yet


Module usage::

    import json
    from omi.validation import validate_oemetadata_licenses, validate_metadata


    # use a function like this one to read you oemetadata json file
    def read_json_file(file_path: str) -> dict:
        with open(file_path, "r") as file:
            data = json.load(file)
        return data

    # for example you can use the oemetdata example.json for version 2.0.0
    # find it here https://github.com/OpenEnergyPlatform/oemetadata/blob/develop/metadata/v20/example.json
    # make sure to provide a valid path relative to where you store the python environment
    file_path = "example_v16.json"

    # read the new input from file
    meta = read_json_file(file_path)

    # validate the oemetadata: This will return noting or the errors including descriptions
    validate_metadata(meta)

    # As we are prone to open data we use this license check to validate the license name that
    # is available in the metadata document for each data resource/distribution.
    validate_oemetadata_licenses(meta)


**Inspection**

Describing your data structure is a quite technical task. OMI offers functionality to describe your data automatically.
You need to provide yor data in tabular text based format for this, for example a CSV file. Using frictionless OMI
guesses the data schema specification you can use this you provide required fields in an oemetadata document.

CLI - oemetadata conversion::

    # Not implemented yet

Module usage::

    import json

    import pathlib

    from omi.inspection import infer_metadata

    CSV_DATA_FILE = pathlib.Path(__file__).parent / "data" / "data.csv"

    # infer the data fields from CSV fuile and add to an empty metadata template
    with CSV_DATA_FILE.open("r") as f:
        metadata = infer_metadata(f, "OEP")

    # Save to a JSON file
    with open("script/metadata/result_inspection.json", "w", encoding="utf-8") as json_file:
        json.dump(metadata, json_file, ensure_ascii=False, indent=4)  # `indent=4` makes the JSON file easier to read

**Additional Fields**

To be in line with the oemetadata specification we do not allow for additional properties or fields in the metadata.
We want to keep the oemetadata relatively lean and readable still linking to other documents or to
propose a new property to extend the oemetadata would be a possibility here.

Still some times it becomes necessary to add additional information then this would be a use case outside of the OpenEnergyPlatform
specifically for your own use. You are welcome to use the oemetadata as base and add new fields we are happy to integrate them
back into the oeplatform and oemetadata if they seem relevant to other users.

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
