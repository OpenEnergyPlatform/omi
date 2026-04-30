"""Create OEMetadata JSON datapackage structure and return or store it."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from omi.base import get_metadata_specification
from omi.creation.cleaner import (
    detect_unknown_keys,
    normalize_metadata_for_schema,
    strip_unknown_keys,
)
from omi.validation import validate_metadata


class OEMetadataCreator:
    """
    Create OEMetadata JSON datapackages.

    Output is based on dataset and resource descriptions and validated against
    the official schema.
    """

    def __init__(self, oem_version: str = "OEMetadata-2.0") -> None:
        """Initialize the creator with a specific OEMetadata version."""
        self.oem_spec = get_metadata_specification(oem_version)

    def generate_metadata(self, dataset: dict, resources: list[dict]) -> dict:
        """Generate OEMetadata JSON datapackage from dataset and resources."""
        metadata = {
            "@context": self.oem_spec.schema["properties"]["@context"]["examples"][0],
            **dataset,
            "resources": resources,
            # metaMetadata is *always* taken from the spec example,
            # so users don't have to provide it.
            "metaMetadata": self.oem_spec.example["metaMetadata"],
        }

        # Normalize for schema (incl. bounding boxes) before validation
        metadata = normalize_metadata_for_schema(metadata, keep_empty=True)

        validate_metadata(metadata, check_license=False)
        return metadata

    def save(
        self,
        dataset: dict,
        resources: list[dict],
        output_file: Path | str,
        **dump_kwargs,
    ) -> None:
        """
        Generate OEMetadata and save it to a JSON file.

        Parameters
        ----------
        dataset : dict
            Dataset metadata.
        resources : list[dict]
            List of resource metadata entries.
        output_file : Path | str
            Path to the output JSON file.
        **dump_kwargs :
            Extra kwargs forwarded to `json.dump`. Defaults applied here:
            - indent: 2
            - ensure_ascii: False
        """
        metadata = self.generate_metadata(dataset, resources)

        # Defaults, can be overridden by caller via **dump_kwargs
        indent = dump_kwargs.pop("indent", 2)
        ensure_ascii = dump_kwargs.pop("ensure_ascii", False)

        with Path(output_file).open("w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=indent, ensure_ascii=ensure_ascii, **dump_kwargs)

        print(f"OEMetadata written to {output_file}")  # noqa: T201

    def save_metadata(  # noqa: PLR0913
        self,
        metadata: dict,
        output_file: Path | str,
        *,
        validate: bool = False,
        check_license: bool = False,
        ensure_ascii: bool = False,
        indent: int = 2,
        strip_before_validate: bool = False,
        fail_on_unknown: bool = False,
    ) -> None:
        """
        Save a pre-built OEMetadata dict to disk with optional cleaning and validation.

        This variant is meant for the *augmented* metadata you produce after assembly
        and potential builder/overlay mutations.

        Parameters
        ----------
        metadata
            OEMetadata dict to write.
        output_file
            Destination JSON path.
        validate
            If True, validate using `omi.validation.validate_metadata`.
        check_license
            Forwarded to validator; if True, also checks license map compliance.
        ensure_ascii
            If True, JSON-escape non-ASCII characters; default: False (UTF-8).
        indent
            JSON indentation; default: 2.
        strip_before_validate
            If True, drop all keys not allowed by the spec (best-effort) before
            validation and writing.
        fail_on_unknown
            If True, raise with a list of JSON-Pointer-like paths if unknown keys
            are present (checked *before* stripping).

        Raises
        ------
        ValueError
            If `fail_on_unknown` is True and unknown keys are detected.

        Notes
        -----
        - Cleaning relies on the schema from `self.oem_spec.schema`.
        - If you want silent cleanup, set `strip_before_validate=True`.
        - If you prefer fail-fast CI behavior, set `fail_on_unknown=True`.
        """
        md = deepcopy(metadata)
        schema = self.oem_spec.schema

        if fail_on_unknown:
            unknown = detect_unknown_keys(md, oem_schema=schema)
            if unknown:
                raise ValueError(
                    "Metadata contains keys not allowed by the OEMetadata schema:\n"
                    + "\n".join(f"  - {p}" for p in unknown),
                )

        if strip_before_validate:
            md = strip_unknown_keys(md, oem_schema=schema)

        if validate:
            from omi.validation import validate_metadata as _validate

            _validate(md, check_license=check_license)

        p = Path(output_file)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(md, indent=indent, ensure_ascii=ensure_ascii), encoding="utf-8")
