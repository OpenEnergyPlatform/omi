"""Assemble OEMetadata dictionary from parts: dataset, template, and resources."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Union

from .creator import OEMetadataCreator
from .utils import (
    DEFAULT_CONCAT_LIST_KEYS,
    apply_template_to_resources,
    discover_dataset_ids,
    discover_dataset_ids_from_index,
    load_parts,
)

if TYPE_CHECKING:
    from collections.abc import Iterable


def assemble_metadata_dict(
    base_dir: Union[str, Path],
    dataset_id: str,
    index_file: Optional[Union[str, Path]] = None,
    *,
    concat_list_keys: Optional[Iterable[str]] = None,
) -> dict[str, Any]:
    """
    Load dataset/template/resources; apply template; validate via creator; return dict.

    Parameters
    ----------
    base_dir: Union[str, Path]
        Base directory containing datasets, templates, and resources.
    dataset_id: str
        Identifier for the dataset to load.
    index_file: Optional[Union[str, Path]]
        Optional path to an index YAML file for resolving dataset parts.
    concat_list_keys: Optional[Iterable[str]]
        List-valued keys for which template + resource values should be concatenated
        (deduplicated). If None, uses DEFAULT_CONCAT_LIST_KEYS
        (e.g. {"keywords", "topics", "languages"}).

    Returns
    -------
    Dict[str, Any]
        The assembled and validated OEMetadata dictionary.
    """
    version, dataset, resources, template = load_parts(base_dir, dataset_id, index_file)

    keys = set(concat_list_keys) if concat_list_keys is not None else DEFAULT_CONCAT_LIST_KEYS

    merged_resources = apply_template_to_resources(
        resources,
        template,
        concat_list_keys=keys,
    )

    creator = OEMetadataCreator(oem_version=version)
    return creator.generate_metadata(dataset, merged_resources)


def assemble_many_metadata(
    base_dir: Union[str, Path],
    dataset_ids: Optional[Iterable[str]] = None,
    index_file: Optional[Union[str, Path]] = None,
    *,
    as_dict: bool = True,
    concat_list_keys: Optional[Iterable[str]] = None,
) -> Union[dict[str, dict], list[tuple[str, dict]]]:
    """
    Assemble OEMetadata for multiple datasets in one call.

    - If dataset_ids is None:
        * when index_file is provided -> use keys from index
        * otherwise -> discover by 'datasets/*.dataset.yaml'
    - Returns a mapping {dataset_id: metadata} if as_dict=True,
      else a list of (dataset_id, metadata) pairs in sorted id order.

    Parameters
    ----------
    base_dir : Union[str, Path]
        Base directory containing datasets, templates, and resources.
    dataset_ids : Optional[Iterable[str]], optional
        Optional iterable of dataset IDs to assemble. If None, all datasets found
        in base_dir will be assembled, by default None.
    index_file : Optional[Union[str, Path]], optional
        Optional path to an index YAML file for resolving dataset parts.
    as_dict : bool, optional
        Whether to return results as a dict mapping dataset_id to metadata. If False,
        returns a list of (dataset_id, metadata) tuples, by default True.
    concat_list_keys: Optional[Iterable[str]]
        Forwarded to assemble_metadata_dict (see there for semantics).

    Returns
    -------
    Union[dict[str, dict], list[tuple[str, dict]]]
        Assembled OEMetadata for each dataset.
    """
    base = Path(base_dir)

    if dataset_ids is None:
        ids = discover_dataset_ids_from_index(index_file) if index_file else discover_dataset_ids(base)
    else:
        ids = list(dataset_ids)

    results_pairs: list[tuple[str, dict]] = []
    for ds_id in ids:
        md = assemble_metadata_dict(
            base,
            ds_id,
            index_file=index_file,
            concat_list_keys=concat_list_keys,
        )
        results_pairs.append((ds_id, md))

    if as_dict:
        return dict(results_pairs)
    return results_pairs
