"""
Generate an OEMetadata configuration file.

Module for generating metadata files from resources like directories or zip files.
This used to get started from scratch - init metadata.
"""

import fnmatch
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Union

import yaml

from omi.inspection import DEFAULT_DELIMITER, infer_metadata


@dataclass
class FileFilterOptions:
    """
    Options for filtering files when reading directories or zip files.

    Attributes
    ----------
    exclude_extensions: list[str] | None
        List of file extensions to exclude (e.g., ['.log', '.tmp']).
    exclude_patterns: list[str] | None
        List of filename patterns to exclude (e.g., ['*_backup.*', '*.bak']).
    exclude_hidden: bool
    Whether to exclude hidden files/directories (default True).
    """

    exclude_extensions: list[str] | None = None
    exclude_patterns: list[str] | None = None
    exclude_hidden: bool = True


def read_directory(
    directory: Union[str, Path],
    filter_opts: FileFilterOptions,
) -> list[Path]:
    """
    Recursively read files from the directory, applying optional filters.

    Parameters
    ----------
    directory: Union[str, Path]
        The directory to read files from. Can be a string or a Path object.
    filter_opts: FileFilterOptions
        Filtering options including extensions, patterns, and hidden files.

    Returns
    -------
    list[Path]
        A list of Path objects representing the files that match the criteria.
    """
    directory = Path(directory)

    exclude_extensions = set(filter_opts.exclude_extensions or [".log", ".tmp", ".bak", ".DS_Store", ".md"])
    exclude_patterns = filter_opts.exclude_patterns or ["*_backup.*", "*~", "*.old", "*.ignore"]

    valid_files = []
    for file_path in directory.rglob("*"):
        if not file_path.is_file():
            continue

        if filter_opts.exclude_hidden and any(part.startswith(".") for part in file_path.parts):
            continue

        if file_path.suffix in exclude_extensions:
            continue

        if any(fnmatch.fnmatch(file_path.name, pattern) for pattern in exclude_patterns):
            continue

        valid_files.append(file_path)

    return valid_files


def read_zipfile(
    zip_path: Union[str, Path],
    extract_to: Union[str, Path],
    filter_opts: FileFilterOptions,
) -> list[Path]:
    """Extract a zip file and return list of extracted files."""
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)
    return read_directory(extract_to, filter_opts)


def infer_file_metadata(file_path: Path) -> dict:
    """
    Infer basic resource metadata from file name and type.

    Parameters
    ----------
    file_path: Path
        Path to the file for which metadata should be inferred.

    Returns
    -------
    dict
        A dictionary containing inferred metadata for the resource.
    """
    file_name = file_path.stem
    file_format = file_path.suffix.replace(".", "").upper()

    resource = {
        "name": file_name.lower().replace(" ", "_"),
        "title": file_name.replace("_", " ").title(),
        "path": file_path.as_posix(),
        "description": f"Auto-generated description for {file_name}",
        "type": "table" if file_format in ["CSV", "XLSX", "JSON"] else "file",
        "format": file_format,
        "encoding": "UTF-8",
    }

    if file_format == "CSV":
        with file_path.open("r") as f:
            inferred = infer_metadata(f, "OEP")["resources"][0]

        resource["schema"] = inferred["schema"]
        # The delimiter is part of the inferred dialect; it used to be read off
        # the schema dict, which never carries one and always yielded ",".
        resource["dialect"] = inferred.get("dialect") or {
            "delimiter": DEFAULT_DELIMITER,
            "decimalSeparator": ".",
        }

    return resource


def generate_oemetadata_yaml_from_datapackage(
    directory: Union[str, Path],
    output_yaml: Union[str, Path],
    dataset_metadata: dict,
    filter_opts: FileFilterOptions,
) -> None:
    """
    Generate an OEMetadata YAML configuration file based on files in a directory or zipped directory.

    Parameters
    ----------
    directory: Union[str, Path]
        Path to the directory or zip file containing data files.
    output_yaml: Union[str, Path]
        Path to the output YAML file.
    dataset_metadata: dict
        Metadata for the dataset, including name, title, description, and ID.
    filter_opts: FileFilterOptions
        Filtering options for excluding files by extension, pattern, or hidden state.
    """
    temp_dir = None
    directory = Path(directory)
    if zipfile.is_zipfile(directory):
        temp_dir = Path("temp_extracted")
        files = read_zipfile(directory, temp_dir, filter_opts)
        files = read_directory(temp_dir, filter_opts)  # Apply filtering after extraction
    else:
        files = read_directory(directory, filter_opts)

    resources = []
    for file in files:
        resource_meta = infer_file_metadata(file)

        resources.append(resource_meta)

    yaml_structure = {
        "dataset": dataset_metadata,
        "template": {  # TODO @jh-RLI: This section must be defined by user # noqa: TD003
            "context": {
                "title": "Your Project Title",
                "homepage": "https://yourhomepage.org",
                "contact": "contact@yourproject.org",
            },
        },
        "resources": resources,
    }

    with open(output_yaml, "w", encoding="utf-8") as yaml_file:  # noqa: PTH123
        yaml.dump(yaml_structure, yaml_file, sort_keys=False, allow_unicode=True)

    if temp_dir:
        import shutil

        shutil.rmtree(temp_dir)

    print(f"YAML configuration generated at: {output_yaml}")  # noqa: T201


# Example usage
if __name__ == "__main__":
    dataset_metadata_example = {
        "name": "example_dataset",
        "title": "Example Dataset",
        "description": "This dataset was autogenerated from directory content.",
        "@id": "https://example.org/dataset/example_dataset",
    }

    generate_oemetadata_yaml_from_datapackage(
        directory="/home/jh/projekte/SLE/postprocessed/",
        output_yaml="generated_metadata.yaml",
        dataset_metadata=dataset_metadata_example,
        filter_opts=FileFilterOptions(
            exclude_patterns=[".snake*"],
            exclude_hidden=True,
        ),
    )
