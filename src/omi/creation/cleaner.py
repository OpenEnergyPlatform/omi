"""
Minimal schema hygiene helpers for OEMetadata.

This module focuses on two practical tasks:

1. Empty-value handling
   - Optionally drop keys whose values are "empty" (None, "", [], {}).
   - This can be used at the end of a pipeline to create a compact
     metadata product, depending on user choice.

   Behavior:
     * keep_empty=True  -> keep all empty fields.
     * keep_empty=False -> remove empty fields and fully-empty objects,
                           except for a small set of schema-required
                           keys that must exist even when empty.

2. Bounding box normalization
   - Ensure each resource's ``spatial.extent.boundingBox`` exists and has
     exactly four numeric values (padding with zeros if needed).
   - This prevents JSON Schema validation failures due to wrong shape.

Additionally, for better editing UX, "short" objects appended later
(e.g. contributors with only a few keys) can be normalized to have the
same key set as their siblings when keep_empty=True.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

Json = dict[str, Any]

_EMPTY_SENTINELS = (None, "", [], {})

#: Keys that must never be pruned even if their value is "empty".
#: This keeps schema-required properties (e.g. primaryKey: []) intact.
_PROTECTED_EMPTY_KEYS = {
    "primaryKey",
    # You can add more here if validation errors show up for other fields.
}

# Magic-number replacements / small schema constants
_FIELD_PATH_MIN_LEN = 3
_BBOX_COORDINATE_COUNT = 4


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _is_protected_path(path: str, key: str) -> bool:
    """
    Return True if this key at this path must not be pruned, even if empty.

    Rules derived from the OEMetadata JSON Schema:
      - schema.fields[*].name and .type are required
      - schema.primaryKey is required (handled via _PROTECTED_EMPTY_KEYS)
    """
    # Global protected keys (e.g. schema.primaryKey)
    if key in _PROTECTED_EMPTY_KEYS:
        return True

    # Split path and drop empty segments
    segs = [s for s in path.split("/") if s]

    # Protect only the *field object* name/type:
    #   resources/.../schema/fields/<index>/name
    #   resources/.../schema/fields/<index>/type
    # and NOT nested ones like isAbout[*].name, valueReference[*].name
    if len(segs) >= _FIELD_PATH_MIN_LEN and segs[-3] == "fields":
        if segs[-1] == "name":
            return True
        if segs[-1] == "type":
            return True

    return False


def _prune_empty(obj: object, *, path: str = "") -> object:
    """
    Recursively remove empty values (None, '', [], {}) from a JSON-like structure.

    Keys listed in _PROTECTED_EMPTY_KEYS, and schema-critical paths such as
    schema.fields[*].name/type, are never removed even if their value is empty.
    """
    if isinstance(obj, dict):
        result: dict[str, object] = {}
        for k, v in obj.items():
            child_path = f"{path}/{k}" if path else k
            cleaned = _prune_empty(v, path=child_path)
            # drop if empty and not protected by schema
            if cleaned in _EMPTY_SENTINELS and not _is_protected_path(child_path, k):
                continue
            result[k] = cleaned
        return result

    if isinstance(obj, list):
        cleaned_list: list[object] = []
        for idx, v in enumerate(obj):
            child_path = f"{path}/{idx}" if path else str(idx)
            cleaned = _prune_empty(v, path=child_path)
            if cleaned in _EMPTY_SENTINELS:
                continue
            cleaned_list.append(cleaned)
        return cleaned_list

    return obj


def _ensure_bounding_boxes(md: Json) -> None:  # noqa: C901, PLR0912
    """
    In-place: ensure each resource has a 4-element numeric boundingBox.

    Path targeted:
      resources[*].spatial.extent.boundingBox

    Rules:
      - If boundingBox is missing or not a list -> set to [0, 0, 0, 0].
      - If length < 4 -> pad with zeros.
      - If length > 4 -> truncate to first 4 elements.
      - Try to coerce entries to float; empty strings or invalid values -> 0.
    """
    resources = md.get("resources")
    if not isinstance(resources, list):
        return

    for res in resources:
        if not isinstance(res, dict):
            continue

        spatial = res.get("spatial")
        if not isinstance(spatial, dict):
            continue

        extent = spatial.get("extent")
        if not isinstance(extent, dict):
            continue

        bbox = extent.get("boundingBox")
        if not isinstance(bbox, list):
            bbox = []

        # normalize length
        if len(bbox) < _BBOX_COORDINATE_COUNT:
            bbox = list(bbox) + [0] * (_BBOX_COORDINATE_COUNT - len(bbox))
        elif len(bbox) > _BBOX_COORDINATE_COUNT:
            bbox = list(bbox[:_BBOX_COORDINATE_COUNT])

        # coerce to numbers, treating empty/invalid as 0
        cleaned: list[float] = []
        for v in bbox:
            if isinstance(v, (int, float)):
                cleaned.append(float(v))
            elif isinstance(v, str):
                s = v.strip()
                if not s:
                    cleaned.append(0.0)
                else:
                    try:
                        cleaned.append(float(s))
                    except ValueError:
                        cleaned.append(0.0)
            else:
                cleaned.append(0.0)

        extent["boundingBox"] = cleaned


def _normalize_object_list_shape(items: object) -> None:  # noqa: C901
    """
    In-place: make all dict elements in a list share the same key set.

    Strategy:
      - Compute the union of keys across all dict items.
      - For each key, look at the first non-empty value type:
          * if it's a list -> default is [] for missing keys
          * otherwise      -> default is "" for missing keys
      - Fill missing keys in each dict with the appropriate default.

    This is mainly used for small, schema'd objects like contributors so
    that "short" objects appended later get the same shape as template
    skeletons when keep_empty=True.
    """
    if not isinstance(items, list):
        return

    union_keys: set[str] = set()
    exemplar_is_list: dict[str, bool] = {}

    # First pass: discover keys and whether they are list-like
    for obj in items:
        if not isinstance(obj, dict):
            continue
        for k, v in obj.items():
            union_keys.add(k)
            if k not in exemplar_is_list and v is not None:
                exemplar_is_list[k] = isinstance(v, list)

    # Second pass: fill missing keys
    for obj in items:
        if not isinstance(obj, dict):
            continue
        for k in union_keys:
            if k in obj:
                continue
            if exemplar_is_list.get(k, False):
                obj[k] = []
            else:
                obj[k] = ""


def _normalize_resource_lists_for_editing(md: Json, *, keep_empty: bool) -> None:
    """
    In-place normalization of list-of-dicts shapes for better editing.

    Currently only normalizes:
      - resources[*].contributors
    """
    if not keep_empty:
        # No need to expand shapes if we're going to drop empties anyway.
        return

    resources = md.get("resources")
    if not isinstance(resources, list):
        return

    for res in resources:
        if not isinstance(res, dict):
            continue

        contributors = res.get("contributors")
        _normalize_object_list_shape(contributors)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def normalize_metadata_for_schema(
    md: Json,
    *,
    keep_empty: bool = True,
    **_: object,
) -> Json:
    """
    Return a cleaned metadata dict, suitable for saving or further editing.

    This function does **not** mutate the input.

    Parameters
    ----------
    md :
        The assembled OEMetadata mapping.
    keep_empty :
        Controls how empty values are handled:

        - True  -> keep empty fields (None, '', [], {}), but normalize
                   object shapes in certain lists so all entries look
                   consistent (good for editing).
        - False -> drop empty values and fully-empty objects using a
                   recursive prune, while **preserving keys** listed
                   in ``_PROTECTED_EMPTY_KEYS`` (e.g. ``primaryKey``).

    **_ :
        Extra keyword arguments are accepted and ignored for backward
        compatibility with older call sites (e.g. `fill_nullable`,
        `ensure_primary_key`, etc.).

    Returns
    -------
    dict
        A deep-copied and cleaned metadata dictionary.
    """
    out: Json = deepcopy(md)

    # Always fix bounding boxes (cheap and schema-friendly)
    _ensure_bounding_boxes(out)

    # Make contributors list elements look consistent in editing mode
    _normalize_resource_lists_for_editing(out, keep_empty=keep_empty)

    # Optionally drop empty values (but keep protected keys)
    if not keep_empty:
        out = _prune_empty(out)  # type: ignore[assignment]

    return out


def lint_metadata_against_schema(md: Json) -> list[str]:
    """
    Very minimal linting for obvious issues.

    Currently checks:
      - 'resources' is a list (if present).
      - each boundingBox has length 4, if present.
    """
    warnings: list[str] = []

    resources = md.get("resources")
    if resources is None:
        return warnings  # multi-dataset shapes are handled elsewhere

    if not isinstance(resources, list):
        warnings.append("Top-level 'resources' should be a list.")
        return warnings

    for i, res in enumerate(resources):
        if not isinstance(res, dict):
            warnings.append(f"resources[{i}] should be an object.")
            continue
        spatial = res.get("spatial")
        if isinstance(spatial, dict):
            extent = spatial.get("extent")
            if isinstance(extent, dict):
                bbox = extent.get("boundingBox")
                if bbox is not None and (not isinstance(bbox, list) or len(bbox) != _BBOX_COORDINATE_COUNT):
                    warnings.append(
                        f"resources[{i}].spatial.extent.boundingBox should be a "
                        f"list of {_BBOX_COORDINATE_COUNT} values.",
                    )

    return warnings


def detect_unknown_keys(metadata: Json, *, oem_schema: Json) -> list[str]:
    """
    Return an empty list of unknown keys.

    API-compatible stub; implement real logic if needed.
    """
    # Mark parameters as used to keep the signature without triggering lints.
    del metadata, oem_schema
    return []


def strip_unknown_keys(metadata: Json, *, oem_schema: Json) -> Json:
    """
    Return a deep copy unchanged.

    API-compatible stub; implement real logic if needed.
    """
    # Mark unused parameter as used.
    del oem_schema
    return deepcopy(metadata)
