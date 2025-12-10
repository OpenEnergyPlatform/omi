"""
Command line interface for OMI.

This CLI only supports the split-files layout:
- datasets/<dataset_id>.dataset.yaml
- datasets/<dataset_id>.template.yaml  (optional)
- resources/<dataset_id>/*.resource.yaml
(optionally wired via metadata_index.yaml)

Usage:
omi assemble \
  --base-dir ./metadata \
  --dataset-id powerplants \
  --output-file ./out/powerplants.json \
  --index-file ./metadata/metadata_index.yaml   # optional

"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import click

from omi.api.oep import (
    import_oep_table_as_resource,
    update_oep_tables_from_dataset_metadata,
    update_single_oep_table_from_dataset_metadata,
)
from omi.creation.assembler import assemble_metadata_dict
from omi.creation.creator import OEMetadataCreator
from omi.creation.init import (
    init_dataset,
    init_from_oem_json,
    init_resources_from_files,
)
from omi.creation.utils import (
    DEFAULT_CONCAT_LIST_KEYS,
    apply_template_to_resources,
    load_parts,
)


@click.group()
def grp() -> None:
    """OMI CLI."""


@grp.command("assemble")
@click.option(
    "--base-dir",
    required=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="Root directory containing 'datasets/' and 'resources/'.",
)
@click.option("--dataset-id", required=True, help="Logical dataset id (e.g. 'powerplants').")
@click.option(
    "--output-file",
    required=True,
    type=click.Path(dir_okay=False, path_type=Path),
    help="Path to write the generated OEMetadata JSON.",
)
@click.option(
    "--index-file",
    default=None,
    type=click.Path(dir_okay=False, path_type=Path),
    help="Optional metadata index YAML for explicit mapping.",
)
@click.option(
    "--concat-list-key",
    "concat_list_keys",
    multiple=True,
    help=(
        "List-valued keys to concatenate (template+resource) instead of overriding. "
        "Defaults to: keywords, topics, languages."
    ),
)
def assemble_cmd(
    base_dir: Path,
    dataset_id: str,
    output_file: Path,
    index_file: Optional[Path],
    concat_list_keys: tuple[str, ...],
) -> None:
    """Assemble OEMetadata from split YAML files and write JSON to OUTPUT_FILE."""
    # Load pieces
    version, dataset, resources, template = load_parts(base_dir, dataset_id, index_file=index_file)

    # Choose which list keys should be concatenated
    keys = set(concat_list_keys) if concat_list_keys else DEFAULT_CONCAT_LIST_KEYS

    merged_resources = apply_template_to_resources(
        resources,
        template,
        concat_list_keys=keys,
    )

    # Build & save with the correct spec version
    creator = OEMetadataCreator(oem_version=version)
    creator.save(dataset, merged_resources, output_file, ensure_ascii=False, indent=2)


@grp.command("push-oep-all")
@click.option(
    "--base-dir",
    required=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="Root directory containing 'datasets/' and 'resources/'.",
)
@click.option(
    "--dataset-id",
    required=True,
    help="Logical dataset id (e.g. 'pv_bundle').",
)
@click.option(
    "--token",
    required=True,
    help=(
        "OEP user API token (raw token string). The 'Authorization: Token <token>' header is constructed internally."
    ),
)
@click.option(
    "--method",
    default="POST",
    show_default=True,
    type=click.Choice(["POST", "PUT"], case_sensitive=False),
    help="HTTP method to use for the OEP meta API.",
)
@click.option(
    "--timeout",
    default=90,
    show_default=True,
    type=int,
    help="Request timeout in seconds.",
)
@click.option(
    "--only-table",
    "only_tables",
    multiple=True,
    help=(
        "Restrict updates to specific table names (can be given multiple times). "
        "If omitted, all resources in the dataset are used."
    ),
)
@click.option(
    "--index-file",
    default=None,
    type=click.Path(dir_okay=False, path_type=Path),
    help=("Optional metadata index YAML for resolving dataset parts, same semantics as in the 'assemble' command."),
)
def push_oep_all_cmd(  # noqa: PLR0913
    base_dir: Path,
    dataset_id: str,
    token: str,
    method: str,
    timeout: int,
    only_tables: tuple[str, ...],
    index_file: Optional[Path],
) -> None:
    """Push OEMetadata for all (or selected) tables of a dataset to the OEP."""
    # 1) Assemble full dataset OEMetadata from split YAML
    md = assemble_metadata_dict(
        base_dir=base_dir,
        dataset_id=dataset_id,
        index_file=index_file,
    )

    # 2) Bundle optional call arguments to keep PLR0913 happy
    call_opts: dict[str, object] = {
        "method": method.upper(),
        "timeout": timeout,
    }
    if only_tables:
        call_opts["only_tables"] = only_tables

    # 3) Push per-table metadata to OEP
    results = update_oep_tables_from_dataset_metadata(
        metadata=md,
        token=token,
        **call_opts,
    )

    # 4) Print a short summary
    if not results:
        click.echo("No tables were updated (no matching resources or filter excluded all).")
    else:
        click.echo("Updated metadata for the following OEP tables:")
        for table_name in sorted(results.keys()):
            click.echo(f"  - {table_name}")


@grp.command("push-oep")
@click.option(
    "--base-dir",
    required=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="Root directory containing 'datasets/' and 'resources/'.",
)
@click.option(
    "--dataset-id",
    required=True,
    help="Logical dataset id (e.g. 'pv_bundle').",
)
@click.option(
    "--table",
    "oep_table",
    required=True,
    help="Name of the OEP table to update (must match resource.name in the metadata).",
)
@click.option(
    "--token",
    required=True,
    help=(
        "OEP user API token (raw token string). The 'Authorization: Token <token>' header is constructed internally."
    ),
)
@click.option(
    "--method",
    default="POST",
    show_default=True,
    type=click.Choice(["POST", "PUT"], case_sensitive=False),
    help="HTTP method to use for the OEP meta API.",
)
@click.option(
    "--timeout",
    default=90,
    show_default=True,
    type=int,
    help="Request timeout in seconds.",
)
@click.option(
    "--index-file",
    default=None,
    type=click.Path(dir_okay=False, path_type=Path),
    help="Optional metadata index YAML for resolving dataset parts.",
)
def push_oep_one_cmd(  # noqa: PLR0913
    base_dir: Path,
    dataset_id: str,
    oep_table: str,
    token: str,
    method: str,
    timeout: int,
    index_file: Optional[Path],
) -> None:
    """Push OEMetadata for a single OEP table, based on a dataset-level OEMetadata dict."""
    # 1) Assemble full dataset OEMetadata from split YAML
    md = assemble_metadata_dict(
        base_dir=base_dir,
        dataset_id=dataset_id,
        index_file=index_file,
    )

    # 2) Bundle options to avoid PLR0913 on the call
    call_opts: dict[str, object] = {
        "method": method.upper(),
        "timeout": timeout,
    }

    # 3) Push just this one table's metadata
    update_single_oep_table_from_dataset_metadata(
        metadata=md,
        oep_table=oep_table,
        token=token,
        **call_opts,
    )

    click.echo(f"Updated metadata for {oep_table}")


@click.group()
def init() -> None:
    """Scaffold OEMetadata split-files layout."""


@init.command("dataset")
@click.argument("base_dir", type=click.Path(file_okay=False, path_type=Path))
@click.argument("dataset_id")
@click.option("--oem-version", default="OEMetadata-2.0", show_default=True)
@click.option("--resource", "resources", multiple=True, help="Initial resource names (repeatable).")
@click.option("--overwrite", is_flag=True, help="Overwrite existing files.")
def init_dataset_cmd(
    base_dir: Path,
    dataset_id: str,
    oem_version: str,
    resources: tuple[str, ...],
    *,
    overwrite: bool,
) -> None:
    """Initialize a split-files OEMetadata dataset layout under BASE_DIR."""
    res = init_dataset(base_dir, dataset_id, oem_version=oem_version, resources=resources, overwrite=overwrite)
    click.echo(f"dataset:  {res.dataset_yaml}")
    click.echo(f"template: {res.template_yaml}")
    for p in res.resource_yamls:
        click.echo(f"resource: {p}")


@init.command("resources")
@click.argument("base_dir", type=click.Path(file_okay=False, path_type=Path))
@click.argument("dataset_id")
@click.argument("files", nargs=-1, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--oem-version", default="OEMetadata-2.0", show_default=True)
@click.option("--overwrite", is_flag=True, help="Overwrite existing files.")
def init_resources_cmd(
    base_dir: Path,
    dataset_id: str,
    files: tuple[Path, ...],
    oem_version: str,
    *,
    overwrite: bool,
) -> None:
    """Create resource YAML files for DATASET_ID from the given FILES."""
    outs = init_resources_from_files(base_dir, dataset_id, files, oem_version=oem_version, overwrite=overwrite)
    for p in outs:
        click.echo(p)


@init.command("from-json")
@click.argument("base_dir", type=click.Path(file_okay=False, path_type=Path))
@click.argument("dataset_id")
@click.argument("oem_json", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--oem-version", default="OEMetadata-2.0", show_default=True)
@click.option(
    "--collect-common",
    is_flag=True,
    help=(
        "Collect fields that are identical across all resources "
        "into the dataset template (e.g. context/spatial/temporal)."
    ),
)
def init_from_json_cmd(
    base_dir: Path,
    dataset_id: str,
    oem_json: Path,
    oem_version: str,
    *,
    collect_common: bool,
) -> None:
    """
    Initialize split-files layout from an existing OEMetadata JSON file.

    BASE_DIR:   Root directory containing 'datasets/' and 'resources/'.
    DATASET_ID: Logical dataset id (e.g. 'sle').
    OEM_JSON:   Path to an OEMetadata JSON file with one or more resources.
    """
    res = init_from_oem_json(
        base_dir=base_dir,
        dataset_id=dataset_id,
        oem_json_path=oem_json,
        oem_version=oem_version,
        collect_common=collect_common,
    )

    click.echo(f"dataset:  {res.dataset_yaml}")
    click.echo(f"template: {res.template_yaml}")
    for p in res.resource_yamls:
        click.echo(f"resource: {p}")


@init.command("oep-resource")
@click.argument("base_dir", type=click.Path(file_okay=False, path_type=Path))
@click.argument("dataset_id")
@click.argument("oep_table")
@click.option(
    "--no-create-dataset",
    is_flag=True,
    help=(
        "Do not create a dataset skeleton if it is missing. "
        "If set and the dataset does not exist, the command will fail."
    ),
)
@click.option(
    "--overwrite-resource",
    is_flag=True,
    help="Overwrite an existing resource YAML with the same name.",
)
def init_oep_resource_cmd(
    base_dir: Path,
    dataset_id: str,
    oep_table: str,
    no_create_dataset: bool,  # noqa: FBT001
    overwrite_resource: bool,  # noqa: FBT001
) -> None:
    """
    Import an OEP table's OEMetadata and add it as a resource to a local dataset.

    BASE_DIR:    Root directory containing 'datasets/' and 'resources/'.
    DATASET_ID:  Local dataset id in the split-files layout.
    OEP_TABLE:   Name of the table on the Open Energy Platform.

    Notes
    -----
    - Fetches OEMetadata from the OEP meta API for the given table.
    - Ignores the top-level dataset fields in the OEP JSON (id, name, title, @id,
      @context, description, ...).
    - Converts only the first entry in ``resources`` into a
      ``resources/<dataset_id>/<name>.resource.yaml`` file.
    """
    create_dataset_if_missing = not no_create_dataset

    res_path = import_oep_table_as_resource(
        base_dir=base_dir,
        dataset_id=dataset_id,
        oep_table=oep_table,
        create_dataset_if_missing=create_dataset_if_missing,
        overwrite_resource=overwrite_resource,
    )
    click.echo(f"resource: {res_path}")


# Keep CommandCollection for backwards compatibility with your entry point
cli = click.CommandCollection(sources=[grp, init])


def main() -> None:
    """Start click application."""
    cli()
