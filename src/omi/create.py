"""Enty point for metadata creation."""

import json
from pathlib import Path
from typing import Union

from omi.creation.creator import OEMetadataCreator
from omi.creation.utils import load_yaml_metadata


def from_yaml(yaml_file: Union[str, Path], output_file: Union[str, Path]) -> None:
    """
    Generate OEMetadata from a YAML file and write it to an output file.

    Parameters
    ----------
    yaml_file: str
        Path to the input YAML file containing dataset and resources.
    output_file: str
        Path to the output file where the generated OEMetadata JSON will be saved.
    """
    version, dataset, resources = load_yaml_metadata(yaml_file)
    creator = OEMetadataCreator()
    metadata = creator.generate_metadata(dataset, resources)

    with Path(output_file).open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"OEMetadata written to {output_file}")  # noqa: T201
