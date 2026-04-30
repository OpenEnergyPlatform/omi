"""Entry point for OEMetadata creation (split-files layout only)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Union

from omi.creation.assembler import assemble_many_metadata, assemble_metadata_dict


def build_from_yaml(
    base_dir: Union[str, Path],
    dataset_id: str,
    output_file: Union[str, Path],
    *,
    index_file: Optional[Union[str, Path]] = None,
) -> None:
    """
    Assemble one dataset and write the resulting OEMetadata JSON to a file.

    Parameters
    ----------
    base_dir : Union[str, Path]
        Base directory containing the split-files dataset structure.
    dataset_id : str
        The dataset ID to assemble.
    output_file : Union[str, Path]
        Path to write the resulting OEMetadata JSON file.
    index_file : Optional[Union[str, Path]], optional
        Optional path to an index file for resolving cross-dataset references,
        by default None.
    """
    md = assemble_metadata_dict(base_dir, dataset_id, index_file=index_file)
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    Path(output_file).write_text(json.dumps(md, indent=2, ensure_ascii=False), encoding="utf-8")


def build_many_from_yaml(
    base_dir: Union[str, Path],
    output_dir: Union[str, Path],
    *,
    dataset_ids: Optional[list[str]] = None,
    index_file: Optional[Union[str, Path]] = None,
) -> None:
    """
    Assemble multiple datasets and write each as <dataset_id>.json to output_dir.

    Parameters
    ----------
    base_dir : Union[str, Path]
        Base directory containing the split-files dataset structure.
    output_dir : Union[str, Path]
        Directory to write the resulting OEMetadata JSON files.
    dataset_ids : Optional[list[str]], optional
        Optional list of dataset IDs to assemble. If None, all datasets found
        in base_dir will be assembled, by default None.
    index_file : Optional[Union[str, Path]], optional
        Optional path to an index file for resolving cross-dataset references,
        by default None.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results = assemble_many_metadata(
        base_dir,
        dataset_ids=dataset_ids,
        index_file=index_file,
        as_dict=True,  # keep it as a mapping id -> metadata
    )
    for ds_id, md in results.items():
        (out_dir / f"{ds_id}.json").write_text(
            json.dumps(md, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
