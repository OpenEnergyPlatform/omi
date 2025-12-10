"""Helpers for importing and pushing OEMetadata to the Open Energy Platform (OEP)."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Union

from omi.base import (
    MetadataError,
    get_metadata_from_oep_table,
    get_metadata_version,
    update_metadata_for_oep_table,
)
from omi.creation.init import (
    add_resource_from_oem_metadata,
    init_dataset,
)

if TYPE_CHECKING:
    from collections.abc import Iterable


def import_oep_table_as_resource(
    base_dir: Union[str, Path],
    dataset_id: str,
    oep_table: str,
    *,
    create_dataset_if_missing: bool = True,
    overwrite_resource: bool = False,
) -> Path:
    """
    Import the OEMetadata of an OEP table and attach it as a resource to a local OMI dataset.

    Behavior
    --------
    - Fetches metadata from the OEP (GET /api/v0/tables/{table}/meta/).
    - Ignores the top-level dataset in the returned JSON.
    - Converts exactly one resource from ``resources[0]`` into a
      ``resources/<dataset_id>/<resource>.resource.yaml`` file.
    - If ``datasets/<dataset_id>.dataset.yaml`` does not exist and
      ``create_dataset_if_missing=True``, a new dataset skeleton is created
      from the OEMetadata specification (with ``name=dataset_id``, etc.).

    Parameters
    ----------
    base_dir :
        Base directory for the split-files layout.
    dataset_id :
        Local dataset name in OMI (e.g. "pv_openfield145").
    oep_table :
        Table name on the OEP (e.g. "parameter_photovoltaik_openfield145").
    create_dataset_if_missing :
        Whether to create a dataset skeleton if it does not yet exist.
    overwrite_resource :
        Whether to overwrite an existing resource YAML with the same name.

    Returns
    -------
    Path
        Path to the created resource YAML file.
    """
    base_dir = Path(base_dir)
    dataset_yaml = base_dir / "datasets" / f"{dataset_id}.dataset.yaml"

    # 1) Fetch OEMetadata from OEP (raises MetadataError if empty)
    oem = get_metadata_from_oep_table(oep_table)

    # 2) Read OEMetadata version from metaMetadata (e.g. OEMetadata-2.0.4 -> OEMetadata-2.0)
    try:
        oem_version = get_metadata_version(oem)
    except MetadataError:
        oem_version = "OEMetadata-2.0"

    # 3) Create dataset skeleton if requested and not yet present
    if not dataset_yaml.exists() and create_dataset_if_missing:
        init_dataset(
            base_dir=base_dir,
            dataset_id=dataset_id,
            oem_version=oem_version,
            resources=(),
            overwrite=False,
        )
        # Important: we do NOT call _update_dataset_yaml_from_top_level()
        # so the OEP top-level dataset fields remain ignored.

    # 4) Derive a resource from the OEMetadata and store it as .resource.yaml
    res_path = add_resource_from_oem_metadata(
        base_dir=base_dir,
        dataset_id=dataset_id,
        oem=oem,
        resource_index=0,
        resource_name=None,  # or explicitly e.g. oep_table
        overwrite=overwrite_resource,
        fill_missing_from_template=True,
    )

    print(  # noqa: T201
        f"Imported OEP table '{oep_table}' as resource into dataset '{dataset_id}': {res_path}",
    )
    return res_path


def _metadata_for_single_resource(metadata: dict, resource_index: int) -> dict:
    """
    Return a new OEMetadata dict that contains exactly one resource (resources[resource_index]).

    but keeps all top-level dataset attributes.

    Parameters
    ----------
    metadata :
        Full OEMetadata mapping (dataset + multiple resources).
    resource_index :
        Index into ``metadata["resources"]``.

    Returns
    -------
    dict
        A new OEMetadata mapping with all top-level keys preserved and
        exactly one entry in ``resources``.

    Raises
    ------
    MetadataError
        If no valid 'resources' list is present.
    IndexError
        If the resource_index is out of range.
    """
    resources = metadata.get("resources")
    if not isinstance(resources, list) or not resources:
        msg = "Metadata must contain a non-empty 'resources' list."
        raise MetadataError(msg)

    if resource_index < 0 or resource_index >= len(resources):
        raise IndexError(
            f"Resource index {resource_index} out of range for metadata.resources (len={len(resources)}).",
        )

    # Copy all top-level keys except 'resources'
    base: dict[str, Any] = {k: deepcopy(v) for k, v in metadata.items() if k != "resources"}

    # Attach only the selected resource
    base["resources"] = [deepcopy(resources[resource_index])]
    return base


def update_oep_tables_from_dataset_metadata(
    metadata: dict,
    *,
    token: str,
    method: str = "POST",
    timeout: int = 90,
    only_tables: Optional[Iterable[str]] = None,
) -> dict[str, dict]:
    """
    Update OEP table metadata for all resources in a dataset-level OEMetadata dict.

    For each resource in ``metadata["resources"]``:

    - A per-table OEMetadata dict is constructed that:
        * keeps all dataset-level (top-level) attributes, and
        * contains only that single resource in ``resources``.
    - The OEP table name is taken from ``resource["name"]``.
    - The per-table metadata is sent to the OEP meta API using the
      ``update_metadata_for_oep_table`` helper.

    Parameters
    ----------
    metadata :
        Full OEMetadata mapping (dataset attributes + multiple resources).
    token :
        OEP user API token for authentication (raw token string; the
        ``Authorization: Token <token>`` header is constructed internally).
    method :
        HTTP method to use for the OEP meta API ("POST" or "PUT").
    timeout :
        Request timeout in seconds.
    only_tables :
        Optional iterable of table names to restrict updates to. If provided,
        only resources whose ``name`` is in this set are updated.

    Returns
    -------
    Dict[str, dict]
        Mapping from OEP table name to the parsed JSON response returned
        by the OEP meta API for that table.

    Raises
    ------
    MetadataError
        If 'resources' is missing/invalid, or if a resource lacks a name.
    """
    resources = metadata.get("resources")
    if not isinstance(resources, list) or not resources:
        msg = "Metadata must contain a non-empty 'resources' list."
        raise MetadataError(msg)

    restrict = set(only_tables) if only_tables is not None else None
    results: dict[str, dict] = {}

    for idx, res in enumerate(resources):
        if not isinstance(res, dict):
            raise MetadataError(f"Resource at index {idx} is not a mapping.")

        table_name = (res.get("name") or "").strip()
        if not table_name:
            raise MetadataError(f"Resource at index {idx} is missing a 'name' field.")

        if restrict is not None and table_name not in restrict:
            continue  # skip this resource if it's not in the filter

        per_table_md = _metadata_for_single_resource(metadata, idx)

        resp = update_metadata_for_oep_table(
            oep_table=table_name,
            metadata=per_table_md,
            token=token,
            method=method,
            timeout=timeout,
        )
        results[table_name] = resp

    return results


def update_single_oep_table_from_dataset_metadata(
    metadata: dict,
    oep_table: str,
    *,
    token: str,
    method: str = "POST",
    timeout: int = 90,
) -> dict:
    """
    Update the metadata for a single OEP table from a dataset-level OEMetadata dict.

    The table name is matched against the ``name`` field of the resources in
    ``metadata["resources"]``. The payload sent to the OEP meta API contains:

    - all dataset-level attributes from ``metadata``, and
    - exactly one resource (the one whose name matches ``oep_table``).

    Parameters
    ----------
    metadata :
        Full OEMetadata mapping (dataset + multiple resources).
    oep_table :
        Name of the OEP table to update (matched against resource.name).
    token :
        OEP user API token for authentication (raw token string; the
        ``Authorization: Token <token>`` header is constructed internally).
    method :
        HTTP method to use for the OEP meta API ("POST" or "PUT").
    timeout :
        Request timeout in seconds.

    Returns
    -------
    dict
        Parsed JSON response from the OEP meta API.

    Raises
    ------
    MetadataError
        If no resource with the given name is found, or 'resources' is invalid.
    """
    resources = metadata.get("resources")
    if not isinstance(resources, list) or not resources:
        msg = "Metadata must contain a non-empty 'resources' list."
        raise MetadataError(msg)

    target_index: Optional[int] = None
    for idx, res in enumerate(resources):
        if not isinstance(res, dict):
            continue
        name = (res.get("name") or "").strip()
        if name == oep_table:
            target_index = idx
            break

    if target_index is None:
        raise MetadataError(
            f"No resource with name '{oep_table}' found in metadata.resources.",
        )

    per_table_md = _metadata_for_single_resource(metadata, target_index)
    return update_metadata_for_oep_table(
        oep_table=oep_table,
        metadata=per_table_md,
        token=token,
        method=method,
        timeout=timeout,
    )
