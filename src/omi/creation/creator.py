"""Create OEMetadata JSON datapackage structure and return or store it."""

from __future__ import annotations

import json
from pathlib import Path

from omi.base import get_metadata_specification
from omi.validation import validate_metadata


class OEMetadataCreator:
    """
    Create OEMetadata JSON datapackages.

    Output is based on dataset and resource descriptions and validated against
    the official schema.
    """

    def __init__(self, oem_version: str = "OEMetadata-2.0") -> None:
        """Initialize the creator with a specific OEMetadata version."""
        self.oem_spec = get_metadata_specification(oem_version)

    def generate_metadata(self, dataset: dict, resources: list[dict]) -> dict:
        """Generate OEMetadata JSON datapackage from dataset and resources."""
        metadata = {
            "@context": self.oem_spec.schema["properties"]["@context"]["examples"][0],
            **dataset,
            "resources": resources,
            "metaMetadata": self.oem_spec.example["metaMetadata"],
        }

        validate_metadata(metadata, check_license=False)
        return metadata

    def save(
        self,
        dataset: dict,
        resources: list[dict],
        output_file: Path | str,
        **dump_kwargs,
    ) -> None:
        """
        Generate OEMetadata and save it to a JSON file.

        Parameters
        ----------
        dataset : dict
            Dataset metadata.
        resources : list[dict]
            List of resource metadata entries.
        output_file : Path | str
            Path to the output JSON file.
        **dump_kwargs :
            Extra kwargs forwarded to `json.dump`. Defaults applied here:
            - indent: 2
            - ensure_ascii: False
        """
        metadata = self.generate_metadata(dataset, resources)

        # Defaults, can be overridden by caller via **dump_kwargs
        indent = dump_kwargs.pop("indent", 2)
        ensure_ascii = dump_kwargs.pop("ensure_ascii", False)

        with Path(output_file).open("w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=indent, ensure_ascii=ensure_ascii, **dump_kwargs)

        print(f"OEMetadata written to {output_file}")  # noqa: T201
