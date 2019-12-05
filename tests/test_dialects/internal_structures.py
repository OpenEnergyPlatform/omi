import datetime

from omi import structure as s

_source_year = s.Field(
    name="year", description="Reference year", field_type="integer", unit=None
)

_target_year = s.Field(name="year", description=None, field_type=None, unit=None)

_target_resource = s.Resource(
    name="schema.table",
    schema=s.Schema(fields=[_target_year], foreign_keys=None, primary_key=None),
    dialect=None,
    encoding=None,
    path=None,
    profile=None,
    resource_format=None,
)

_target_year.resource = _target_resource


cc010 = s.License(
    name="Creative Commons Zero v1.0 Universal",
    identifier="CC0-1.0",
    path="https://creativecommons.org/publicdomain/zero/1.0/legalcode",
    other_references=None,
    text=None,
)

odbl10 = s.License(
    identifier="ODbL-1.0",
    name="Open Data Commons Open Database License 1.0",
    path="https://opendatacommons.org/licenses/odbl/1.0/",
    other_references=None,
    text=None,
)

odbl10_13 = s.License(
    name=None, identifier="ODbL-1.0", path=None, other_references=None, text=None
)

metadata_v_1_3 = s.OEPMetadata(
    name=None,
    title="Conceived Example Table Meant for Creating an Illustrative Metadata String thereof",
    identifier=None,
    description="An imaginary table that provides many features, offering a suitable source for metadata template entries",
    languages=["eng"],
    keywords=None,
    publication_date=None,
    context=None,
    spatial=s.Spatial(location=None, extent="Berlin", resolution="1 m"),
    temporal=s.Temporal(
        reference_date=datetime.datetime(2018, 11, 13),
        start=None,
        end=None,
        resolution=None,
        ts_orientation=None,
    ),
    sources=[
        s.Source(
            title="Technical review and evaluation of Issue",
            description="Study financed by Organisation describes Issue. The study is authored by Jon Doe and Erika Mustermann",
            path="https://doi.org/1.1/j.d.2000.01.001",
            licenses=[s.TermsOfUse(attribution="Publisher")],
        ),
        s.Source(
            title="Metastudy on Issue",
            description="Study financed by State Actor evaluates Issue in regions. The study is authored by Jane Doe and Otto Normal",
            path="https://doi.org/2.2/j.d.2022.02.022",
            licenses=[s.TermsOfUse(attribution="Publisher2")],
        ),
    ],
    terms_of_use=[
        s.TermsOfUse(
            lic=odbl10,
            instruction="You are free: To Share, To Create, To Adapt; As long as you: Attribute, Share-Alike, Keep open!",
            attribution="Institute",
        )
    ],
    contributions=[
        s.Contribution(
            contributor=s.Person(
                name="Person McHuman", email="person.mchuman@good-institute.net"
            ),
            date=datetime.datetime(2011, 1, 11, 0, 0, 0),
            obj=None,
            comment="Prepared the dataset",
        ),
        s.Contribution(
            contributor=s.Person(
                name="Indivia Mensch", email="indivia.mensch@gute-organisation.org"
            ),
            date=datetime.datetime(2012, 2, 12, 0, 0, 0),
            obj=None,
            comment="Fixed Metadata String and date format ",
        ),
    ],
    resources=[
        s.Resource(
            name="example.datatable",
            resource_format="PostgreSQL",
            schema=s.Schema(
                fields=[
                    s.Field(
                        name="id",
                        description="unambiguous unique numer",
                        unit=None,
                        field_type=None,
                    ),
                    s.Field(
                        name="component_id",
                        description="Identifying numer of component. May repeat due to several occurences of the same component.",
                        unit=None,
                        field_type=None,
                    ),
                    s.Field(
                        name="measurement",
                        description="Measured by Instrument",
                        unit="kWh",
                        field_type=None,
                    ),
                    s.Field(
                        name="reference",
                        description="Bibtex String that references the information source.",
                        unit=None,
                        field_type=None,
                    ),
                ],
                primary_key=None,
                foreign_keys=None,
            ),
            path=None,
            profile=None,
            encoding=None,
            dialect=None,
        )
    ],
    review=None,
    comment=None,
)

metadata_v_1_4 = s.OEPMetadata(
    name="oep_metadata_table_example_v14",
    title="Good example title",
    identifier="http://openenergyplatform.org/dataedit/view/model_draft/oep_metadata_table_example_v14",
    description="example metadata for example data",
    languages=["en-GB", "en-US", "de-DE", "fr-FR"],
    keywords=["example", "template", "test"],
    publication_date=datetime.datetime(2018, 6, 12, 0, 0),
    context=s.Context(
        homepage="https://reiner-lemoine-institut.de/szenariendb/",
        documentation="https://github.com/OpenEnergyPlatform/organisation/wiki/metadata",
        source_code="https://github.com/OpenEnergyPlatform/examples/tree/master/metadata",
        contact="https://github.com/Ludee",
        grant_number="03ET4057",
        funding_agency=s.Agency(
            name="Bundesministerium für Wirtschaft und Energie",
            logo="https://www.innovation-beratung-foerderung.de/INNO/Redaktion/DE/Bilder/Titelbilder/titel_foerderlogo_bmwi.jpg?__blob=poster&v=2",
        ),
        publisher=s.Agency(
            logo="https://reiner-lemoine-institut.de//wp-content/uploads/2015/09/rlilogo.png"
        ),
    ),
    spatial=s.Spatial(location=None, extent="europe", resolution="100 m"),
    temporal=s.Temporal(
        reference_date=datetime.datetime(2016, 1, 1, 0, 0),
        start=datetime.datetime(
            2017, 1, 1, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(0, 3600))
        ),
        end=datetime.datetime(
            2017, 12, 31, 23, 0, tzinfo=datetime.timezone(datetime.timedelta(0, 3600))
        ),
        resolution="1 h",
        ts_orientation=s.TimestampOrientation.left,
        aggregation="sum",
    ),
    sources=[
        s.Source(
            title="OpenEnergyPlatform Metadata Example",
            description="Metadata description",
            path="https://github.com/OpenEnergyPlatform",
            licenses=[
                s.TermsOfUse(
                    lic=cc010,
                    instruction="You are free: To Share, To Create, To Adapt",
                    attribution="© Reiner Lemoine Institut",
                )
            ],
        ),
        s.Source(
            title="OpenStreetMap",
            description="A collaborative project to create a free editable map of the world",
            path="https://www.openstreetmap.org/",
            licenses=[
                s.TermsOfUse(
                    lic=odbl10,
                    instruction="You are free: To Share, To Create, To Adapt; As long as you: Attribute, Share-Alike, Keep open!",
                    attribution="© OpenStreetMap contributors",
                )
            ],
        ),
    ],
    terms_of_use=[
        s.TermsOfUse(
            lic=odbl10,
            instruction="You are free: To Share, To Create, To Adapt; As long as you: Attribute, Share-Alike, Keep open!",
            attribution="© Reiner Lemoine Institut © OpenStreetMap contributors",
        )
    ],
    contributions=[
        s.Contribution(
            contributor=s.Person(name="Ludee", email=None),
            date=datetime.datetime(2016, 6, 16),
            obj="metadata",
            comment="Create metadata",
        ),
        s.Contribution(
            contributor=s.Person(name="Ludee", email=None),
            date=datetime.datetime(2016, 11, 22),
            obj="metadata",
            comment="Update metadata",
        ),
        s.Contribution(
            contributor=s.Person(name="Ludee", email=None),
            date=datetime.datetime(2016, 11, 22),
            obj="metadata",
            comment="Update header and license",
        ),
        s.Contribution(
            contributor=s.Person(name="Ludee", email=None),
            date=datetime.datetime(2017, 3, 16),
            obj="metadata",
            comment="Add license to source",
        ),
        s.Contribution(
            contributor=s.Person(name="Ludee", email=None),
            date=datetime.datetime(2017, 3, 28),
            obj="metadata",
            comment="Add copyright to source and license",
        ),
        s.Contribution(
            contributor=s.Person(name="Ludee", email=None),
            date=datetime.datetime(2017, 5, 30),
            obj="metadata",
            comment="Release metadata version 1.3",
        ),
        s.Contribution(
            contributor=s.Person(name="Ludee", email=None),
            date=datetime.datetime(2017, 6, 26),
            obj="metadata",
            comment="Move referenceDate into temporal and remove array",
        ),
        s.Contribution(
            contributor=s.Person(name="Ludee", email=None),
            date=datetime.datetime(2018, 7, 19),
            obj="metadata",
            comment="Start metadata version 1.4",
        ),
        s.Contribution(
            contributor=s.Person(name="Ludee", email=None),
            date=datetime.datetime(2018, 7, 26),
            obj="data",
            comment="Rename table and files",
        ),
        s.Contribution(
            contributor=s.Person(name="Ludee", email=None),
            date=datetime.datetime(2018, 10, 18),
            obj="metadata",
            comment="Add contribution object",
        ),
        s.Contribution(
            contributor=s.Person(name="christian-rli", email=None),
            date=datetime.datetime(2018, 10, 18),
            obj="metadata",
            comment="Add datapackage compatibility",
        ),
        s.Contribution(
            contributor=s.Person(name="Ludee", email=None),
            date=datetime.datetime(2018, 11, 2),
            obj="metadata",
            comment="Release metadata version 1.4",
        ),
        s.Contribution(
            contributor=s.Person(name="christian-rli", email=None),
            date=datetime.datetime(2019, 2, 5),
            obj="metadata",
            comment="Apply template structure to example",
        ),
        s.Contribution(
            contributor=s.Person(name="Ludee", email=None),
            date=datetime.datetime(2019, 3, 22),
            obj="metadata",
            comment="Hotfix foreignKeys",
        ),
        s.Contribution(
            contributor=s.Person(name="Ludee", email=None),
            date=datetime.datetime(2019, 7, 9),
            obj="metadata",
            comment="Release metadata version OEP-1.3.0",
        ),
    ],
    resources=[
        s.Resource(
            name="model_draft.oep_metadata_table_example_v14",
            path="http://openenergyplatform.org/dataedit/view/model_draft/oep_metadata_table_example_v14",
            profile="tabular-data-resource",
            resource_format="PostgreSQL",
            encoding="UTF-8",
            schema=s.Schema(
                fields=[
                    s.Field(
                        name="id",
                        description="Unique identifier",
                        field_type="serial",
                        unit=None,
                    ),
                    _source_year,
                    s.Field(
                        name="value",
                        description="Example value",
                        field_type="double precision",
                        unit="MW",
                    ),
                    s.Field(
                        name="geom",
                        description="Geometry",
                        field_type="geometry(Point, 4326)",
                        unit=None,
                    ),
                ],
                primary_key=["id"],
                foreign_keys=[
                    s.ForeignKey(
                        references=[
                            s.Reference(source=_source_year, target=_target_year)
                        ]
                    )
                ],
            ),
            dialect=s.Dialect(delimiter=None, decimal_separator="."),
        )
    ],
    review=s.Review(
        path="https://github.com/OpenEnergyPlatform/data-preprocessing/wiki",
        badge="platin",
    ),
    comment=s.MetaComment(
        metadata_info="Metadata documentation and explanation (https://github.com/OpenEnergyPlatform/organisation/wiki/metadata)",
        dates="Dates and time must follow the ISO8601 including time zone (YYYY-MM-DD or YYYY-MM-DDThh:mm:ss±hh)",
        units="Use a space between numbers and units (100 m)",
        languages="Languages must follow the IETF (BCP47) format (en-GB, en-US, de-DE)",
        licenses="License name must follow the SPDX License List (https://spdx.org/licenses/)",
        review="Following the OEP Data Review (https://github.com/OpenEnergyPlatform/data-preprocessing/wiki)",
        none="If not applicable use (null)",
    ),
)


metadata_v_1_3_minimal = s.OEPMetadata()

metadata_v_1_4_minimal = s.OEPMetadata(identifier="id")
