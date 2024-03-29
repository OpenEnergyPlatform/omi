import datetime
import logging

from omi import structure
from omi.dialects.base.compiler import Compiler
from omi.oem_structures import oem_v15


def compile_date_or_none(x, format=None):
    if isinstance(x, (datetime.datetime, datetime.date)):
        if format:
            return x.strftime(format)
        else:
            return x.isoformat()
    else:
        return x


class JSONCompiler(Compiler):
    __METADATA_VERSION = "OEP-1.4.0"
    OMIT_NONE_FIELDS = False

    def _construct_dict(self, *args, omit_none=None, **kwargs):
        """
        Accepts a list of arguments of shape (name: str, field: Compileable) and returns a dictionary that maps
        name -> self.visit(field). If `omit_none` is true, fields that are `None` are ignored.
        Parameters
        ----------
        args
        omit_none
        kwargs

        Returns
        -------

        """
        omit_none = self.OMIT_NONE_FIELDS
        d = {
            field_name: self.visit(field)
            for field_name, field in args
            if (not omit_none) or (field is not None)
        }
        d.update(**kwargs)
        return d

    def visit_context(self, context: structure.Context, *args, **kwargs):
        result = self._construct_dict(
            ("homepage", context.homepage),
            ("documentation", context.documentation),
            ("sourceCode", context.source_code),
            ("contact", context.contact),
            ("grantNo", context.grant_number),
        )
        if context.funding_agency is not None:
            result["fundingAgency"] = context.funding_agency.name
            result["fundingAgencyLogo"] = context.funding_agency.logo
        if context.publisher is not None:
            result["publisherLogo"] = context.publisher.logo
        logging.info(
            f"The context is parsed from file with the following values: {context}"
        )
        logging.info(
            f"The context class is compiled to the following python dict: {result}"
        )
        return result

    def visit_contribution(self, contribution: structure.Contribution, *args, **kwargs):
        result = self._construct_dict(
            ("title", contribution.contributor.name),
            ("email", contribution.contributor.email),
            ("object", contribution.object),
            ("comment", contribution.comment),
            ("date", compile_date_or_none(contribution.date, "%Y-%m-%d")),
        )
        logging.info(
            f"The contributions are parsed from file with the following values: {contribution}"
        )
        logging.info(
            f"The contributions class is compiled to the following python dict: {result}"
        )
        return result

    def visit_language(self, language: structure.Language, *args, **kwargs):
        return str(language)

    def visit_spatial(self, spatial: structure.Spatial, *args, **kwargs):
        return self._construct_dict(
            ("location", spatial.location),
            ("extent", spatial.extent),
            ("resolution", spatial.resolution),
        )

    def visit_timestamp_orientation(
        self, tso: structure.TimestampOrientation, *args, **kwargs
    ):
        if tso == structure.TimestampOrientation.left:
            return "left"
        elif tso == structure.TimestampOrientation.middle:
            return "middle"
        elif tso == structure.TimestampOrientation.right:
            return "right"
        else:
            raise NotImplementedError

    def visit_temporal(self, temporal: structure.Temporal, *args, **kwargs):
        start = None
        end = None
        if temporal.ts_start is not None:
            start = compile_date_or_none(temporal.ts_start)
        if temporal.ts_end is not None:
            end = compile_date_or_none(temporal.ts_end)
        return self._construct_dict(
            (
                "referenceDate",
                compile_date_or_none(temporal.reference_date, "%Y-%m-%d"),
            ),
            timeseries=self._construct_dict(
                ("start", start),
                ("end", end),
                ("resolution", temporal.ts_resolution),
                ("alignment", temporal.ts_orientation),
                ("aggregationType", temporal.aggregation),
            ),
        )

    def visit_source(self, source: structure.Source, *args, **kwargs):
        return self._construct_dict(
            ("title", source.title),
            ("description", source.description),
            ("path", source.path),
            ("licenses", source.licenses),
        )

    def visit_license(self, lic: structure.License, *args, **kwargs):
        return self._construct_dict(
            ("name", lic.identifier),
            ("title", lic.name),
            ("path", lic.path),
        )

    def visit_terms_of_use(self, terms_of_use: structure.TermsOfUse):
        license_kwargs = (
            self.visit(terms_of_use.license) if terms_of_use.license else {}
        )
        return self._construct_dict(
            ("instruction", terms_of_use.instruction),
            ("attribution", terms_of_use.attribution),
            **license_kwargs,
        )

    def visit_resource(self, resource: structure.Resource, *args, **kwargs):
        return self._construct_dict(
            ("profile", resource.profile),
            ("name", resource.name),
            ("path", resource.path),
            ("format", resource.format),
            ("encoding", resource.encoding),
            ("schema", resource.schema),
            ("dialect", resource.dialect),
        )

    def visit_field(self, field: structure.Field, *args, **kwargs):
        return self._construct_dict(
            ("name", field.name),
            ("description", field.description),
            ("type", field.type),
            ("unit", field.unit),
        )

    def visit_schema(self, schema: structure.Schema, *args, **kwargs):
        return self._construct_dict(
            ("primaryKey", schema.primary_key),
            ("foreignKeys", schema.foreign_keys),
            ("fields", schema.fields),
        )

    def visit_dialect(self, dialect: structure.Dialect, *args, **kwargs):
        return self._construct_dict(
            ("delimiter", dialect.delimiter),
            ("decimalSeparator", dialect.decimal_separator),
        )

    def visit_foreign_key(self, foreign_key: structure.ForeignKey, *args, **kwargs):
        if foreign_key.references:
            source_fields, target_fields, target_resources = zip(
                *map(self.visit, foreign_key.references)
            )
            target_resource = target_resources[0]

            return self._construct_dict(
                ("fields", source_fields),
                reference=self._construct_dict(
                    ("resource", target_resource),
                    ("fields", target_fields),
                ),
            )
        else:
            raise Exception("Missing reference in foreign key")

    def visit_reference(self, reference: structure.Reference, *args, **kwargs):
        return (
            reference.source.name,
            reference.target.name,
            reference.target.resource.name,
        )

    def visit_review(self, review: structure.Review, *args, **kwargs):
        return self._construct_dict(("path", review.path), badge=review.badge)

    def visit_meta_comment(self, comment: structure.MetaComment, *args, **kwargs):
        return self._construct_dict(
            ("metadata", comment.metadata_info),
            ("dates", comment.dates),
            ("units", comment.units),
            ("languages", comment.languages),
            ("licenses", comment.licenses),
            ("review", comment.review),
            ("null", comment.none),
        )

    def visit_metadata(self, metadata: structure.OEPMetadata, *args, **kwargs):
        publication_date = None
        if metadata.publication_date is not None:
            publication_date = compile_date_or_none(
                metadata.publication_date, "%Y-%m-%d"
            )
        return self._construct_dict(
            ("name", metadata.name),
            ("title", metadata.title),
            ("id", metadata.identifier),
            ("description", metadata.description),
            ("keywords", metadata.keywords),
            ("publicationDate", publication_date),
            ("context", metadata.context),
            ("spatial", metadata.spatial),
            ("temporal", metadata.temporal),
            ("review", metadata.review),
            ("language", metadata.languages),
            ("sources", metadata.sources),
            ("licenses", metadata.license),
            ("contributors", metadata.contributions),
            ("resources", metadata.resources),
            ("_comment", metadata.comment),
            metaMetadata=self._construct_dict(
                ("metadataVersion", self.__METADATA_VERSION),
                metadataLicense=self._construct_dict(
                    name="CC0-1.0",
                    title="Creative Commons Zero v1.0 Universal",
                    path="https://creativecommons.org/publicdomain/zero/1.0/",
                ),
            ),
        )


class JSONCompilerOEM15(JSONCompiler):
    """
    Compiles OEMetadata version JSONCompilerOEM15.__METADATA_VERSION .

    Args:
        JSONCompiler (object):  Parent Class provides compiler methods for all
                                metadata fields that have not been changed in
                                the metadata structure.
    """

    __METADATA_VERSION = "OEP-1.5.2"

    def visit(self, obj, *args, **kwargs):
        """
        Calls the respective compiler for :class:`~omi.structure.Compilable` objects
        respective to :attr:`Compilable.__compiler_name__`


        Parameters
        ----------
        obj
            Object to compile

        Returns
        -------
            Metadata representation of `obj`

        """
        if isinstance(obj, list):
            return [self.visit(x) for x in obj if x is not None]
        if isinstance(obj, oem_v15.Compilable):
            meth = getattr(self, "visit_{name}".format(name=obj.__compiler_name__))
            return meth(obj, *args, **kwargs)
        else:
            return obj

    def visit_subject(self, subject: oem_v15.Subject, *args, **kwargs):
        return self._construct_dict(("name", subject.name), ("path", subject.path))

    def visit_timestamp_orientation(
        self, tso: oem_v15.TimestampOrientation, *args, **kwargs
    ):
        if tso == oem_v15.TimestampOrientation.left:
            return "left"
        elif tso == oem_v15.TimestampOrientation.middle:
            return "middle"
        elif tso == oem_v15.TimestampOrientation.right:
            return "right"
        else:
            raise NotImplementedError

    def visit_timeseries(self, timeseries: oem_v15.Timeseries, *args, **kwargs):
        start = None
        end = None
        if timeseries.ts_start is not None:
            start = compile_date_or_none(timeseries.ts_start)
        if timeseries.ts_end is not None:
            end = compile_date_or_none(timeseries.ts_end)
        return self._construct_dict(
            ("start", start),
            ("end", end),
            ("resolution", timeseries.ts_resolution),
            ("alignment", timeseries.ts_orientation),
            ("aggregationType", timeseries.aggregation),
        )

    def visit_temporal(self, temporal: oem_v15.Temporal, *args, **kwargs):
        return self._construct_dict(
            (
                "referenceDate",
                compile_date_or_none(temporal.reference_date, "%Y-%m-%d"),
            ),
            ("timeseries", temporal.timeseries_collection),
        )

    def visit_license(self, lic: oem_v15.License, *args, **kwargs):
        return self._construct_dict(
            ("name", lic.name),
            ("title", lic.title),
            ("path", lic.path),
        )

    def visit_isAbout(self, isAbout: oem_v15.IsAbout, *args, **kwargs):
        return self._construct_dict(("name", isAbout.name), ("path", isAbout.path))

    def visit_valueReference(
        self, valueReference: oem_v15.ValueReference, *args, **kwargs
    ):
        return self._construct_dict(
            ("value", valueReference.value),
            ("name", valueReference.name),
            ("path", valueReference.path),
        )

    def visit_field(self, field: oem_v15.Field, *args, **kwargs):
        return self._construct_dict(
            ("name", field.name),
            ("description", field.description),
            ("type", field.type),
            ("isAbout", field.isAbout),
            ("valueReference", field.valueReference),
            ("unit", field.unit),
        )

    def visit_meta_comment(self, comment: oem_v15.MetaComment, *args, **kwargs):
        return self._construct_dict(
            ("metadata", comment.metadata_info),
            ("dates", comment.dates),
            ("units", comment.units),
            ("languages", comment.languages),
            ("licenses", comment.licenses),
            ("review", comment.review),
            ("null", comment.null),
            ("todo", comment.todo),
        )

    def visit_metadata(self, metadata: oem_v15.OEPMetadata, *args, **kwargs):
        publication_date = None
        if metadata.publication_date is not None:
            publication_date = compile_date_or_none(
                metadata.publication_date, "%Y-%m-%d"
            )
        return self._construct_dict(
            ("name", metadata.name),
            ("title", metadata.title),
            ("id", metadata.identifier),
            ("description", metadata.description),
            ("subject", metadata.subject),
            ("language", metadata.languages),
            ("keywords", metadata.keywords),
            ("publicationDate", publication_date),
            ("context", metadata.context),
            ("spatial", metadata.spatial),
            ("temporal", metadata.temporal),
            ("sources", metadata.sources),
            ("licenses", metadata.license),
            ("contributors", metadata.contributions),
            ("resources", metadata.resources),
            ("@id", metadata.databus_identifier),
            ("@context", metadata.databus_context),
            ("review", metadata.review),
            metaMetadata=self._construct_dict(
                ("metadataVersion", self.__METADATA_VERSION),
                metadataLicense=self._construct_dict(
                    name="CC0-1.0",
                    title="Creative Commons Zero v1.0 Universal",
                    path="https://creativecommons.org/publicdomain/zero/1.0/",
                ),
            ),
            _comment=self._construct_dict(
                metadata="Metadata documentation and explanation (https://github.com/OpenEnergyPlatform/oemetadata)",
                dates="Dates and time must follow the ISO8601 including time zone (YYYY-MM-DD or YYYY-MM-DDThh:mm:ss±hh)",
                units="Use a space between numbers and units (100 m)",
                languages="Languages must follow the IETF (BCP47) format (en-GB, en-US, de-DE)",
                licenses="License name must follow the SPDX License List (https://spdx.org/licenses/)",
                review="Following the OEP Data Review (https://github.com/OpenEnergyPlatform/data-preprocessing/blob/master/data-review/manual/review_manual.md)",
                null="If not applicable use: null",
                todo="If a value is not yet available, use: todo",
            ),
            **kwargs,
        )
