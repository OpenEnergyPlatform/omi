"""
The conversion in OMI is used to translate metadata version, usually from low to high version.

The Converter class is the base class that provides base funtionality to enable a specific version translateion.

The Translation class includes all functionality to create missing fields and supply default, none or user input values for each new field.
The translated metadata will be build and can be saved to a file by using convinience methodes provides by the converter or manually saved 
to file using OMI's dialect15.compile_and_render().

BUGS:
- oeo keys are not included
- value reference and is about got wrong name format in json
"""

import json
import logging
import pathlib
from datetime import datetime

from omi import structure
from omi.dialects import get_dialect
from omi.dialects.base.dialect import Dialect
from omi.oem_structures import oem_v15


# NOTE: Maybe change this to abstract class and implement methods in concrete child classes
class Converter:
    """
    Base Converter class for oemetadata version conversion.
    Provides basic converstion functions and helpers.
    All concrete conversion classes should inheret from this class.

    """

    def __init__(
        self,
        dielact_id: str = "oep-v1.5",  # latest version
        metadata: structure.OEPMetadata = None,
    ) -> None:
        self.dialect_id = dielact_id
        self.metadata = metadata
        self.omi_version = "OMI-v0.0.8"

    def validate_str_version_format(self):
        return NotImplementedError

    def sanitize_oem(self, oemetadata: dict) -> oem_v15.OEPMetadata:
        """
        Remove all "" or " " values. Additionaly it is possible to specify a specific
        field that will set to none. Key that got a none value will result in a json null
        that will not be visible in a json document.

        Args:
            oemetadata (oem_v15.OEPMetadata): _description_

        Returns:
            oem_v15.OEPMetadata: _description_
        """

        omi_dialect = self.detect_oemetadata_dialect(oemetadata)
        metadata = omi_dialect._parser().parse(oemetadata)
        print(type(omi_dialect))

        if (
            metadata["metaMetadata"]["metadataVersion"] == "oep-v1.5.1"
        ):  # NOTE hardcoded
            oemetadata_obj: oem_v15.OEPMetadata
            # sanitize ....
        else:
            oemetadata_obj: structure.OEPMetadata
            # sanitize ....

        return oemetadata_obj

    def format_version_string(self, version_string: str = None) -> str:
        if version_string is not None:
            version_string = version_string.lower()
            parts = version_string.split(sep="-")
            self.dialect_id = parts[0] + "-v" + parts[1][:-2]
        return self.dialect_id

    def detect_oemetadata_dialect(self, metadata=None) -> Dialect:
        if metadata is None:
            try:
                version: str = self.metadata["metaMetadata"]["metadataVersion"]
                self.dialect_id = self.format_version_string(version_string=version)
                logging.info(f"The dectected dialect is: {self.dialect_id}")
            except Exception as e:
                logging.warning(
                    {
                        "exception": f"{e}",
                        "message": f"Could not detect the dialect based on the Oemetadata json string. The key related to meta-metadata information might not be present in the input metadata json file. Fallback to the default dialect: '{self.dialect_id}'.",
                    }
                )
        else:
            try:
                version: str = metadata["metaMetadata"]["metadataVersion"]
                self.dialect_id = self.format_version_string(version_string=version)
                logging.info(f"The dectected dialect is: {self.dialect_id}")
            except Exception as e:
                logging.warning(
                    {
                        "exception": f"{e}",
                        "message": f"Could not detect the dialect based on the Oemetadata json string. The key related to meta-metadata information might not be present in the input metadata json file. Fallback to the default dialect: '{self.dialect_id}'.",
                    }
                )

        return get_dialect(identifier=self.dialect_id)

    # NOTE: Add omi version to user?
    def set_contribution(
        self,
        metadata: oem_v15.OEPMetadata,
        user: str = "OMI-v0.0.8",
        user_email: str = None,
    ) -> oem_v15.OEPMetadata:
        to_metadata = "oep-v1.5.1"  # NOTE hardcoded
        contribution = oem_v15.Contribution(
            contributor=oem_v15.Person(name=user, email=user_email),
            date=datetime.now(),
            obj="Metadata conversion",
            comment="Update metadata to "
            + to_metadata
            + " using OMIs metadata conversion tool.",
        )

        metadata = metadata.contributions.append(contribution)

        return metadata

    def convert_oemetadata():
        pass


class Metadata14To15Translation(Converter):
    """
    Converts/translates the oemetadata object generated based on the input oemetadata.json file to oemetadata-v1.5.1 structure.

    Args:
        Converter : Base converter class
    """

    def remove_temporal(
        self, metadata14: structure.OEPMetadata
    ) -> structure.OEPMetadata:
        metadata14.temporal = None
        return metadata14

    @staticmethod
    def create_subject(subject: oem_v15.Subject, name: str = "", path: str = ""):
        subject = subject()
        subject.name = name
        subject.path = path
        return subject

    @staticmethod
    def create_oeo_id(oeo_id: str = None):
        return oeo_id

    @staticmethod
    def create_oeo_context(oeo_context: str = None):
        return oeo_context

    # NOTE: need?
    @staticmethod
    def create_meta_comment_null(
        meta_comment_null: str = "If not applicable use: null",  # hardcoded
    ):
        return meta_comment_null

    @staticmethod
    def create_meta_comment_todo(
        meta_comment_todo: str = "If a value is not yet available, use: todo",  # hardcoded
    ):
        return meta_comment_todo

    @staticmethod
    def create_is_about(is_about: oem_v15.IsAbout, name: str = "", path: str = ""):
        is_about = is_about()
        is_about.name = name
        is_about.path = path
        return is_about

    @staticmethod
    def create_value_reference(
        value_reference: oem_v15.ValueReference,
        value: str = "",
        name: str = "",
        path: str = "",
    ):
        value_reference = value_reference()
        value_reference.value = value
        value_reference.name = name
        value_reference.path = path
        return value_reference

    def convert_timestamp_orientation(self, ts: str):
        new_ts = oem_v15.TimestampOrientation.create(ts)
        return new_ts

    # NOTE maybe move timeseries element from convert temporal
    def convert_timeseries(self, metadata14_temporal: structure.Temporal):
        timeseries = None
        if metadata14_temporal.ts_start and metadata14_temporal.ts_end is not None:
            timeseries = oem_v15.Timeseries(
                start=metadata14_temporal.ts_start,
                end=metadata14_temporal.ts_end,
                resolution=metadata14_temporal.ts_resolution,
                ts_orientation=self.convert_timestamp_orientation(
                    metadata14_temporal.ts_orientation.name
                ),
                aggregation=metadata14_temporal.aggregation,
            )
        return timeseries

    def convert_temporal(
        self,
        metadata14_temporal: structure.Temporal,
    ):
        temporal = None
        if metadata14_temporal is not None:
            temporal = oem_v15.Temporal(
                reference_date=metadata14_temporal.reference_date,
                timeseries_collection=[self.convert_timeseries(metadata14_temporal)],
            )  # NOTE: assume there will be a single timeseries as input because OEM-v1.4 did not support multiple timeseries elements
        return temporal

    def convert_meta_comment(
        self, metadata14_meta_comment: structure.MetaComment
    ) -> oem_v15.MetaComment:

        meta_comment = None
        if metadata14_meta_comment is not None:
            meta_comment = oem_v15.MetaComment(
                metadata_info=metadata14_meta_comment.metadata_info,
                dates=metadata14_meta_comment.dates,
                units=metadata14_meta_comment.units,
                languages=metadata14_meta_comment.languages,
                licenses=metadata14_meta_comment.licenses,
                review=metadata14_meta_comment.review,
                null=self.create_meta_comment_null(),
                todo=self.create_meta_comment_todo(),
            )

        return meta_comment

    def convert_ressources_field(self, metadata14_ressources_field: list = None):
        field: oem_v15.Field
        ressources_fields = []
        if metadata14_ressources_field is not None:
            for field in metadata14_ressources_field:
                ressources_field = oem_v15.Field(
                    name=field.name,
                    description=field.description,
                    field_type=field.type,
                    isAbout=[self.create_is_about(oem_v15.IsAbout)],
                    valueReference=[
                        self.create_value_reference(oem_v15.ValueReference)
                    ],
                    unit=field.unit,
                    resource=field.resource,
                )
                ressources_fields.append(ressources_field)
        else:
            ressources_fields = None

        return ressources_fields

    def convert_ressource(self, metadata14_ressources: list):
        ressource: oem_v15.Resource
        ressources = []
        for ressource in metadata14_ressources:
            single_ressource = oem_v15.Resource(
                name=ressource.name,
                path=ressource.path,
                profile=ressource.profile,
                resource_format=ressource.format,
                encoding=ressource.encoding,
                schema=oem_v15.Schema(
                    fields=self.convert_ressources_field(ressource.schema.fields),
                    primary_key=ressource.schema.primary_key,
                    foreign_keys=ressource.schema.foreign_keys,
                ),
                dialect=ressource.dialect,
            )
            ressources.append(single_ressource)

        return ressources

    def build_metadata15(self, metadata: structure.OEPMetadata):
        converted_metadata = oem_v15.OEPMetadata(
            name=metadata.name,
            title=metadata.title,
            identifier=metadata.identifier,
            description=metadata.description,
            subject=[
                self.create_subject(oem_v15.Subject)
            ],  # NOTE add just one dummy subject object, maybe its better to keep it empty? # add value from user input??
            languages=metadata.languages,
            keywords=metadata.keywords,
            publication_date=metadata.publication_date,
            context=metadata.context,
            spatial=metadata.spatial,
            temporal=self.convert_temporal(
                metadata.temporal
            ),  # NOTE add value from user input??
            sources=metadata.sources,
            terms_of_use=metadata.license,
            contributions=metadata.contributions,
            resources=self.convert_ressource(metadata.resources),
            databus_identifier=self.create_oeo_id(),  # NOTE add value from user input??
            databus_context=self.create_oeo_context(),  # NOTE add value from user input??
            review=metadata.review,
            comment=self.convert_meta_comment(metadata.comment),
        )

        return converted_metadata


def read_input_json(file_path: pathlib.Path = "tests/data/metadata_v14.json"):
    with open(file_path, "r", encoding="utf-8") as f:
        jsn = json.load(f)

    return jsn


def save_to_file(metadata: oem_v15.OEPMetadata, file_path: pathlib.Path):

    with open(file_path, "w", encoding="utf-8") as outfile:
        outfile.write(metadata)


def run_conversion(
    to_metadata: str, from_metadata: str, convert=Metadata14To15Translation
):
    metadata_file = read_input_json(from_metadata)
    convert = convert(metadata=metadata_file)
    dialect_input = convert.detect_oemetadata_dialect()
    metadata = dialect_input._parser().parse(metadata_file)
    convert.set_contribution(metadata)

    converted = convert.build_metadata15(metadata)

    dialect15 = get_dialect("oep-v1.5")()
    s = dialect15.compile_and_render(obj=converted)
    save_to_file(s, to_metadata)

    return s


if __name__ == "__main__":

    # Run conversion with test data
    run_conversion(
        to_metadata="1_test_results/metadata/conversion_out_oem151.json",
        from_metadata="tests/data/metadata_v14.json",
    )
