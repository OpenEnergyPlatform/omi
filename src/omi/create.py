"""Entry point for OEMetadata creation (split-files layout only)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from omi.creation.creator import OEMetadataCreator
from omi.creation.utils import apply_template_to_resources, load_parts

if TYPE_CHECKING:
    from pathlib import Path


def build_from_yaml(
    base_dir: Union[str, Path],
    dataset_id: str,
    output_file: Union[str, Path],
    *,
    index_file: Optional[Union[str, Path]] = None,
) -> None:
    """
    Assemble OEMetadata from split YAML files.

      - datasets/<dataset_id>.dataset.yaml
      - datasets/<dataset_id>.template.yaml  (optional)
      - resources/<dataset_id>/*.resource.yaml
      (optionally resolved via an index YAML)

    Parameters
    ----------
    base_dir : str | Path
        Root directory containing 'datasets/' and 'resources/'.
    dataset_id : str
        Logical dataset id (e.g. 'powerplants').
    output_file : str | Path
        Output path for the generated OEMetadata JSON.
    index_file : str | Path | None
        Optional explicit mapping file (metadata_index.yaml).
    """
    version, dataset, resources, template = load_parts(base_dir, dataset_id, index_file=index_file)
    merged_resources = apply_template_to_resources(resources, template)

    creator = OEMetadataCreator(oem_version=version)
    creator.save(dataset, merged_resources, output_file, ensure_ascii=False, indent=2)
