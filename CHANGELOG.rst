
Changelog
=========

current (2022-XX-XX)
--------------------

0.1.0 (2022-11-18)
--------------------
* Add validation and helper functionality - validation based on json schema and the oemetadata schema files that are published for each release (PR#63)

0.0.9 (2022-10-31)
--------------------

* Fix bug that is raised if the input oemetadata does not contain the key _comment (PR#74) 

0.0.8 (2022-10-20)
--------------------

* Add conversion to translate oemetadata from v1.4 to v1.5
* Add conversion option to OMIs CLI application
* Add conversion additional script that converts oemetadata from v1.4 to v1.5 without using OMI. thanks to @chrwm

* Fix oeo related isAbout and valueReference field names (PR#65)
* Introduce github actions: Add automation worfklows for pypi publish for test and official (PR#67)
* Introduce new directory and provide some use cases and example implementation for omi usage and improve general code quality (PR#61)
* Reintroduce automated testing (CI) that icludes omi unit test (parser, compiler) and more (PR#69)

0.0.7 (2022-06-02)
------------------

* Add oem_structure module: Introcude support for multipe OEMetadata structure representations
* add new Dialect for OEM v15
* Full support (except for validation) for OEP-Metadata v1.5


0.0.6 (2020-07-08)
------------------

* Fix compilation of null values
* Fix parsing of lists


0.0.5 (2020-05-12)
------------------

* Fixed compiler for None in date fields


0.0.4 (2019-12-06)
------------------

* Improved documentation
* Full support of OEP-Metadata 1.4
* Support for optional fields in metadata strings
