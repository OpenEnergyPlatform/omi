# OMI OEMetadata Assembly Guide

This guide explains how to author, assemble, and validate **OEMetadata** using **YAML files** with OMI. It covers file structure, templating behavior, discovery vs. explicit mapping, Python APIs, multi-dataset usage, initialization scaffolding, testing, and common pitfalls.

---

## Table of Contents

1. [Overview](#overview)
2. [Concepts & Data Flow](#concepts--data-flow)
3. [Repository Layout](#repository-layout)
4. [YAML File Formats](#yaml-file-formats)

   * [Dataset YAML](#dataset-yaml)
   * [Template YAML (optional)](#template-yaml-optional)
   * [Resource YAML](#resource-yaml)
   * [Index YAML (optional)](#index-yaml-optional)
5. [Templating Rules](#templating-rules)
6. [Discovery vs. Index Mapping](#discovery-vs-index-mapping)
7. [Programmatic Usage](#programmatic-usage)

   * [Minimal Usage](#minimal-usage)
   * [With Index Mapping](#with-index-mapping)
   * [Manual Loading (No Discovery)](#manual-loading-no-discovery)
8. [Multi-dataset Assembly](#multi-dataset-assembly)
9. [Spec-Driven Output Ordering](#spec-driven-output-ordering)
10. [Project Initialization (Scaffolding)](#project-initialization-scaffolding)
11. [Airflow Integration Example](#airflow-integration-example)
12. [Testing](#testing)
13. [Validation & Error Handling](#validation--error-handling)
14. [Auto-Generation From Directory (Optional Onboarding)](#auto-generation-from-directory-optional-onboarding)
15. [Filtering Irrelevant Files (Optional)](#filtering-irrelevant-files-optional)
16. [Design Notes & Extensibility](#design-notes--extensibility)
17. [FAQ](#faq)

---

## Overview

* **Goal:** Author OEMetadata as **YAML** (dataset + resources), keep it **DRY** via **templates**, assemble into a single **JSON** metadata document, and **validate** it with the official schema.
* **Core ideas:**

  * Maintain a dataset YAML, an optional template YAML (applied to all resources), and one or more resource YAMLs.
  * OMI assembles + validates metadata into final OEMetadata JSON.
  * Works in pipelines (e.g., Airflow) and plain Python.

---

## Concepts & Data Flow

1. **Authoring:**

   * `datasets/<id>.dataset.yaml`
   * `datasets/<id>.template.yaml` *(optional)*
   * `resources/<id>/*.resource.yaml`
2. **Assembly:**

   * Load dataset, template, and resource YAML files.
   * Apply template → deep merge; resource overrides.
   * Create OEMetadata JSON via `OEMetadataCreator` and validate.
3. **Storage:**

   * Assembly returns a Python `dict`. Store wherever you like (file/DB/API).

---

## Repository Layout

```bash
metadata/
  datasets/
    <dataset_id>.dataset.yaml
    <dataset_id>.template.yaml        # optional
  resources/
    <dataset_id>/
      <resource_a>.resource.yaml
      <resource_b>.resource.yaml
  metadata_index.yaml                 # optional explicit mapping
```

Use the **convention** above or an **index** file for explicit mapping.

---

## YAML File Formats

### Dataset YAML

```yaml
# metadata/datasets/powerplants.dataset.yaml
version: "OEMetadata-2.0.4"               # optional (default: OEMetadata-2.0.4)
dataset:
  name: oep_oemetadata
  title: OEP OEMetadata
  description: A dataset for the OEMetadata examples.
  "@id": https://databus.openenergyplatform.org/oeplatform/supply/wri_global_power_plant_database/
```

> Backwards compatibility: dataset fields can also be at top-level; OMI treats that as `dataset: {...}`.

---

### Template YAML (optional)

Applied to **every** resource (unless overridden). Keeps YAML DRY.

```yaml
# metadata/datasets/powerplants.template.yaml
licenses:
  - name: ODbL-1.0
    title: Open Data Commons Open Database License 1.0
    path: https://opendatacommons.org/licenses/odbl/1-0/index.html
    instruction: >
      You are free to share and change, but you must attribute, and
      share derivations under the same license. See https://tldrlegal.com/license/odc-open-database-license-(odbl)
      for further information.
    attribution: © Reiner Lemoine Institut
    copyrightStatement: https://github.com/OpenEnergyPlatform/oemetadata/blob/production/LICENSE.txt

context:
  title: NFDI4Energy
  homepage: https://nfdi4energy.uol.de/
  documentation: https://nfdi4energy.uol.de/sites/about_us/
  sourceCode: https://github.com/NFDI4Energy
  publisher: Open Energy Platform (OEP)
  publisherLogo: https://github.com/OpenEnergyPlatform/organisation/blob/production/logo/OpenEnergyFamily_Logo_OpenEnergyPlatform.svg
  contact: contact@example.com
  fundingAgency: " Deutsche Forschungsgemeinschaft (DFG)"
  fundingAgencyLogo: https://upload.wikimedia.org/wikipedia/commons/8/86/DFG-logo-blau.svg
  grantNo: "501865131"

topics: [model_draft]
languages: [en-GB, de-DE]
keywords: [example, ODbL-1.0, NFDI4Energy]
```

---

### Resource YAML

```yaml
# metadata/resources/powerplants/oemetadata_table.resource.yaml
name: oemetadata_table
type: table
title: OEMetadata Table Template
description: Example table used to illustrate the OEMetadata structure and features.

# Resource-specific attributes
path: http://openenergyplatform.org/dataedit/view/model_draft/oemetadata_table
scheme: http
format: CSV
encoding: UTF-8

dialect:
  decimalSeparator: "."
  csv:
    delimiter: ";"

schema:
  fields:
    - name: id
      type: integer
      description: Unique identifier
      nullable: false
    # ... more fields ...
  primaryKey: [id]
  foreignKeys:
    - fields: [id, version]
      reference:
        resource: model_draft.oep_oemetadata_table_example_version
        fields: [id, version]

"@id": https://databus.openenergyplatform.org/oeplatform/supply/wri_global_power_plant_database/2022-11-07/wri_global_power_plant_database_variant=data.csv

sources:
  - title: IPCC Sixth Assessment Report (AR6) - Climate Change 2023 - Synthesis Report
    authors: [Hoesung Lee, José Romero, The Core Writing Team]
    publicationYear: "2023"
    path: https://www.ipcc.ch/report/ar6/syr/downloads/report/IPCC_AR6_SYR_FullVolume.pdf
    sourceLicenses:
      - name: CC-BY-4.0
        title: Creative Commons Attribution 4.0 International
        path: https://creativecommons.org/licenses/by/4.0/legalcode
        instruction: >
          You are free to share and change, but you must attribute.
          See https://tldrlegal.com/license/odc-open-database-license-odbl for further information.
        attribution: © Intergovernmental Panel on Climate Change 2023
        copyrightStatement: https://www.ipcc.ch/copyright/
```

Second resource:

```yaml
# metadata/resources/powerplants/data_2.resource.yaml
name: data_2
type: table
title: My Second Resource
path: reGon/metadata/data_2.csv
scheme: file
format: csv
mediatype: text/csv
encoding: utf-8
schema:
  fields:
    - name: id
      type: integer
      nullable: true
    - name: i
      type: integer
      nullable: true
    - name: o
      type: string
      nullable: true
  primaryKey: [id]
```

---

### Index YAML (optional)

Explicit mappings instead of convention:

```yaml
# metadata/metadata_index.yaml
datasets:
  powerplants:
    dataset: datasets/powerplants.dataset.yaml
    template: datasets/powerplants.template.yaml
    resources:
      - resources/powerplants/oemetadata_table.resource.yaml
      - resources/powerplants/data_2.resource.yaml
```

---

## Templating Rules

* **Deep merge** for dictionaries (e.g., `context`):
  Resource **overrides**; missing nested keys are **filled** from template.
* **Lists**:
  **Concatenate** for `keywords`, `topics`, `languages` (resource first, then template-only items).
  For other lists (e.g., `licenses`, `contributors`): **resource wins** (no concat).
  *(Modify via `DEFAULT_CONCAT_LIST_KEYS` if you want different behavior.)*
* **Scalars**: resource value **wins**.

---

## Discovery vs. Index Mapping

* **Discovery (convention):**
  `datasets/<id>.dataset.yaml`, `datasets/<id>.template.yaml`, `resources/<id>/*.resource.yaml`
  → No index needed.
* **Index (explicit):**
  Provide `metadata_index.yaml` with explicit paths relative to your base directory.

---

## Programmatic Usage

### Minimal Usage

```python
from omi.creation.assembly import assemble_metadata_dict

metadata = assemble_metadata_dict(base_dir="./metadata", dataset_id="powerplants")
```

### With Index Mapping

```python
metadata = assemble_metadata_dict(
    base_dir="./metadata",
    dataset_id="powerplants",
    index_file="./metadata/metadata_index.yaml",
)
```

### Manual Loading (No Discovery)

```python
from pathlib import Path
from omi.creation.creator import OEMetadataCreator
from omi.creation.utils import load_yaml, apply_template_to_resources

dataset = load_yaml(Path("./metadata/datasets/powerplants.dataset.yaml")).get("dataset", {})
template = load_yaml(Path("./metadata/datasets/powerplants.template.yaml"))
resources = [
    load_yaml(Path("./metadata/resources/powerplants/oemetadata_table.resource.yaml")),
    load_yaml(Path("./metadata/resources/powerplants/data_2.resource.yaml")),
]
resources = apply_template_to_resources(resources, template)

creator = OEMetadataCreator(oem_version="OEMetadata-2.0.4")
metadata = creator.generate_metadata(dataset, resources)
```

> `OEMetadataCreator` injects `@context` and `metaMetadata` from the spec and validates the result.

---

## Multi-dataset Assembly

Assemble **N datasets** in one call:

```python
from omi.creation.assembly import assemble_many_metadata

# Discover by convention (datasets/*.dataset.yaml)
all_metadata = assemble_many_metadata(base_dir="./metadata")

# From explicit index
all_metadata = assemble_many_metadata(
    base_dir="./metadata", index_file="./metadata/metadata_index.yaml"
)

# Subset
some = assemble_many_metadata(base_dir="./metadata", dataset_ids=["powerplants", "households"])
```

Result is a dict `{dataset_id: metadata}` by default.

---

## Spec-Driven Output Ordering

For human-friendly JSON key order without hard-coded lists, order by the **official example** (fallback: schema `properties`):

```python
from omi.creation.assembly import assemble_metadata_dict
from omi.creation.creator import OEMetadataCreator
from omi.creation.utils import order_with_spec

creator = OEMetadataCreator(oem_version="OEMetadata-2.0.4")
metadata = assemble_metadata_dict("./metadata", "powerplants")

ordered = order_with_spec(metadata, creator.oem_spec)  # uses spec.example and schema
```

Write with preserved unicode:

```python
import json, pathlib
out = pathlib.Path("./out/powerplants.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(ordered, indent=2, ensure_ascii=False), encoding="utf-8")
```

---

## Project Initialization (Scaffolding)

Create a metadata skeleton **from the spec** (no inline templates):

```python
from omi.creation.scaffold import init_skeleton_from_spec

paths = init_skeleton_from_spec(
    base_dir="./metadata",
    dataset_id="powerplants",
    oem_version="OEMetadata-2.0.4",
    resource_name="oemetadata_table",
    with_index=True,   # creates metadata_index.yaml
    force=False,       # do not overwrite
)
```

This imports the spec via:

```python
from omi.base import get_metadata_specification
```

…and derives:

* `datasets/<id>.dataset.yaml` (with version from spec)
* `datasets/<id>.template.yaml` (from `oem_spec.template` or pruned example resource)
* `resources/<id>/sample.resource.yaml` (sanitized from example)
* optional `metadata_index.yaml`

You can expose a CLI command `omi init` that wraps `init_skeleton_from_spec`.

---

## Airflow Integration Example

```python
from omi.creation.assembly import assemble_metadata_dict

def build_oemetadata_for_powerplants(**context):
    md = assemble_metadata_dict(
        base_dir="/opt/airflow/dags/metadata",
        dataset_id="powerplants",
        index_file="/opt/airflow/dags/metadata/metadata_index.yaml",
    )
    context["ti"].xcom_push(key="oemetadata", value=md)
```

---

## Testing

* **Assembly test** (uses a fake creator): see `tests/test_assembly.py` example in this doc.
* **Utils tests** (I/O, discovery, merging): see `tests/test_creation_utils.py`.
  It covers:

  * `load_parts` (template application)
  * `_merge_lists`, `deep_apply_template_to_resource`, `apply_template_to_resources`
  * `load_yaml`
  * `discover_paths`, `resolve_from_index`, `load_parts`
  * `discover_dataset_ids`, `discover_dataset_ids_from_index`

Run:

```bash
pytest -q
```

---

## Validation & Error Handling

`OEMetadataCreator.generate_metadata()` validates with the official schema:

```python
from omi.validation import ValidationError

try:
    metadata = assemble_metadata_dict("./metadata", "powerplants")
except ValidationError as e:
    print("Validation failed:", e)
```

**Common causes**:

* Missing required field keys (e.g., a schema field without `"nullable"`).
* Wrong types (e.g., non-URI where `format: uri` is required).
* Invalid list shapes (e.g., `primaryKey`, `foreignKeys`).

---

## Auto-Generation From Directory (Optional Onboarding)

You can bootstrap YAMLs from a directory or zip:

* infer resources from file names/extensions
* for CSV, infer a table schema
* emit dataset YAML + one resource YAML per file

Use filters to skip temp/log/backup files (see next section).

---

## Filtering Irrelevant Files (Optional)

When scanning directories, exclude noise such as backup and editor artifacts:

```python
exclude_extensions = {".log", ".tmp", ".bak", ".DS_Store", ".md"}
exclude_patterns   = {"*_backup.*", "*~", "*.old", "*.ignore"}
exclude_hidden     = True
```

---

## Design Notes & Extensibility

* **Separation of concerns**:

  * `utils`: YAML loading, discovery, deep merge, ordering by spec.
  * `assembly`: Orchestrates load → merge → create → (optionally) order.
  * `creator`: Pulls spec via `get_metadata_specification`, injects `@context` and `metaMetadata`, validates.
  * `scaffold`: Initializes a project from the **spec/example** (no inline strings).
* **Storage-agnostic**: assembly returns a dict; saving is up to you.
* **Configurable merging**: tweak `DEFAULT_CONCAT_LIST_KEYS` to change list concat behavior.

---

## FAQ

**Q: Can resource YAML override template-provided `licenses`?**
A: Yes. By default, resource lists override template lists except for `keywords`, `topics`, `languages` (which concatenate). Add `"licenses"` to `DEFAULT_CONCAT_LIST_KEYS` if you want concatenation.

**Q: Where do `@context` and `metaMetadata` come from?**
A: `OEMetadataCreator` loads the spec (`get_metadata_specification(oem_version)`) and injects both before validation.

**Q: Why does JSON show `\u00a9` instead of `©`?**
A: Use `ensure_ascii=False` in `json.dump` to preserve unicode characters.

**Q: I got a validation error: `'nullable' is a required property`.**
A: Ensure each `schema.fields[]` has **`name`**, **`type`**, **`nullable`**. If you auto-generate, set `nullable: false` unless you detect nulls.

**Q: Can I reorder output keys to match the official example?**
A: Yes. Use `order_with_spec(metadata, creator.oem_spec)` for spec-driven ordering (no hard-coded key lists).

**Q: Can I manage multiple datasets in one metadata module?**
A: Yes. Use `assemble_many_metadata(...)` to discover/assemble **N datasets** at once (by convention or index).
