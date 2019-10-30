METADATA_SCHEMA_v1_3_0 = {
    "description": "",
    "type": "object",
    "properties": {
        "title": {"description": "", "type": "string"},
        "description": {"description": "", "type": "string"},
        "language": {
            "description": "",
            "type": "array",
            "items": {"language": {"description": "", "type": "string"}},
        },
        "spatial": {
            "description": "",
            "type": "object",
            "properties": {
                "location": {"description": "", "type": "string"},
                "extent": {"description": "", "type": "string"},
                "resolution": {"description": "", "type": "string"},
            },
        },
        "temporal": {
            "description": "",
            "type": "object",
            "properties": {
                "reference_date": {"description": "", "type": "string"},
                "start": {"description": "", "type": "string"},
                "end": {"description": "", "type": "string"},
                "resolution": {"description": "", "type": "string"},
            },
        },
        "sources": {
            "description": "",
            "type": "array",
            "items": {
                "description": "",
                "type": "object",
                "properties": {
                    "name": {"description": "", "type": "string"},
                    "description": {"description": "", "type": "string"},
                    "url": {"description": "", "type": "string"},
                    "license": {"description": "", "type": "string"},
                    "copyright": {"description": "", "type": "string"},
                },
            },
        },
        "license": {
            "description": "",
            "type": "object",
            "properties": {
                "id": {"description": "", "type": "string"},
                "name": {"description": "", "type": "string"},
                "version": {"description": "", "type": "string"},
                "url": {"description": "", "type": "string"},
                "instruction": {"description": "", "type": "string"},
                "copyright": {"description": "", "type": "string"},
            },
        },
        "contributors": {
            "description": "",
            "type": "array",
            "items": {
                "description": "",
                "type": "object",
                "properties": {
                    "name": {"description": "", "type": "string"},
                    "email": {"description": "", "type": "string"},
                    "date": {"description": "", "type": "string"},
                    "comment": {"description": "", "type": "string"},
                },
            },
        },
        "resources": {
            "description": "",
            "type": "array",
            "items": {
                "description": "",
                "type": "object",
                "properties": {
                    "name": {"description": "", "type": "string"},
                    "format": {"description": "", "type": "string"},
                    "fields": {
                        "description": "",
                        "type": "array",
                        "items": {
                            "description": "",
                            "type": "object",
                            "properties": {
                                "name": {"description": "", "type": "string"},
                                "description": {"description": "", "type": "string"},
                                "unit": {"description": "", "type": "string"},
                            },
                        },
                    },
                },
            },
        },
        "metadata_version": {"description": "", "type": "string"},
        "_comment": {
            "description": "",
            "type": "object",
            "properties": {
                "_url": {"description": "", "type": "string"},
                "_copyright": {"description": "", "type": "string"},
                "_metadata_license": {"description": "", "type": "string"},
                "_metadata_license_url": {"description": "", "type": "string"},
                "_contains": {"description": "", "type": "string"},
                "_additional_information": {
                    "description": "",
                    "type": "object",
                    "properties": {
                        "_dates": {"description": "", "type": "string"},
                        "_units": {"description": "", "type": "string"},
                        "_none": {"description": "", "type": "string"},
                    },
                },
            },
        },
    },
}

METADATA_SCHEMA_v1_4_0 = {
    "$schema": "TBD, e.g.: http://json-schema.org/draft-07/schema#",
    "$id": "TBD",
    "description": 'TBD: maybe "description" in properties belongs in here, maybe not?',
    "type": "object",
    "properties": {
        "name": {
            "description": "File name or database table name. Example: oep_metadata_table_example_v14",
            "type": "string",
        },
        "title": {
            "description": "Human readable title. Example: Metadata Example Table",
            "type": "string",
        },
        "id": {
            "description": "Uniform Resource Identifier (URI) that unambiguously identifies the resource. This can be a URL on the data set. It can also be a Digital Object Identifier (DOI). Example: https://example.com",
            "type": "string",
        },
        "description": {
            "description": "A description of the package. It should be usable as summary information for the entire package that is described by the metadata. Example: Example table used to illustrate the metadata structure and meaning",
            "type": "string",
        },
        "language": {
            "description": "Language used within the described data structures (e.g. titles, descriptions). The language key can be repeated if more languages are used. Standard: IETF (BCP47). Example: [en-GB, de-DE, fr-FR]",
            "type": "array",
            "items": {"language": {"description": "TBD", "type": "string"}},
        },
        "keywords": {
            "description": "An array of string keywords to assist users searching for the package in catalogs. Example: [example, template, test]",
            "type": "array",
            "items": {"keywords": {"description": "", "type": "string"}},
        },
        "publicationDate": {
            "description": "Date of publishing. Date Format is ISO 8601 (YYYY-MM-DD). Example: 2019-02-06",
            "type": "string",
        },
        "context": {
            "description": "Object. Contains name-value-pairs that describe the general setting, evironment or project leading to the creation or maintenance of this dataset.",
            "type": "object",
            "properties": {
                "homepage": {
                    "description": "URL of project. Example: https://openenergy-platform.org/",
                    "type": "string",
                },
                "documentation": {
                    "description": "TBD (description wrong): URL of the projects source code. Example: https://github.com/OpenEnergyPlatform/examples/wiki/Metadata-Description",
                    "type": "string",
                },
                "sourceCode": {
                    "description": "TBD (description wrong): Url of project. Example: https://github.com/OpenEnergyPlatform",
                    "type": "string",
                },
                "contact": {
                    "description": "Reference to the creator or maintainer of the data set. Example: contact@example.com",
                    "type": "string",
                },
                "grantNo": {
                    "description": "In a publicly funded Project: the identifying grant number. Example: 01AB2345",
                    "type": "string",
                },
                "fundingAgency": {
                    "description": "In a funded Project: The name of the funding agency. Example: Bundesministerium für Wirtschaft und Energie",
                    "type": "string",
                },
                "fundingAgencyLogo": {
                    "description": "In a publicly funded Project: A link to the Logo of the funding agency. Example: https://www.innovation-beratung-foerderung.de/INNO/Redaktion/DE/Bilder/Titelbilder/titel_foerderlogo_bmwi.jpg?__blob=poster&v=2",
                    "type": "string",
                },
                "publisherLogo": {
                    "description": "Link to the logo of the publishing institution. Example: https://reiner-lemoine-institut.de//wp-content/uploads/2015/09/rlilogo.png",
                    "type": "string",
                },
            },
        },
        "spatial": {
            "description": "Object. Contains name-value-pairs describing the spatial context of the contained data.",
            "type": "object",
            "properties": {
                "location": {
                    "description": "In the case of data where the location can be described as a point. May come as coordinates, URI or addresses with street, house number and zip code. Example: 52.433509, 13.535855",
                    "type": "string",
                },
                "extent": {
                    "description": "Covered area. May be the name of a region, or the geometry of a bounding box. Example: Europe",
                    "type": "string",
                },
                "resolution": {
                    "description": "Pixel size in case of a regular raster image. Reference to administrative level or other spatial division that is present as the smallest spatially distinguished unit size. Example: 30 m",
                    "type": "string",
                },
            },
        },
        "temporal": {
            "description": 'Object. Time period covered in the data. Temporal information should either contain a "referenceDate" or the keys describing a time series; in rare cases both. Use null for the ones that don\'t apply.',
            "type": "object",
            "properties": {
                "referenceDate": {
                    "description": "Base year, month or day. Point in time for which the data is meant to be accurate. A census will generally have a reference year. A satellite image will have a reference date. Date Format is ISO 8601. Example: 2016-01-01",
                    "type": "string",
                },
                "timeseries": {
                    "description": "TBD? Object",
                    "type": "object",
                    "properties": {
                        "start": {
                            "description": "The beginning point in time of a time series. Example: 2019-02-06T10:12:04+00:00",
                            "type": "string",
                        },
                        "end": {
                            "description": "The end point in time of a time series. Example: 2019-02-07T10:12:04+00:00",
                            "type": "string",
                        },
                        "resolution": {
                            "description": "The time span between individual points of information in a time series. Example: 30 s",
                            "type": "string",
                        },
                        "alignment": {
                            "description": 'Indicator whether stamps in a time series are left, right or middle. "null" if there is no time series. Example: left',
                            "type": "string",
                        },
                        "aggregationType": {
                            "description": "Indicates whether the values are a sum, average or current. Example: sum",
                            "type": "string",
                        },
                    },
                },
            },
        },
        "sources": {
            "description": 'TBD: maybe description of "items" belongs in here, maybe not?',
            "type": "array",
            "items": {
                "description": "List of Objects. Each object has all name-value-pairs.",
                "type": "object",
                "properties": {
                    "title": {
                        "description": "Human readable title of the source, e.g. document title or organisation name. Example: IPCC Fifth Assessment Report",
                        "type": "string",
                    },
                    "description": {
                        "description": "Free text description of the data set. Example: Scientific climate change report by the UN",
                        "type": "string",
                    },
                    "path": {
                        "description": "URL to original source. Example: https://www.ipcc.ch/site/assets/uploads/2018/02/ipcc_wg3_ar5_full.pdf",
                        "type": "string",
                    },
                    "licenses": {
                        "description": 'TBD: maybe description of "items" belongs in here, maybe not?',
                        "type": "array",
                        "items": {
                            "description": "List of Objects. Each object has all name-value-pairs. The license(s) under which the source is provided.",
                            "type": "object",
                            "properties": {
                                "name": {
                                    "description": "SPDX identifier: Example: ODbL-1.0",
                                    "type": "string",
                                },
                                "title": {
                                    "description": "Official (human readable) title. Example: Open Data Commons Open Database License 1.0",
                                    "type": "string",
                                },
                                "path": {
                                    "description": "A link to the license. Example: https://opendatacommons.org/licenses/odbl/1-0/index.html",
                                    "type": "string",
                                },
                                "instruction": {
                                    "description": "Short description of rights and restrictions. Example: You are free to share and change, but you must attribute, and share derivations under the same license.",
                                    "type": "string",
                                },
                                "attribution": {
                                    "description": "Copyrightholder of the source. Example: © Intergovernmental Panel on Climate Change 2014",
                                    "type": "string",
                                },
                            },
                        },
                    },
                },
            },
        },
        "licenses": {
            "description": 'TBD: maybe description of "items" belongs in here, maybe not?',
            "type": "array",
            "items": {
                "description": "The license(s) under which the described package is provided. List of Objects. Each object has all name-value-pairs.",
                "type": "object",
                "properties": {
                    "name": {
                        "description": "SPDX identifier. Example: ODbL-1.0",
                        "type": "string",
                    },
                    "title": {
                        "description": "Official (human readable) title. Example: 	Open Data Commons Open Database License 1.0",
                        "type": "string",
                    },
                    "path": {
                        "description": "path	A url-or-path string, that is a fully qualified HTTP address, or a relative POSIX path (see the url-or-path definition in Data Resource for details). Example: https://opendatacommons.org/licenses/odbl/1-0/index.html",
                        "type": "string",
                    },
                    "instruction": {
                        "description": "Short description of rights and restrictions. Example: You are free to share and change, but you must attribute, and share derivations under the same license.",
                        "type": "string",
                    },
                    "attribution": {
                        "description": "Copyrightholder of the produced data set. Example: © Reiner Lemoine Institut",
                        "type": "string",
                    },
                },
            },
        },
        "contributors": {
            "description": 'TBD: maybe description of "items" belongs in here, maybe not?',
            "type": "array",
            "items": {
                "description": "The people or organizations who contributed to this Data Package. This has to be a list. Each object refers to one contributor. Every contributor must have a title and property. A path, email, role and organization properties are optional extras.",
                "type": "object",
                "properties": {
                    "title": {
                        "description": "Name/title of the contributor (name for a person, name or title for an organization). Example: Jon Doe",
                        "type": "string",
                    },
                    "email": {
                        "description": "E-mail address of the contributor. Example: contact@example.com",
                        "type": "string",
                    },
                    "date": {
                        "description": "Date of the contribution. If the contribution took more than a day, use the date of the final contribiution. Date Format is ISO 8601. Example: 2016-06-16",
                        "type": "string",
                    },
                    "object": {
                        "description": "Target of contribution. Which part of the package was supplied/changed. Example: Metadata",
                        "type": "string",
                    },
                    "comment": {
                        "description": "Free text comment on what's been done. Example: Fixed a typo in the title",
                        "type": "string",
                    },
                },
            },
        },
        "resources": {
            "description": 'TBD: maybe description of "items" belongs in here, maybe not?',
            "type": "array",
            "items": {
                "description": "The Data Resource format describes a data resource as an individual file or table.",
                "type": "object",
                "properties": {
                    "profile": {
                        "description": 'A string identifying the profile of this descriptor as per the profiles specification. This information is retained in order to comply with the "Tabular Data Package" standard. If at all in doubt the value should read "tabular-data-resource". Example: tabular-data-resource',
                        "type": "string",
                    },
                    "name": {
                        "description": 'A resource MUST contain a name unique to amongst all resources in this data package. To comply with the data package standard it must consist of only lowercase alphanumeric character plus ".", "-" and "_". It may not start with a number. In a database this will be the name of the table within its containing schema. It would be usual for the name to correspond to the file name (minus the file-extension) of the data file the resource describes. Example: sandbox.example_table',
                        "type": "string",
                    },
                    "path": {
                        "description": "A url-or-path string, that should be a permanent http(s) address or other path directly linking to the resource. Example: directly linking to the resource.	https://openenergy-platform.org/dataedit/view/openstreetmap/osm_deu_roads",
                        "type": "string",
                    },
                    "format": {
                        "description": '"csv", "xls", "json" etc. would be expected to be the standard file extension for this type of resource. When you upload your data to the OEDB, in the shown metadata string, the format will be changed accordingly to "PostgreSQL", since the data there are stored in a database. Example: csv',
                        "type": "string",
                    },
                    "encoding": {
                        "description": 'Specifies the character encoding of the resource\'s data file. The values should be one of the "Preferred MIME Names" for a character encoding registered with IANA. If no value for this key is specified then the default is UTF-8. Example: UTF-8',
                        "type": "string",
                    },
                    "schema": {
                        "description": "Object containing fields and primary key. Describes the structure of the present data.",
                        "type": "object",
                        "properties": {
                            "fields": {
                                "description": "List of objects. Every object describes a column and provides name, description, type and unit.",
                                "type": "array",
                                "items": {
                                    "description": "TBD",
                                    "type": "object",
                                    "properties": {
                                        "name": {
                                            "description": "Name string unique within its scope. Example: year",
                                            "type": "string",
                                        },
                                        "description": {
                                            "description": "Free-text describing the field. Example: Reference year for which the data were collected.",
                                            "type": "string",
                                        },
                                        "type": {
                                            "description": "Data type of the field. In case of a geom-column in a database, also indicate the shape and CRS. Example: geometry(Point, 4326)",
                                            "type": "string",
                                        },
                                        "unit": {
                                            "description": 'Unit, preferably SI-Unit, that values in this field are mapped to. If "unit" doesn\'t apply to a field, use "none". Example: MW',
                                            "type": "string",
                                        },
                                    },
                                },
                            },
                            "primaryKey": {
                                "description": 'TBD: maybe description of "items" belongs in here, maybe not?',
                                "type": "array",
                                "items": {
                                    "primaryKey": {
                                        "description": "A primary key is a field or set of fields that uniquely identifies each row in the table. It's recorded as a list of strings, since it is possible to define the primary key as made up of several columns. Example: id",
                                        "type": "string",
                                    }
                                },
                            },
                            "foreignKeys": {
                                "description": 'TBD: maybe description of "items" belongs in here, maybe not?',
                                "type": "array",
                                "items": {
                                    "description": "A foreign key is a field that refers to a column in another table.",
                                    "type": "object",
                                    "properties": {
                                        "fields": {
                                            "description": 'TBD: maybe description of "items > fields" belongs in here, maybe not?',
                                            "type": "array",
                                            "items": {
                                                "fields": {
                                                    "description": "The column in the table that is constrainted by the foreign key. Example: version",
                                                    "type": "string",
                                                }
                                            },
                                        },
                                        "reference": {
                                            "description": "The reference to the foreign table.",
                                            "type": "object",
                                            "properties": {
                                                "resource": {
                                                    "description": "The foreign resource (table). Example: schema.table",
                                                    "type": "string",
                                                },
                                                "fields": {
                                                    "description": 'TBD: maybe description of "items > fields" belongs in here, maybe not?',
                                                    "type": "array",
                                                    "items": {
                                                        "fields": {
                                                            "description": "The foreign resource column. Example: version",
                                                            "type": "string",
                                                        }
                                                    },
                                                },
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                    "dialect": {
                        "description": 'Object. A CSV Dialect defines a simple format to describe the various dialects of CSV files in a language agnostic manner. In case of a database, the values in the containing fields are "none".',
                        "type": "object",
                        "properties": {
                            "delimiter": {
                                "description": 'Specifies the character sequence which should separate fields (aka columns). Common characters are "," (comma), "." (point) and "\t" (tab). Example: ,',
                                "type": "string",
                            },
                            "decimalSeparator": {
                                "description": 'Symbol used to separate the integer part from the fractional part of a number written in decimal form. Depending on language and region this symbol can be "." or ",". Example: .',
                                "type": "string",
                            },
                        },
                    },
                },
            },
        },
        "review": {
            "description": "Data uploaded through the OEP needs to go through review. The review will cover the areas described here: https://github.com/OpenEnergyPlatform/data-preprocessing/wiki and carried out by a team of the platform. The review itself is documented at the specified path and a badge is rewarded with regards to completeness.",
            "type": "object",
            "properties": {
                "path": {
                    "description": "A URL or path string, that should be a permanent http(s) address directly linking to the documented review. Example: https://www.example.com",
                    "type": "string",
                },
                "badge": {
                    "description": "A badge of either Bronze, Silver, Gold or Platin is used to label the given metadata based on its quality. Example: Platin",
                    "type": "string",
                },
            },
        },
        "metaMetadata": {
            "description": "Object. Description about the metadata themselves, their format, version and license. These fields should already be provided when you’re filling out your metadata.",
            "type": "object",
            "properties": {
                "metadataVersion": {
                    "description": "Type and version number of the metadata. Example: OEP-1.4",
                    "type": "string",
                },
                "metadataLicense": {
                    "description": "Object describing the license of the provided metadata.",
                    "type": "object",
                    "properties": {
                        "name": {
                            "description": "SPDX identifier. Example: CC0-1.0",
                            "type": "string",
                        },
                        "title": {
                            "description": "Official (human readable) license title. Example: Creative Commons Zero v1.0 Universal",
                            "type": "string",
                        },
                        "path": {
                            "description": "Url or path string, that is a fully qualified HTTP address. Example: https://creativecommons.org/publicdomain/zero/1.0/",
                            "type": "string",
                        },
                    },
                },
            },
        },
        "_comment": {
            "description": "Array of objects. The “_comment”-section is used as a self-description of the final metadata-file. It is text, intended for humans and can include a link to the metadata documentation(s), required value formats and similar remarks. The comment section has no fix structure or mandatory values, but a useful self-description, similar to the one depicted here, is encouraged.",
            "type": "object",
            "properties": {
                "metadata": {
                    "description": "Reference to the metadata documentation in use. Example: Metadata documentation and explanation (https://github.com/OpenEnergyPlatform/organisation/wiki/metadata)",
                    "type": "string",
                },
                "dates": {
                    "description": "Comment on data/time format. Example: Dates and time must follow the ISO8601 including time zone (YYYY-MM-DD or YYYY-MM-DDThh:mm:ss±hh)",
                    "type": "string",
                },
                "units": {
                    "description": "Comment on units. Example: If you must use units in cells (which is discouraged), leave a space between numbers and units (100 m)",
                    "type": "string",
                },
                "languages": {
                    "description": "Comment on language format. Example: Languages must follow the IETF (BCP47) format (en-GB, en-US, de-DE)",
                    "type": "string",
                },
                "licenses": {
                    "description": "Reference to license format. Example: License name must follow the SPDX License List (https://spdx.org/licenses/)",
                    "type": "string",
                },
                "review": {
                    "description": "Reference to review documentation. Example: Following the OEP Data Review (https://github.com/OpenEnergyPlatform/data-preprocessing/wiki)",
                    "type": "string",
                },
                "null": {
                    "description": 'Feel free to add more descriptive comments. Like "none". Example: If a field is not applicable just enter "none"',
                    "type": "string",
                },
            },
        },
    },
}
