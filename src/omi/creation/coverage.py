# omi/creation/coverage.py
"""
Coverage reporting for an OEMetadata split-YAML store.

Given an *expected* set of resource names (the tables that should be
documented -- supplied by the caller, e.g. derived from a pipeline's declared
outputs), report which are:

- **missing**  -- expected but no resource YAML exists (hard gap),
- **skeleton** -- a YAML exists but required human fields are still blank or
  carry scaffolding placeholders (soft gap / warning),
- **complete** -- fully documented,

plus **orphans** -- resources present in the store that nobody expects.

The expected list is caller-supplied so this stays project-agnostic: OMI does
not know about any particular pipeline's output declarations; the caller
computes the list and passes resource names in.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from .utils import discover_dataset_ids, discover_paths, load_yaml

if TYPE_CHECKING:
    from collections.abc import Iterable

Json = dict[str, object]

# a filled field must not still carry a scaffolding placeholder
_PLACEHOLDER_MARKERS: tuple[str, ...] = ("TODO", "WILL_BE_SET_AT_PUBLICATION")
# resource-level fields a human must fill for a resource to count as complete
_DEFAULT_REQUIRED_RESOURCE_FIELDS: tuple[str, ...] = ("title", "description")


@dataclass
class ResourceState:
    """Coverage state of a single expected resource."""

    name: str
    state: str  # "missing" | "skeleton" | "complete"
    path: Optional[Path] = None
    reasons: list[str] = field(default_factory=list)


@dataclass
class CoverageReport:
    """Result of comparing an expected resource list against the store."""

    missing: list[str] = field(default_factory=list)  # expected, no YAML
    skeleton: list[ResourceState] = field(default_factory=list)
    complete: list[str] = field(default_factory=list)
    orphans: list[str] = field(default_factory=list)  # in store, not expected
    states: dict[str, ResourceState] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        """True when nothing expected is missing (skeletons are warnings)."""
        return not self.missing

    def summary(self) -> str:
        """One-line human-readable tally."""
        return (
            f"complete={len(self.complete)} "
            f"skeleton={len(self.skeleton)} "
            f"missing={len(self.missing)} "
            f"orphans={len(self.orphans)}"
        )


def _is_blank(value: object) -> bool:
    return value in (None, "", [], {})


def _has_placeholder(value: object) -> bool:
    return isinstance(value, str) and any(m in value for m in _PLACEHOLDER_MARKERS)


def resource_completeness(
    resource: Json,
    *,
    required_fields: Iterable[str] = _DEFAULT_REQUIRED_RESOURCE_FIELDS,
    require_field_descriptions: bool = True,
) -> tuple[str, list[str]]:
    """
    Classify a resource dict as ``"complete"`` or ``"skeleton"``.

    A resource is *complete* when every required resource-level field is
    non-empty and free of scaffolding placeholders and -- when
    ``require_field_descriptions`` is set -- every schema field carries a
    placeholder-free description. Otherwise it is a *skeleton*.

    Returns
    -------
    (state, reasons)
        ``reasons`` lists every unmet condition (empty when complete).
    """
    reasons: list[str] = []

    for name in required_fields:
        value = resource.get(name)
        if _is_blank(value):
            reasons.append(f"'{name}' is empty")
        elif _has_placeholder(value):
            reasons.append(f"'{name}' still has a placeholder")

    if require_field_descriptions:
        schema = resource.get("schema")
        fields = schema.get("fields") if isinstance(schema, dict) else None
        if isinstance(fields, list):
            for fld in fields:
                if not isinstance(fld, dict):
                    continue
                col = fld.get("name", "?")
                desc = fld.get("description")
                if _is_blank(desc):
                    reasons.append(f"field '{col}' has no description")
                elif _has_placeholder(desc):
                    reasons.append(f"field '{col}' description is a placeholder")

    return ("complete" if not reasons else "skeleton", reasons)


def index_store_resources(
    base_dir: Union[str, Path],
    *,
    dataset_ids: Optional[Iterable[str]] = None,
) -> dict[str, Path]:
    """
    Map every resource *name* present in the store to its YAML path.

    Scans the given dataset ids (or all discovered ids) and reads each
    resource YAML's ``name`` field. A name defined in more than one dataset
    resolves to the last one scanned.
    """
    base = Path(base_dir)
    ids = list(dataset_ids) if dataset_ids is not None else discover_dataset_ids(base)
    index: dict[str, Path] = {}
    for ds_id in ids:
        _, _, resource_paths = discover_paths(base, ds_id)
        for path in resource_paths:
            doc = load_yaml(path)
            name = doc.get("name")
            if isinstance(name, str) and name:
                index[name] = path
    return index


def coverage_report(
    base_dir: Union[str, Path],
    expected: Iterable[str],
    *,
    dataset_ids: Optional[Iterable[str]] = None,
    required_fields: Iterable[str] = _DEFAULT_REQUIRED_RESOURCE_FIELDS,
    require_field_descriptions: bool = True,
) -> CoverageReport:
    """
    Compare an expected resource-name list against the store.

    Parameters
    ----------
    base_dir :
        Path to the metadata store (contains ``datasets/`` and ``resources/``).
    expected :
        Resource names that *should* be documented (e.g. ``schema.table``).
    dataset_ids :
        Restrict the scan to these dataset ids (default: all discovered).
    required_fields, require_field_descriptions :
        Passed through to :func:`resource_completeness` to tune the
        skeleton/complete threshold.
    """
    expected_names = list(dict.fromkeys(expected))  # dedupe, preserve order
    store = index_store_resources(base_dir, dataset_ids=dataset_ids)
    required = tuple(required_fields)

    report = CoverageReport()
    for name in expected_names:
        path = store.get(name)
        if path is None:
            state = ResourceState(name=name, state="missing")
            report.missing.append(name)
        else:
            level, reasons = resource_completeness(
                load_yaml(path),
                required_fields=required,
                require_field_descriptions=require_field_descriptions,
            )
            state = ResourceState(name=name, state=level, path=path, reasons=reasons)
            if level == "complete":
                report.complete.append(name)
            else:
                report.skeleton.append(state)
        report.states[name] = state

    expected_set = set(expected_names)
    report.orphans = sorted(name for name in store if name not in expected_set)
    return report
