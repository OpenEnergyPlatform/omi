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

Usage
=====

**Parse, Compile, Render, Convert and Validate**
Omi can read(parse), compile, Render(json compilant), convert(convert metadata from v1.4 to v1.5 structure) and validate - a json 
file or object that is compliant with the oemetadata spec. This is usefull to do various operations that help to integrate with - as 
well as in interact with the oemetadata. Some parts of this tool might still be volatile but the code quality is conventionsly improved 
as this module is a core component of the oeplatfroms metadata integration system.

Check if omi is able to read a oemetadata file (for version 1.4 and 1.5)
CLI - oemetadata version 1.5::

    omi translate -f oep-v1.5 examples/data/metadata_v15.json

CLI - oemetadata version 1.4::

    omi translate -f oep-v1.4 -t oep-v1.4 examples/data/metadata_v14.json

omi is able to read a JSON file and parse it into one of the internal Python structures (depending on the oemetadata version). 
The OEPMetadata Python object can then be compiled and converted back to JSON. You can manipulate a successfully parsed 
OEPMetadata object.

Module usage::

    from omi.dialects.oep.dialect import OEP_V_1_3_Dialect, OEP_V_1_4_Dialect, OEP_V_1_5_Dialect
    inp = '{"id":"unique_id"}' #or read from json file
    dialect1_5 = OEP_V_1_5_Dialect()
    parsed = dialect1_5.parse(input)
    print(parsed)
    parsed.identifier = "another_unique_id"
    compiled = dialect1_5.compile(parsed)
    print(compiled)


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
    from omi.dialects.oep.parser import JSONParser

    with open("tests/data/metadata_v15.json", "r", encoding="utf-8") as f:
        metadata = json.load(f)

    parser = JSONParser()
    parser.validate(metadata)
    
    # check if your metadata is valid for the given schmea 
    schema = ... get a schema or import form oemetadata module
    parser.is_valid(metadata, schema)


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
