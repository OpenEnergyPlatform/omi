# OMI OEMetadata Assembly Guide

This guide explains how to author, assemble, and validate **OEMetadata** using **YAML files** with OMI. It covers file structure, templating behavior, discovery vs. explicit mapping, Python APIs, testing, and common pitfalls. You can drop this as a single `.md` file in your repo (e.g. `docs/oemetadata-assembly.md`) or split into multiple files later.

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
8. [Airflow Integration Example](#airflow-integration-example)
9. [Testing](#testing)
10. [Validation & Error Handling](#validation--error-handling)
11. [Auto-Generation From Directory (Optional Onboarding)](#auto-generation-from-directory-optional-onboarding)
12. [Filtering Irrelevant Files (Optional)](#filtering-irrelevant-files-optional)
13. [Design Notes & Extensibility](#design-notes--extensibility)
14. [FAQ](#faq)

---

## Overview

* **Goal:** Author OEMetadata as **YAML** (dataset + resources), keep it **DRY** via **templates**, assemble into a single **JSON** metadata document, and **validate** it with the official schema.
* **Core ideas:**

  * Authors maintain a dataset YAML, an optional template YAML (applied to all resources), and one or more resource YAMLs.
  * OMI assembles and validates metadata into a final OEMetadata JSON.
  * Works well in pipelines (e.g., Airflow) and in regular Python.

---

## Concepts & Data Flow

1. **Authoring:**

   * `datasets/<id>.dataset.yaml`
   * `datasets/<id>.template.yaml` *(optional)*
   * `resources/<id>/*.resource.yaml`

2. **Assembly:**

   * OMI **loads** dataset, template, and resource YAML files.
   * OMI **applies the template** to each resource (deep merge; resource overrides template).
   * OMI **generates and validates** OEMetadata JSON via `OEMetadataCreator`.

3. **Storage:**

   * You decide where to store: file, DB, API, etc. (OMI returns a Python `dict`).

---

## Repository Layout

```
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

* You can use **convention** (the directory / filename structure above) or an **index** file for explicit mapping.

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

> Backwards compatibility: if you prefer, you may put dataset fields directly at the top level; OMI will treat that as `dataset: {...}`.

---

### Template YAML (optional)

Applied to **every** resource (unless the resource overrides specific fields). Keeps your YAML DRY.

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
# metadata/resources/powerplants/oemetadata_table_template.resource.yaml
name: oemetadata_table_template
type: table
title: OEMetadata Table Template
description: Example table used to illustrate the OEMetadata structure and features.

# Resource-specific attributes
path: http://openenergyplatform.org/dataedit/view/model_draft/oemetadata_table_template
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

# Other metadata like subject, publicationDate, spatial, temporal, contributors, review...
```

A second resource:

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

Use this if you want explicit mappings instead of convention-based discovery.

```yaml
# metadata/metadata_index.yaml
datasets:
  powerplants:
    dataset: datasets/powerplants.dataset.yaml
    template: datasets/powerplants.template.yaml
    resources:
      - resources/powerplants/oemetadata_table_template.resource.yaml
      - resources/powerplants/data_2.resource.yaml
```

---

## Templating Rules

* **Deep merge** for dictionaries (e.g., `context`):

  * Resource **overrides** template on conflicts.
  * Missing nested keys are **filled** from template.

* **Lists**:

  * **Concatenate** (resource first, then template-only items) for:
    `keywords`, `topics`, `languages`.
  * For other lists (e.g., `licenses`, `contributors`), **resource wins** (no concat).
  * You can change this behavior in code by adding keys to `DEFAULT_CONCAT_LIST_KEYS`.

* **Scalars**: resource value **wins**.

This keeps YAML DRY while allowing fine-grained per-resource overrides.

---

## Discovery vs. Index Mapping

* **Discovery (convention):**
  `datasets/<id>.dataset.yaml`, `datasets/<id>.template.yaml`, and `resources/<id>/*.resource.yaml`
  → No index file needed.

* **Index (explicit mapping):**
  Use `metadata_index.yaml` to map dataset/template/resources by path, relative to the metadata base directory.

---

## Programmatic Usage

OMI exposes high-level assembly and creation utilities.

### Minimal Usage

```python
from omi.creation.assembly import assemble_metadata_dict

metadata = assemble_metadata_dict(
    base_dir="./metadata",
    dataset_id="powerplants",
)  # returns a Python dict with valid OEMetadata
```

### With Index Mapping

```python
from omi.creation.assembly import assemble_metadata_dict

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
    load_yaml(Path("./metadata/resources/powerplants/oemetadata_table_template.resource.yaml")),
    load_yaml(Path("./metadata/resources/powerplants/data_2.resource.yaml")),
]

resources = apply_template_to_resources(resources, template)
creator = OEMetadataCreator(oem_version="OEMetadata-2.0.4")
metadata = creator.generate_metadata(dataset, resources)
```

> The `OEMetadataCreator` injects `@context` and `metaMetadata` and calls validation.

---

## Airflow Integration Example

```python
# In a DAG task (PythonOperator callable)
from omi.creation.assembly import assemble_metadata_dict

def build_oemetadata_for_powerplants(**context):
    md = assemble_metadata_dict(
        base_dir="/opt/airflow/dags/metadata",          # your metadata module
        dataset_id="powerplants",
        index_file="/opt/airflow/dags/metadata/metadata_index.yaml",  # or None for discovery
    )
    # Store or pass downstream: write to file/DB/API, or XCom
    context["ti"].xcom_push(key="oemetadata", value=md)
```

---

## Testing

You can unit test assembly logic without depending on the real spec/validator by **monkeypatching** the creator.

**Example (`tests/test_assembly.py`):**

```python
from pathlib import Path
import yaml
import pytest
from omi.creation.assembly import assemble_metadata_dict

def write_yaml(p: Path, data) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")

class FakeCreator:
    def __init__(self, oem_version: str = "OEMetadata-2.0.4"):
        self.oem_version = oem_version
    def generate_metadata(self, dataset: dict, resources: list[dict]) -> dict:
        return {"@context": "...", **dataset, "resources": resources, "metaMetadata": {"metadataVersion": self.oem_version}}

def test_assemble(tmp_path, monkeypatch):
    write_yaml(tmp_path / "datasets" / "demo.dataset.yaml", {"dataset": {"name": "demo", "title": "Demo"}})
    write_yaml(tmp_path / "datasets" / "demo.template.yaml", {"keywords": ["k1"], "context": {"contact": "a@b"}})
    write_yaml(tmp_path / "resources" / "demo" / "a.resource.yaml", {"name": "a", "title": "A", "keywords": ["ak"]})
    write_yaml(tmp_path / "resources" / "demo" / "b.resource.yaml", {"name": "b", "title": "B", "context": {"publisher": "X"}})

    monkeypatch.setattr("omi.creation.assembly.OEMetadataCreator", FakeCreator)
    md = assemble_metadata_dict(tmp_path, "demo")

    assert md["name"] == "demo"
    a, b = md["resources"]
    assert a["keywords"] == ["ak", "k1"]          # concat
    assert b["context"]["contact"] == "a@b"       # filled from template
    assert b["context"]["publisher"] == "X"       # resource wins
```

Run with:

```bash
pytest -q
```

---

## Validation & Error Handling

* `OEMetadataCreator.generate_metadata()` runs `validate_metadata(metadata, check_license=False)`.
* If validation fails, catch and inspect the exception from `omi.validation`:

```python
from omi.validation import ValidationError

try:
    metadata = assemble_metadata_dict("./metadata", "powerplants")
except ValidationError as e:
    print("Validation failed:", e)
```

**Common causes:**

* Missing **required** keys (e.g., field missing `"nullable"`).
* Incorrect data types (e.g., non-URI in a field that requires `format: uri`).
* Invalid list shapes (`primaryKey`, `foreignKeys`, etc.).

---

## Auto-Generation From Directory (Optional Onboarding)

You can auto-generate a starter YAML for a dataset by scanning a directory or zip:

* Infer resource entries based on file names & extensions.
* For CSVs, call your CSV inference to produce initial `schema.fields`.
* Write a `dataset` YAML + per-file `resource` YAMLs as a starting point.

> Keep this as an onboarding tool; human review is still recommended.

---

## Filtering Irrelevant Files (Optional)

If auto-generating from a directory, filter out noise:

```python
def read_directory(directory, exclude_extensions=None, exclude_patterns=None, exclude_hidden=True):
    # ...
    # exclude_extensions=['.log','.tmp','.bak','.DS_Store','.md']
    # exclude_patterns=['*_backup.*','*~','*.old','*.ignore']
    return files
```

Helps avoid including backups, temp files, editor artifacts, etc.

---

## Design Notes & Extensibility

* **Separation of concerns**:

  * `utils` covers loading YAML, discovery, merging/templating.
  * `assembly` orchestrates the load → merge → create flow.
  * `creator` handles schema-based assembly and validation.
* **Storage-agnostic**: assembly returns a dict; you decide where to store it (file/DB/API).
* **Configurable merge**: change list concat behavior by editing `DEFAULT_CONCAT_LIST_KEYS`.

---

## FAQ

**Q:** Can a resource override template-provided `licenses`?
**A:** Yes. By default, **resource wins** for lists except `keywords`, `topics`, `languages` (which concatenate). You can include `"licenses"` in `DEFAULT_CONCAT_LIST_KEYS` if you want concatenation.

**Q:** Where does `@context` and `metaMetadata` come from?
**A:** `OEMetadataCreator` reads the official spec via `get_metadata_specification(oem_version)` and injects `@context` and a `metaMetadata` block, then validates the final result.

**Q:** The output JSON shows `\u00a9` instead of `©`.
**A:** Use `ensure_ascii=False` when dumping JSON:

```python
json.dump(metadata, f, indent=2, ensure_ascii=False)
```

**Q:** I see validation errors about fields missing `nullable`.
**A:** Ensure each `schema.fields[]` has **`name`**, **`type`**, and **`nullable`** at minimum. If you auto-generate fields, set `nullable: false` as a safe default unless you detect nulls.

**Q:** How do I run without a template YAML?
**A:** Just omit `datasets/<id>.template.yaml`; assembly works without it.

---

> If you want this split across multiple docs, consider:
> `docs/assembly-overview.md`, `docs/yaml-formats.md`, `docs/templating.md`, `docs/integration-airflow.md`, `docs/testing.md`, and `docs/troubleshooting.md`.
