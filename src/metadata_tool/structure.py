from datetime import datetime
from enum import Enum
from typing import Iterable


class Compilable:
    __compiler_name__ = None

    def __repr__(self):
        return "{}({})".format(
            self.__class__.__name__,
            ",".join("{}={}".format(key, val) for key, val in self.__dict__.items()),
        )

    def __lt__(self, other):
        for key in sorted(self.__dict__):
            s = getattr(self, key)
            o = getattr(other, key)
            if s is None:
                return True
            elif s < o:
                return True
            elif s > o:
                return False
        return False


class Language(Compilable):
    __compiler_name__ = "language"


class Spatial(Compilable):
    __compiler_name__ = "spatial"

    def __init__(self, location: str, extent: str, resolution: str):
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


class Temporal(Compilable):
    __compiler_name__ = "temporal"

    def __init__(
        self,
        reference_date: datetime,
        start: datetime,
        end: datetime,
        resolution: str,
        ts_orientation: TimestampOrientation,
    ):  # TODO: This should not be a string... maybe
        # we should use datetime instead?
        self.reference_date = reference_date
        self.ts_start = start
        self.ts_end = end
        self.ts_resolution = resolution
        self.ts_orientation = ts_orientation


class License(Compilable):
    __compiler_name__ = "license"

    def __init__(
        self,
        name: str,
        identifier: str,
        text: str,
        path: str,
        other_references: Iterable[str],
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

    def __init__(self, instruction: str, attribution: str, lic: License):
        self.instruction = instruction
        self.attribution = attribution
        self.license = lic


class Source(Compilable):
    __compiler_name__ = "source"

    def __init__(
        self,
        title: str,
        description: str,
        path: str,
        source_license: License,
        source_copyright: str,
    ):
        self.title = title
        self.description = description
        self.path = path
        self.license = source_license
        self.copyright = source_copyright


class Person(Compilable):
    __compiler_name__ = "person"

    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email


class Contribution(Compilable):
    __compiler_name__ = "contribution"

    def __init__(self, contributor: Person, date: datetime, obj: str, comment: str):
        self.contributor = contributor
        self.date = date
        self.object = obj
        self.comment = comment


class Field(Compilable):
    __compiler_name__ = "field"

    def __init__(
        self,
        name: str,
        description: str,
        field_type: str,
        unit: str,
        resource: "Resource" = None,
    ):
        self.name = name
        self.description = description
        self.type = field_type
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


class Context(Compilable):
    __compiler_name__ = "context"

    def __init__(
        self,
        homepage: str,
        documentation: str,
        source_code: str,
        contact: str,
        grant_number: str,
    ):
        self.homepage = homepage
        self.documentation = documentation
        self.source_code = source_code
        self.contact = contact
        self.grant_number = grant_number


class Reference(Compilable):
    __compiler_name__ = "reference"

    def __init__(self, source: Field, target: Field):
        self.source = source
        self.target = target


class ForeignKey(Compilable):
    __compiler_name__ = "foreign_key"

    def __init__(self, references: Iterable[Reference]):
        self.references = references


class Schema(Compilable):
    __compiler_name__ = "schema"

    def __init__(
        self,
        fields: Iterable[Field],
        primary_key: Iterable[str],
        foreign_keys: Iterable[ForeignKey],
    ):
        self.fields = fields
        self.primary_key = primary_key
        self.foreign_keys = foreign_keys


class Dialect(Compilable):
    __compiler_name__ = "dialect"

    def __init__(self, delimiter: str, decimal_separator: str):
        self.delimiter = delimiter
        self.decimal_separator = decimal_separator


class Resource(Compilable):
    __compiler_name__ = "resource"

    def __init__(
        self,
        name: str,
        path: str,
        profile: str,
        resource_format: str,
        encoding: str,
        schema: Schema,
        dialect: Dialect,
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
        metadata_info: str,
        dates: str,
        units: str,
        languages: str,
        licenses: str,
        review: str,
        none: str,
    ):
        self.metadata_info = metadata_info
        self.dates = dates
        self.units = units
        self.languages = languages
        self.licenses = licenses
        self.review = review
        self.none = none


class Review(Compilable):
    __compiler_name__ = "review"

    def __init__(self, path: str, badge: str):
        self.path = path
        self.badge = badge


class OEPMetadata(Compilable):
    __compiler_name__ = "metadata"

    def __init__(
        self,
        name: str,
        title: str,
        identifier: str,
        description: str,
        languages: Iterable[Language],
        keywords: Iterable[str],
        publication_date: datetime,
        context: Context,
        spatial: Spatial,
        temporal: Temporal,
        sources: Iterable[Source],
        terms_of_use: Iterable[TermsOfUse],
        contributions: Iterable[Contribution],
        resources: Iterable[Resource],
        review: Review,
        comment: MetaComment,
    ):
        self.name = name
        self.title = title
        self.identifier = identifier
        self.description = description
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
        self.review = review
        self.comment = comment

    def has_keywords(self):
        return self.keywords is not None
