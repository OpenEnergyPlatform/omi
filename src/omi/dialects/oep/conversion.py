from datetime import datetime
import json
import logging
import pathlib

from omi.dialects.base.dialect import Dialect
from omi.dialects import get_dialect
from omi import structure
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
        dielact_id: str = "oep-v1.5", #latest version
        metadata: structure.OEPMetadata = None,
    ) -> None:
        self.dialect_id = dielact_id
        self.metadata = metadata

    def validate_str_version_format(self):
        return NotImplementedError

    def format_version_string(self, version_string: str = None) -> str:
        if version_string is not None:
            version_string = version_string.lower()
            parts = version_string.split(sep="-")
            self.dialect_id = parts[0] + "-v" + parts[1][:-2]
        return self.dialect_id

    def detect_oemetadata_dialect(self) -> Dialect:
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
        return get_dialect(identifier=self.dialect_id)

    #NOTE: Add omi version to user? 
    def set_contribution(
        self, metadata: oem_v15.OEPMetadata, user: str = "OMI", user_email: str = None
    ) -> oem_v15.OEPMetadata:
        contribution = oem_v15.Contribution(
            contributor=oem_v15.Person(name=user, email=user_email),
            date=datetime.now(),
            obj="Metadata conversion",
            comment="Update metadata to "
            + self.dialect_id
            + " using OMIs metadata conversion tool.",
        )

        metadata = metadata.contributions.append(contribution)

        return metadata

    def convert_oemetadata():
        pass