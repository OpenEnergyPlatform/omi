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


# Keep CommandCollection for backwards compatibility with your entry point
cli = click.CommandCollection(sources=[grp, init])


def main() -> None:
    """Start click application."""
    cli()
