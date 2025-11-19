# OMI “Create” Entry Point

This mini-guide explains how to use the **programmatic entry points** that turn your split YAML metadata (dataset + template + resources) into a single OEMetadata JSON document.

> If you’re looking for how to author the YAML files and how templating works, see the main **Assembly Guide** in the `creation` module directory. This page just shows how to *call* the entry points.

---

## What it does

The functions in `omi.create` wrap the full assembly pipeline:

1. **Discover / load** your YAML parts (dataset, optional template, resources).
2. **Apply the template** to each resource (deep merge; resource wins; keywords/topics/languages concatenate).
3. **Generate & validate** the final OEMetadata JSON using the official schema (via `OEMetadataCreator`).
4. **Write** the result to disk (`build_from_yaml`) or many results to a directory (`build_many_from_yaml`).

---

## API

```python
from omi.create import build_from_yaml, build_many_from_yaml
```

### `build_from_yaml(base_dir, dataset_id, output_file, *, index_file=None) -> None`

Assemble **one** dataset and write `<output_file>` (JSON).

* `base_dir` (`str | Path`): Root that contains:

  * `datasets/<dataset_id>.dataset.yaml`
  * `datasets/<dataset_id>.template.yaml` *(optional)*
  * `resources/<dataset_id>/*.resource.yaml`
* `dataset_id` (`str`): Logical dataset name (e.g. `"powerplants"`).
* `output_file` (`str | Path`): Path to write the generated OEMetadata JSON.
* `index_file` (`str | Path | None`): Optional explicit mapping file (`metadata_index.yaml`). If provided, paths are taken from the index instead of convention.

### `build_many_from_yaml(base_dir, output_dir, *, dataset_ids=None, index_file=None) -> None`

Assemble **multiple** datasets and write each as `<output_dir>/<dataset_id>.json`.

* `base_dir` (`str | Path`): Same as above.
* `output_dir` (`str | Path`): Destination directory for one JSON file per dataset.
* `dataset_ids` (`list[str] | None`): Limit to specific datasets. If `None`, we:

  * Use keys from `index_file` when provided, **else**
  * Discover all `datasets/*.dataset.yaml` in `base_dir`.
* `index_file` (`str | Path | None`): Optional `metadata_index.yaml`.

---

## Quick examples

### One dataset (convention-based discovery)

```python
from omi.create import build_from_yaml

build_from_yaml(
    base_dir="./metadata",
    dataset_id="powerplants",
    output_file="./out/powerplants.json",
)
```

Directory layout:

```bash
metadata/
  datasets/
    powerplants.dataset.yaml
    powerplants.template.yaml     # optional
  resources/
    powerplants/
      *.resource.yaml
```

### One dataset (explicit index)

```python
from omi.create import build_from_yaml

build_from_yaml(
    base_dir="./metadata",
    dataset_id="powerplants",
    output_file="./out/powerplants.json",
    index_file="./metadata/metadata_index.yaml",
)
```

### Many datasets (discover all)

```python
from omi.create import build_many_from_yaml

build_many_from_yaml(
    base_dir="./metadata",
    output_dir="./out",
)
# writes ./out/<dataset_id>.json for each dataset found
```

### Many datasets (index + subset)

```python
from omi.create import build_many_from_yaml

build_many_from_yaml(
    base_dir="./metadata",
    output_dir="./out",
    dataset_ids=["powerplants", "households"],
    index_file="./metadata/metadata_index.yaml",
)
```

---

## Notes & behavior

* Output JSON is written with `indent=2` and **`ensure_ascii=False`** to preserve characters like `©`.
* Validation happens via `OEMetadataCreator` using the official schema provided by `oemetadata` (imported through `omi.base.get_metadata_specification`).
* If a dataset YAML is missing, `FileNotFoundError` is raised.
* If schema validation fails, you’ll get an exception from `omi.validation`. Catch it where you call the entry point if you want to handle/report errors.

---

## Using in 3rd Party code like data pipelines

```python
from pathlib import Path
from omi.create import build_from_yaml

def build_oemetadata_callable(**context):
    base = Path("/project/metadata")
    out = Path("/project/metadata/out/powerplants.json")
    build_from_yaml(base, "powerplants", out)
    # optionally push to airflow XCom, publish, upload, etc.
```

---

## Testing tips

* For **unit tests** of `omi.create`, patch `omi.create.assemble_metadata_dict` / `assemble_many_metadata` and verify files are written.
* For **integration tests**, put real example YAMLs under `tests/test_data/create/metadata/` and call `build_from_yaml` end-to-end.

---

## Troubleshooting

* **“Dataset YAML not found”**
  Check `base_dir/datasets/<dataset_id>.dataset.yaml` exists, or supply the correct `index_file`.

* **Unicode characters appear escaped (`\u00a9`)**
  Ensure you’re not re-writing the JSON elsewhere with `ensure_ascii=True`.

* **Template not applied**
  Confirm your template file name matches `<dataset_id>.template.yaml` (or is correctly referenced from the index), and the keys you expect to inherit aren’t already set in the resource (resource values win).
