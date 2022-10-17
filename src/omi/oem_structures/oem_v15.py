"""
This module extends the internal data structure 
with the latest changes of the OEMetadata standard.

An OEMeadata version specific dialect can import it.

This bypasses the limitation of OMI to rely on a single 
internal representation of the data structure, since 
OEMetadata is not a static structure and OMI must be
be able to validate multiple OEMetadata versions.
"""
# TODO: maybe change all inheritance to omi.structure to
#      avoide alot of redundancy

from datetime import datetime
from enum import Enum
from typing import Iterable

from omi.structure import Compilable


class Language(Compilable):
    __compiler_name__ = "language"


class Subject(Compilable):
    __compiler_name__ = "subject"

    def __init__(self, name: str = None, path: str = None):
        self.name = name
        self.path = path


class Spatial(Compilable):
    __compiler_name__ = "spatial"

    def __init__(
        self, location: str = None, extent: str = None, resolution: str = None
    ):
        self.location = location
        self.extent = extent
        self.resolution = resolution


class TimestampOrientation(Compilable, Enum):
    __compiler_name__ = "timestamp_orientation"
    left = 0
    middle = 1
    right = 2

    @staticmethod
    def create(value: str) -> "TimestampOrientation":
        if value == "left":
            return TimestampOrientation.left
        elif value == "middle":
            return TimestampOrientation.middle
        elif value == "right":
            return TimestampOrientation.right
        else:
            raise Exception("Unknown timestamp orientation:", value)


class Timeseries(Compilable):
    __compiler_name__ = "timeseries"

    def __init__(
        self,
        start: datetime = None,
        end: datetime = None,
        resolution: str = None,
        ts_orientation: TimestampOrientation = None,
        aggregation: str = None,
    ):
        self.ts_start = start
        self.ts_end = end
        self.ts_resolution = resolution
        self.ts_orientation = ts_orientation
        self.aggregation = aggregation


class Temporal(Compilable):
    __compiler_name__ = "temporal"

    def __init__(
        self,
        reference_date: datetime = None,
        timeseries_collection: Iterable[Timeseries] = None,
    ):
        self.reference_date = reference_date
        self.timeseries_collection = timeseries_collection


class License(Compilable):
    __compiler_name__ = "license"

    def __init__(
        self,
        name: str = None,
        identifier: str = None,
        text: str = None,
        path: str = None,
        other_references: Iterable[str] = None,
        comment: str = None,
    ):
        self.name = name
        self.path = path
        self.identifier = identifier
        self.other_references = other_references
        self.text = text
        self.comment = comment

    @staticmethod
    def instance_name_from_id(identifier: str):
        return "L_" + identifier.replace("-", "_").replace(".", "_").replace(
            "+", "_plus"
        )


class TermsOfUse(Compilable):
    __compiler_name__ = "terms_of_use"

    def __init__(
        self, instruction: str = None, attribution: str = None, lic: License = None
    ):
        self.instruction = instruction
        self.attribution = attribution
        self.license = lic


class Source(Compilable):
    __compiler_name__ = "source"

    def __init__(
        self,
        title: str = None,
        description: str = None,
        path: str = None,
        licenses: Iterable[TermsOfUse] = None,
    ):
        self.title = title
        self.description = description
        self.path = path
        self.licenses = licenses


class Person(Compilable):
    __compiler_name__ = "person"

    def __init__(self, name: str = None, email: str = None):
        self.name = name
        self.email = email


class Contribution(Compilable):
    __compiler_name__ = "contribution"

    def __init__(
        self,
        contributor: Person = None,
        date: datetime = None,
        obj: str = None,
        comment: str = None,
    ):
        self.contributor = contributor
        self.date = date
        self.object = obj
        self.comment = comment


class IsAbout(Compilable):
    __compiler_name__ = "isAbout"

    def __init__(self, name: str = None, path: str = None):
        self.name = name
        self.path = path


class ValueReference(Compilable):
    __compiler_name__ = "valueReference"

    def __init__(self, value: str = None, name: str = None, path: str = None):
        self.value = value
        self.name = name
        self.path = path


class Field(Compilable):
    __compiler_name__ = "field"

    def __init__(
        self,
        name: str = None,
        description: str = None,
        field_type: str = None,
        isAbout: Iterable[IsAbout] = None,
        valueReference: Iterable[ValueReference] = None,
        unit: str = None,
        resource: "Resource" = None,
    ):
        self.name = name
        self.description = description
        self.type = field_type
        self.isAbout = isAbout
        self.valueReference = valueReference
        self.unit = unit
        self.resource = resource

    def __repr__(self):
        return "{}({})".format(
            self.__class__.__name__,
            ",".join(
                "{}={}".format(key, val)
                for key, val in self.__dict__.items()
                if key != "resource"
            ),
        )


class Agency(Compilable):
    __compiler_name__ = "agency"

    def __init__(self, name: str = None, logo: str = None):
        self.name = name
        self.logo = logo


class Context(Compilable):
    __compiler_name__ = "context"

    def __init__(
        self,
        homepage: str = None,
        documentation: str = None,
        source_code: str = None,
        contact: str = None,
        grant_number: str = None,
        funding_agency: Agency = None,
        publisher: Agency = None,
    ):
        self.homepage = homepage
        self.documentation = documentation
        self.source_code = source_code
        self.contact = contact
        self.grant_number = grant_number
        self.funding_agency = funding_agency
        self.publisher = publisher


class Reference(Compilable):
    __compiler_name__ = "reference"

    def __init__(self, source: Field = None, target: Field = None):
        self.source = source
        self.target = target


class ForeignKey(Compilable):
    __compiler_name__ = "foreign_key"

    def __init__(self, references: Iterable[Reference] = None):
        self.references = references


class Schema(Compilable):
    __compiler_name__ = "schema"

    def __init__(
        self,
        fields: Iterable[Field] = None,
        primary_key: Iterable[str] = None,
        foreign_keys: Iterable[ForeignKey] = None,
    ):
        self.fields = fields
        self.primary_key = primary_key
        self.foreign_keys = foreign_keys


class Dialect(Compilable):
    __compiler_name__ = "dialect"

    def __init__(self, delimiter: str = None, decimal_separator: str = None):
        self.delimiter = delimiter
        self.decimal_separator = decimal_separator


class Resource(Compilable):
    __compiler_name__ = "resource"

    def __init__(
        self,
        name: str = None,
        path: str = None,
        profile: str = None,
        resource_format: str = None,
        encoding: str = None,
        schema: Schema = None,
        dialect: Dialect = None,
    ):
        self.name = name
        self.path = path
        self.profile = profile
        self.format = resource_format
        self.encoding = encoding
        self.schema = schema
        if schema is not None:
            for field in schema.fields:
                field.resource = self
        self.dialect = dialect


class MetaComment(Compilable):
    __compiler_name__ = "meta_comment"

    def __init__(
        self,
        metadata_info: str = None,
        dates: str = None,
        units: str = None,
        languages: str = None,
        licenses: str = None,
        review: str = None,
        null: str = None,
        todo: str = None,
    ):
        self.metadata_info = metadata_info
        self.dates = dates
        self.units = units
        self.languages = languages
        self.licenses = licenses
        self.review = review
        self.null = null
        self.todo = todo


class Review(Compilable):
    __compiler_name__ = "review"

    def __init__(self, path: str = None, badge: str = None):
        self.path = path
        self.badge = badge


class OEPMetadata(Compilable):
    __compiler_name__ = "metadata"
    __required__ = ["id"]

    def __init__(
        self,
        name: str = None,
        title: str = None,
        identifier: str = None,
        description: str = None,
        languages: Iterable[Language] = None,
        subject: Iterable[Subject] = None,
        keywords: Iterable[str] = None,
        publication_date: datetime = None,
        context: Context = None,
        spatial: Spatial = None,
        temporal: Temporal = None,
        sources: Iterable[Source] = None,
        terms_of_use: Iterable[TermsOfUse] = None,
        contributions: Iterable[Contribution] = None,
        resources: Iterable[Resource] = None,
        databus_identifier: str = None,
        databus_context: str = None,
        review: Review = None,
        comment: MetaComment = None,
    ):
        self.name = name
        self.title = title
        self.identifier = identifier
        self.description = description
        self.subject = subject
        self.languages = languages
        self.keywords = keywords
        self.publication_date = publication_date
        self.context = context
        self.spatial = spatial
        self.temporal = temporal
        self.sources = sources
        self.license = terms_of_use
        self.contributions = contributions
        self.resources = resources
        self.databus_identifier = databus_identifier
        self.databus_context = databus_context
        self.review = review
        self.comment = comment

    def has_keywords(self):
        return self.keywords is not None
