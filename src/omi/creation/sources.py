# omi/creation/sources.py
"""
Attach provenance sources to OEMetadata resources.

Two kinds of source are supported, both living in the OEMetadata v2 ``sources``
slot on a resource:

- *external* sources -- literature, databases or portals outside the dataset
  (e.g. MaStR, OSM, a Destatis publication). Recorded with descriptive fields
  a human fills in.
- *internal* cross-references -- another table produced within the same
  project whose own metadata carries the full provenance. Recorded as a
  lightweight ``sources`` entry so the consuming resource declares where its
  input came from without duplicating that table's metadata.

Both constructors return plain, spec-shaped ``dict`` source entries;
:func:`add_source_to_resource` appends them without creating duplicates. The
functions are project-agnostic -- callers decide which tables are internal vs.
external.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Optional, Union

from .utils import dump_yaml, load_yaml

Json = dict[str, object]

# keys that decide whether two source entries describe the same thing
_SOURCE_DEDUPE_KEYS: tuple[str, ...] = ("title", "path")


def build_external_source(  # noqa: PLR0913
    title: str,
    *,
    description: str = "",
    path: str = "",
    authors: Optional[list[str]] = None,
    publication_year: Optional[int] = None,
    licenses: Optional[list[Json]] = None,
) -> Json:
    """
    Build an external-source entry for a resource's ``sources`` list.

    Only ``title`` is required; the remaining descriptive fields default to
    empty stubs for a human to complete later.
    """
    return {
        "title": title,
        "description": description,
        "path": path,
        "authors": list(authors) if authors else [],
        "publicationYear": publication_year,
        "sourceLicenses": list(licenses) if licenses else [],
    }


def build_internal_source(
    table: str,
    *,
    title: Optional[str] = None,
    description: str = "",
    path: str = "",
) -> Json:
    """
    Build an internal cross-reference entry pointing at another table.

    ``table`` is the referenced resource name (e.g. ``"grid.egon_etrago_bus"``).
    The full provenance lives in that table's own metadata; this entry only
    records the dependency. ``path`` may point at the referenced metadata (an
    ``@id`` / URL) once known.

    The result uses only spec ``sources`` keys so it stays valid against the
    OEMetadata schema; the internal nature is conveyed by the content.
    """
    ref_title = title or f"Internal table: {table}"
    ref_desc = description or (
        f"Derived from the internal table '{table}'. See that table's own metadata for full provenance."
    )
    return {
        "title": ref_title,
        "description": ref_desc,
        "path": path,
        "authors": [],
        "publicationYear": None,
        "sourceLicenses": [],
    }


def add_source_to_resource(
    resource: Json,
    source: Json,
    *,
    dedupe_keys: tuple[str, ...] = _SOURCE_DEDUPE_KEYS,
) -> tuple[Json, bool]:
    """
    Return a copy of ``resource`` with ``source`` appended to its ``sources``.

    An equivalent source (matching on ``dedupe_keys``, default title + path)
    is not added twice. The input ``resource`` is never mutated in place.

    Returns
    -------
    (resource, added)
        The updated resource copy and whether a new source was appended.
    """
    result = deepcopy(resource)
    existing = result.get("sources")
    existing = list(existing) if isinstance(existing, list) else []

    def sig(s: object) -> tuple:
        if not isinstance(s, dict):
            return (repr(s),)
        return tuple(s.get(k) for k in dedupe_keys)

    target = sig(source)
    if any(sig(s) == target for s in existing):
        result["sources"] = existing
        return result, False

    existing.append(deepcopy(source))
    result["sources"] = existing
    return result, True


def add_source_to_resource_file(
    resource_path: Union[str, Path],
    source: Json,
    *,
    dedupe_keys: tuple[str, ...] = _SOURCE_DEDUPE_KEYS,
) -> bool:
    """
    Load a resource YAML, add ``source`` non-destructively, and write it back.

    Returns True if a new source was written, False if an equivalent one was
    already present (file left untouched in that case).
    """
    path = Path(resource_path)
    resource = load_yaml(path)
    updated, added = add_source_to_resource(resource, source, dedupe_keys=dedupe_keys)
    if added:
        dump_yaml(path, updated)
    return added
