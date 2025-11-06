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
from omi.creation.utils import apply_template_to_resources, load_parts


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
def assemble_cmd(base_dir: Path, dataset_id: str, output_file: Path, index_file: Optional[Path]) -> None:
    """Assemble OEMetadata from split YAML files and write JSON to OUTPUT_FILE."""
    # Load pieces
    version, dataset, resources, template = load_parts(base_dir, dataset_id, index_file=index_file)
    merged_resources = apply_template_to_resources(resources, template)

    # Build & save with the correct spec version
    creator = OEMetadataCreator(oem_version=version)
    creator.save(dataset, merged_resources, output_file, ensure_ascii=False, indent=2)

    click.echo(f"OEMetadata written to {output_file}")


# Keep CommandCollection for backwards compatibility with your entry point
cli = click.CommandCollection(sources=[grp])


def main() -> None:
    """Start click application."""
    cli()
