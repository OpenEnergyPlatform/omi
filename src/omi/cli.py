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
import yaml

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
from omi.inspection import inspect_db_table


def _infer_db_targets(resource_name: str, db_schema: Optional[str], db_table: Optional[str]) -> tuple[str, str]:
    """Infer database schema and table from resource name."""
    expected_parts = 2
    parts = resource_name.split(".")
    if not db_schema or not db_table:
        if len(parts) == expected_parts:
            inferred_schema, inferred_table = parts
            db_schema = db_schema or inferred_schema
            db_table = db_table or inferred_table
        else:
            db_table = db_table or resource_name
    return db_schema or "", db_table or ""


def _print_drift_report(report: dict) -> bool:
    """Print the drift report and return whether drift was detected."""
    drift_detected = False
    if report.get("missing_in_yaml"):
        click.secho(
            f"[!] Columns in DB but missing in YAML: {', '.join(map(str, report['missing_in_yaml']))}",
            fg="yellow",
        )
        drift_detected = True
    if report.get("missing_in_db"):
        click.secho(
            f"[!] Columns in YAML but missing in DB: {', '.join(map(str, report['missing_in_db']))}",
            fg="yellow",
        )
        drift_detected = True
    if report.get("type_mismatches"):
        click.secho("[!] Type mismatches detected:", fg="yellow")
        for col, mismatch in report["type_mismatches"].items():
            if isinstance(mismatch, dict):
                click.echo(f"    - {col}: YAML={mismatch.get('yaml')}, DB={mismatch.get('db')}")
        drift_detected = True
    return drift_detected


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
    res = init_dataset(
        base_dir,
        dataset_id,
        oem_version=oem_version,
        resources=resources,
        overwrite=overwrite,
    )
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
@click.option(
    "--delimiter",
    default=None,
    help="CSV column delimiter. Detected per file if omitted.",
)
def init_resources_cmd(  # noqa: PLR0913
    base_dir: Path,
    dataset_id: str,
    files: tuple[Path, ...],
    oem_version: str,
    delimiter: Optional[str],
    *,
    overwrite: bool,
) -> None:
    """Create resource YAML files for DATASET_ID from the given FILES."""
    outs = init_resources_from_files(
        base_dir,
        dataset_id,
        files,
        oem_version=oem_version,
        overwrite=overwrite,
        delimiter=delimiter,
    )
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


@init.command("db-resource")
@click.argument("base_dir", type=click.Path(file_okay=False, path_type=Path))
@click.argument("dataset_id")
@click.argument("connection_string")
@click.option("--schema", "schema_name", required=True, help="Database schema name.")
@click.option("--table", "table_name", required=True, help="Database table name.")
@click.option("--overwrite", is_flag=True, help="Overwrite existing resource YAML with the same name.")
def init_db_resource_cmd(  # noqa: PLR0913
    base_dir: Path,
    dataset_id: str,
    connection_string: str,
    schema_name: str,
    table_name: str,
    *,
    overwrite: bool,
) -> None:
    """
    Inspect a database table and add it as a resource to a local dataset.

    BASE_DIR:          Root directory containing 'datasets/' and 'resources/'.
    DATASET_ID:        Local dataset id in the split-files layout.
    CONNECTION_STRING: SQLAlchemy database URL.
    """
    # 1. Fetch the skeleton from the database
    try:
        resource_skeleton = inspect_db_table(connection_string, schema_name, table_name)
    except Exception as err:  # noqa: BLE001
        click.secho(f"Failed to inspect database: {err}", fg="red", err=True)
        raise click.Abort from err

    # 2. Determine target path: resources/<dataset_id>/<schema>_<table_name>.resource.yaml
    # We replace '.' with '_' in the filename to avoid confusing extension parsing
    safe_name = resource_skeleton["name"].replace(".", "_")
    target_dir = base_dir / "resources" / dataset_id
    target_path = target_dir / f"{safe_name}.resource.yaml"

    # 3. Check for existence
    if target_path.exists() and not overwrite:
        click.secho(
            f"Resource file already exists: {target_path}\nUse --overwrite to force.",
            fg="yellow",
            err=True,
        )
        raise click.Abort

    # 4. Create directory if it doesn't exist and write the file
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        yaml.safe_dump(resource_skeleton, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    click.echo(f"resource: {target_path}")


@click.group()
def inspect() -> None:
    """Inspect external sources to generate OEMetadata skeletons."""


@inspect.command("db")
@click.argument("connection_string")
@click.option("--schema", "schema_name", required=True, help="Database schema name.")
@click.option("--table", "table_name", required=True, help="Database table name.")
def inspect_db_cmd(connection_string: str, schema_name: str, table_name: str) -> None:
    """
    Inspect a database table and output a YAML resource skeleton.

    CONNECTION_STRING: A SQLAlchemy compatible database URL
    (e.g., postgresql://user:pass@localhost:5432/dbname).
    """
    try:
        resource_skeleton = inspect_db_table(connection_string, schema_name, table_name)
        # Dump the dictionary as YAML to standard output
        yaml_output = yaml.safe_dump(resource_skeleton, sort_keys=False, allow_unicode=True)
        click.echo(yaml_output)
    except Exception as err:  # noqa: BLE001
        click.secho(f"Inspection failed: {err}", fg="red", err=True)
        raise click.Abort from err


@inspect.command("db-drift")
@click.argument("base_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.argument("dataset_id")
@click.argument("resource_name")
@click.argument("connection_string")
@click.option("--schema", "db_schema", help="Database schema (defaults to prefix of resource_name).")
@click.option("--table", "db_table", help="Database table (defaults to suffix of resource_name).")
@click.option("--strict", is_flag=True, help="Exit with error code if drift is detected.")
@click.option("--apply", is_flag=True, help="Update the local resource YAML file with DB structure.")
def inspect_db_drift_cmd(  # noqa: PLR0913
    base_dir: Path,
    dataset_id: str,
    resource_name: str,
    connection_string: str,
    db_schema: Optional[str],
    db_table: Optional[str],
    *,
    strict: bool,
    apply: bool,
) -> None:
    """
    Check for schema drift between local YAML and the database.

    BASE_DIR:          Root directory containing 'datasets/' and 'resources/'.
    DATASET_ID:        Local dataset id (e.g., 'egon-data').
    RESOURCE_NAME:     The name of the resource (e.g., 'boundaries.my_table').
    CONNECTION_STRING: SQLAlchemy database URL.
    """
    from omi.creation.builder import MetadataBuilder, SchemaDriftError
    from omi.creation.utils import dump_yaml, load_yaml
    from omi.inspection import inspect_db_table

    # 1. Infer schema/table if not explicitly provided
    db_schema, db_table = _infer_db_targets(resource_name, db_schema, db_table)

    if not db_table:
        click.secho("Could not infer database table. Please provide --table.", fg="red", err=True)
        raise click.Abort

    # 2. Load the specific resource YAML file
    safe_name = resource_name.replace(".", "_")
    resource_path = base_dir / "resources" / dataset_id / f"{safe_name}.resource.yaml"

    if not resource_path.exists():
        click.secho(f"Resource file not found: {resource_path}", fg="red", err=True)
        raise click.Abort

    resource_dict = load_yaml(resource_path)

    # 3. Fetch physical DB Skeleton
    try:
        db_skeleton = inspect_db_table(connection_string, db_schema, db_table)
    except Exception as err:  # noqa: BLE001
        click.secho(f"Failed to inspect database: {err}", fg="red", err=True)
        raise click.Abort from err

    # 4. Use Builder to compute diff
    # We wrap the single resource in a dummy metadata structure to use the builder logic cleanly
    dummy_md = {"resources": [resource_dict]}
    builder = MetadataBuilder(dummy_md)

    try:
        report = builder.resource(0).merge_and_diff_db_schema(db_skeleton, strict=strict)
    except SchemaDriftError as err:
        click.secho(str(err), fg="red", err=True)
        raise click.Abort from err

    # 5. Print the Drift Report
    drift_detected = _print_drift_report(report)

    if not drift_detected:
        click.secho(f"✓ No schema drift detected for '{resource_name}'", fg="green")

    # 6. Apply changes back to the YAML file
    if apply and drift_detected:
        updated_resource = builder.build(validate_policy="skip")["resources"][0]
        # omi's dump_yaml handles creating directories if needed
        dump_yaml(resource_path, dict(updated_resource))
        click.secho(f"✓ Automatically updated resource YAML: {resource_path.name}", fg="green")


@grp.command("add-source")
@click.argument("resource_yaml", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--kind",
    type=click.Choice(["external", "internal"]),
    default="external",
    show_default=True,
    help="external: literature/other database; internal: another table in this project.",
)
@click.option("--title", default=None, help="Source title (required for --kind external).")
@click.option("--table", "ref_table", default=None, help="Referenced table name (required for --kind internal).")
@click.option("--path", "src_path", default="", help="URL or reference path of the source.")
@click.option("--description", default="", help="Human-readable source description.")
def add_source_cmd(  # noqa: PLR0913
    resource_yaml: Path,
    kind: str,
    title: Optional[str],
    ref_table: Optional[str],
    src_path: str,
    description: str,
) -> None:
    """Append a provenance source to a resource YAML (non-destructive, de-duplicated)."""
    from omi.creation.sources import (
        add_source_to_resource_file,
        build_external_source,
        build_internal_source,
    )

    if kind == "internal":
        if not ref_table:
            msg = "--table is required for --kind internal"
            raise click.UsageError(msg)
        source = build_internal_source(ref_table, title=title, description=description, path=src_path)
    else:
        if not title:
            msg = "--title is required for --kind external"
            raise click.UsageError(msg)
        source = build_external_source(title, description=description, path=src_path)

    added = add_source_to_resource_file(resource_yaml, source)
    if added:
        click.secho(f"✓ Added {kind} source to {resource_yaml}", fg="green")
    else:
        click.secho(f"= Equivalent source already present in {resource_yaml}; unchanged", fg="yellow")


@grp.command("coverage")
@click.argument("base_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "--expected-file",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="File listing expected resource names, one per line ('#' comments allowed).",
)
@click.option("--dataset-id", "dataset_ids", multiple=True, help="Restrict scan to these dataset ids (repeatable).")
@click.option("--strict", is_flag=True, help="Exit non-zero if any expected resource is missing.")
@click.option(
    "--no-field-descriptions",
    is_flag=True,
    help="Do not require per-field descriptions for a resource to count as complete.",
)
def coverage_cmd(
    base_dir: Path,
    expected_file: Path,
    dataset_ids: tuple[str, ...],
    *,
    strict: bool,
    no_field_descriptions: bool,
) -> None:
    """Report documented/skeleton/missing/orphan coverage against an expected resource list."""
    from omi.creation.coverage import coverage_report

    expected = [
        line.strip()
        for line in expected_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    report = coverage_report(
        base_dir,
        expected,
        dataset_ids=dataset_ids or None,
        require_field_descriptions=not no_field_descriptions,
    )

    click.echo(report.summary())
    for name in report.missing:
        click.secho(f"[missing]  {name}", fg="red")
    for state in report.skeleton:
        detail = "; ".join(state.reasons[:3])
        click.secho(f"[skeleton] {state.name}  ({detail})", fg="yellow")
    for name in report.orphans:
        click.secho(f"[orphan]   {name}", fg="cyan")

    if strict and not report.ok:
        raise click.Abort


# The `init` and `inspect` groups are reachable both ways:
#   * nested, as documented:  `omi init resources ...`, `omi inspect db ...`
#   * flat, for backwards compatibility:  `omi resources ...`, `omi db ...`
# The nesting comes from registering the groups on `grp`, the flat aliases from
# listing them as CommandCollection sources.
grp.add_command(init)
grp.add_command(inspect)

# Keep CommandCollection for backwards compatibility with your entry point
cli = click.CommandCollection(sources=[grp, init, inspect])


def main() -> None:
    """Start click application."""
    cli()
