"""Utility functions for OMI creation module."""

from pathlib import Path
from typing import Union

import yaml


def load_yaml_metadata(file_path: Union[str, Path]) -> tuple[str, dict, list[dict], dict]:
    """
    Load YAML file containing version, dataset, template, and resource metadata.

    This function reads a YAML file and extracts the version, dataset description,
    resources, and template. It applies the template to each resource, merging any
    specified fields.
    Returns: version, dataset, list of resources with merged template, and raw template.

    Parameters
    ----------
    file_path: Union[str, Path]
        Path to the YAML file.

    Returns
    -------
    Tuple[str, Dict, List[Dict], Dict]
        A tuple containing:
        - version: The version of the metadata.
        - dataset: The dataset description.
        - resources: A list of resources with the template applied.
        - template: The raw template used for resources.
    """
    with Path(file_path).open(encoding="utf-8") as file:
        data = yaml.safe_load(file)

    version = data.get("version", "OEMetadata-2.0.4")
    dataset = data.get("dataset", {})
    template = data.get("template", {})
    resources = data.get("resources", [])

    # Apply template to each resource
    for resource in resources:
        for key, value in template.items():
            resource.setdefault(key, value)

    return version, dataset, resources
