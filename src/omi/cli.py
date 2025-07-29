"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?

  You might be tempted to import things from __main__ later, but that will cause
  problems: the code will get executed twice:

  - When you run `python -m omi` python will execute
    ``__main__.py`` as a script. That means there won't be any
    ``omi.__main__`` in ``sys.modules``.
  - When you import __main__ it will get executed again (as a module) because
    there's no ``omi.__main__`` in ``sys.modules``.

  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""

import json
from pathlib import Path
from typing import Union

import click

from omi.creation.creator import OEMetadataCreator
from omi.creation.utils import load_yaml_metadata


@click.group()
def grp() -> None:
    """Init click group."""


cli = click.CommandCollection(sources=[grp])


def main() -> None:
    """Start click application."""
    cli()


@click.command()
@click.argument("yaml_file")
@click.argument("output_file")
def from_yaml(yaml_file: Union[str, Path], output_file: Union[str, Path]) -> None:
    """
    Generate OEMetadata from a YAML file and write it to an output file.

    Parameters
    ----------
    yaml_file: Union[str, Path]
        Path to the input YAML file containing dataset and resources.
    output_file: Union[str, Path]
        Path to the output file where the generated OEMetadata JSON will be saved.
    """
    version, dataset, resources = load_yaml_metadata(yaml_file)
    generator = OEMetadataCreator()
    metadata = generator.generate_metadata(dataset, resources)

    with Path(output_file).open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"OEMetadata written to {output_file}")  # noqa: T201
