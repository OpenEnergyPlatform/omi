"""Create oemetadata json datapackage descriptions."""

from omi.base import get_metadata_specification
from omi.validation import validate_metadata


class OEMetadataCreator:
    """
    Class to create oemetadata json datapackages.

    Output is based on datapackage and resource descriptions.
    """

    def __init__(self, oem_version: str = "OEMetadata-2.0") -> None:
        """
        Initialize the OEMetadataCreator with a specific version.

        Parameters
        ----------
        oem_version:str
            The version of the OEMetadata specification to use.
        """
        self.oem_spec = get_metadata_specification(oem_version)

    def generate_metadata(self, dataset: dict, resources: list[dict]) -> dict:
        """
        Generate oemetadata json datapackage from dataset and resources.

        Parameters
        ----------
        dataset: dict
            The dataset description.
        resources: list[dict]
            The list of resource descriptions.

        Returns
        -------
        dict
            The generated oemetadata json datapackage.
        """
        metadata = {
            "@context": self.oem_spec.schema["properties"]["@context"]["examples"][0],
            **dataset,
            "resources": resources,
            "metaMetadata": self.oem_spec.example["metaMetadata"],
        }

        validate_metadata(metadata, check_license=False)
        return metadata
