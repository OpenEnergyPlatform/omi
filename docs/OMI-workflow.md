# Local - remote metadata workflow using OMI and the OEP

This document provides documentation about the core workflow we suggest to work with omi locally to create a single or multiple oemetadata documents.

The workflow describes how local metadata creation using OMI´s YAML file structure can be used together with table resources available on the OEP. The YAML system describes dataset and resources and also provides the option to add reoccurring information to a template YAML. It is used locally on the users PC and allows for a structured metadata management for one or multiple dataset.
To use the OEP as remote metadata repository OMI provides functionality to push or pull metadata to or from tables which are available on the OEP using the Rest-API.

## Workflow

The workflow is still not perfect and must be followed quite strictly especially when working with local metadata files and tables on the OEP. Otherwise it might happen that users create a local version of the metadata and on the same time a table on the OEP where they also can create and edit metadata. In a case where the local version contains less information than the remote version, pushing metadata from local to remote would overwrite the remote version. The same is true vice versa when importing metadata from the OEP to local.  

That said, the workflow we currently suggest got at least 5 initial states:

1. The user does not know how a dataset will look like. Data is not yet available.
2. The user already got a complete dataset of tabular data (CSV, excel files) available locally.
3. The user already got data uploaded to the OEP.
4. The user has some data locally and some on the OEP.
5. The user already got a OMI metadata workspace and wants to extend it.

In general in case of 1. it is mandatory to first get the data, users could already start to create metadata documents using omi and enhance them once data is available. Here it is worth to mention that data must be provided in a database (relational database system) conform data. Otherwise data cant be uploaded to the OEP. 

In case 2. users we see a good starting point for using OMI. Users can use omi to create metadata files for all files using its functionality. OMI also helps with inspecting data and inferring metadata form data files. After that users already have the base set of metadata available and could go ahead with uploading the data to the OEP. They can also refine the metadata by extending the information in the metadata YAML files.

In case 3. The user should initialize a dataset using OMI and then add resources from the OEP. This will create a Dataset skeleton and add resource metadata files to the dataset. Here the metadata which is available on the OEP is imported. After that users can enhance metadata in the YAML files and then push the updated metadata back to all tables on the OEP. While working on metadata locally its important to stop editing metadata on the OEP.

In case 4. The user can initialize a new dataset from local files. This results in the YAML files structure for all files available. Then they might infer metadata from files to get a good minimal metadata set. The user can add the table resources from oep to the existing dataset using OMI. Now bot local and remote resources are available. The user now could go ahead and upload missing resources to the OEP or publish them e.g. on Zenodo to make them publicly available.

In case 5. The user can just add more resources either from file, oep or just by resource name with an empty metadata skeleton. The user also might want to integrate omi into a data pipeline then they should use the build system omi provides. The YAML based metadata system here is still the baseline as for metadata creation manual/human inputs are required. Still the build system enables users to add more metadata during runtime of their code (like pipeline run). This enables Dynamic metadata creation/enhancements and full integration into 3rd party code.

## OMI installation

Currently latest functionality is only available on GitHub in the `dev` branch. In general omi is available on PyPi.

Get code from GitHub

```bash
# navigate into your github repo´s directory
cd github

git clone https://github.com/OpenEnergyPlatform/omi.git

```

Create python environment

```bash
# navigate into your workspace directory
cd omi-workspace

# i recommend using the tool uv here but you can use your local python and pip directly
python3 -m venv .venv
source .venv/bin/activate
```

Install omi package

Option 1

```bash
# from pypi
pip install omi
```

Option 2

```bash
# from cloned github repo using dev mode installation
pip install -e ../github/omi/
```

Make sure you use at least python 3.10 as otherwise installation might fail. If you still encounter issues create a [GitHub issue](https://github.com/OpenEnergyPlatform/omi/issues/new/choose).

## OMI usage

You can use OMI either as python module to integrate certain functionality in your codebase. If you just want to use OMI´s features you can opt for the CLI tool omi provides.

The documentation on how to use omi in your codebase is missing.

In general you can use the omi modules for oemetadata:

- validation
- open data license check
- infer metadata form files
- convert metadata from previous to latest version
- get the oemetadata spec JSON artifacts: schema, template, example
- Upload / download metadata form OEP tables
- Create metadata dataset
- Use the YAML based system to manage metadata locally in dataset with multiple resources and only define information in a template which is applied to all dataset resources
- Initialize or extend dataset metadata from frictionless datapackage json files, from directories containing data files, from oep tables or add resources with empty skeleton

## The OMI-CLI offers easy access to its functionality

The  CLI entry point is:

```bash
omi ...
```

The main groups/commands are:

Try

```bash
omi --help
```

* `omi assemble` – build OEMetadata JSON from YAML.
* `omi  dataset|resources|from-json|oep-resource` – scaffold metadata.
* `omi push-oep-all` – push metadata for **all / selected** tables of a dataset.
* `omi push-oep-one` – push metadata for **one** specific table.

All commands assume a **split layout** like:

```text
metadata/
  datasets/
    my_dataset.dataset.yaml
    my_dataset.template.yaml
  resources/
    my_dataset/
      table_1.resource.yaml
      table_2.resource.yaml
```

You can initialize this setup automatically. You’ll usually set `--base-dir ./metadata`.

---

## 1. Assembling OEMetadata locally

Build one OEMetadata JSON file from split YAML:

```bash
omi assemble \
  --base-dir ./metadata \
  --dataset-id my_dataset \
  --output-file ./out/my_dataset.json
```

Optional if you use a metadata index:

```bash
omi assemble \
  --base-dir ./metadata \
  --dataset-id my_dataset \
  --output-file ./out/my_dataset.json \
  --index-file ./metadata/metadata_index.yaml
```

---

## 2. Init / Scaffolding

### 2.1 Create an empty dataset skeleton

```bash
omi  dataset ./metadata my_dataset \
  --oem-version OEMetadata-2.0 \
  --resource table_1 \
  --resource table_2 \
  --overwrite
```

Creates:

* `datasets/my_dataset.dataset.yaml`
* `datasets/my_dataset.template.yaml`
* optional stub resource YAMLs for `table_1`, `table_2`.

### 2.2 Create resource stubs from files

```bash
omi  resources ./metadata my_dataset path/to/data1.csv path/to/data2.csv \
  --oem-version OEMetadata-2.0 \
  --overwrite
```

Infers schemas for CSV etc. and creates:

* `resources/my_dataset/data1.resource.yaml`
* `resources/my_dataset/data2.resource.yaml`

### 2.3 Import from existing OEMetadata JSON

```bash
omi  from-json ./metadata my_dataset ./oem.json \
  --oem-version OEMetadata-2.0 \
  --collect-common
```

* Creates dataset + template skeleton.
* Generates resource YAMLs from `oem.json`.
* Optionally hoists common fields to the template.

### 2.4 Import a single OEP table as a resource

Fetch metadata from OEP and add it as resource YAML:

```bash
omi  oep-resource ./metadata my_dataset parameter_photovoltaik_openfield145 \

```

* If `datasets/my_dataset.dataset.yaml` does **not** exist, a skeleton is created.
* A resource YAML is written to `resources/my_dataset/<resource-name>.resource.yaml`.
* Top-level OEP dataset fields are ignored.

If you **do not** want auto-creation of the dataset, use the `--no-create-dataset` option (depending on how you wired it; if you followed earlier code it’s there).

---

## 3. Pushing metadata back to OEP

### Token format

Pass the **raw token** to the CLI (e.g. `123abc...`).
The code builds the header `Authorization: Token <token>` internally.

---

### 3.1 Push metadata for **all** tables in a dataset

```bash
omi push-oep-all \
  --base-dir ./metadata \
  --dataset-id my_dataset \
  --token YOUR_OEP_TOKEN \
```

What it does:

* Assembles full OEMetadata from split YAML.
* For each `resource`:

  * builds a per-table OEMetadata that includes:

    * all dataset-level attributes,
    * exactly that one resource in `resources`.
  * sends it to `/api/v0/tables/<resource.name>/meta/`.

So the **OEP table name** must match `resource.name`.

Restrict to specific tables:

```bash
omi push-oep-all \
  --base-dir ./metadata \
  --dataset-id my_dataset \
  --token YOUR_OEP_TOKEN \
  --only-table parameter_photovoltaik_openfield145 \
  --only-table some_other_table
```

Use PUT instead of POST:

```bash
omi push-oep-all \
  --base-dir ./metadata \
  --dataset-id my_dataset \
  --token YOUR_OEP_TOKEN \
  --method PUT
```

---

### 3.2 Push metadata for **one** specific table

```bash
omi push-oep-one \
  --base-dir ./metadata \
  --dataset-id my_dataset \
  --table parameter_photovoltaik_openfield145 \
  --token YOUR_OEP_TOKEN \
```

What it does:

* Assembles full OEMetadata from split YAML.
* Finds the resource where `resource.name == "parameter_photovoltaik_openfield145"`.
* Builds a per-table OEMetadata with:

  * dataset-level attributes,
  * only that resource.
* Sends it to `/api/v0/tables/parameter_photovoltaik_openfield145/meta/`.

You can again choose PUT:

```bash
omi push-oep-one \
  --base-dir ./metadata \
  --dataset-id my_dataset \
  --table parameter_photovoltaik_openfield145 \
  --token YOUR_OEP_TOKEN \
  --method PUT
```

---

## 4. Minimal workflow examples

### A. Start from an OEP table, edit locally, push back

1. **Import OEP table metadata into local layout**

   ```bash
   omi  oep-resource ./metadata pv_bundle parameter_photovoltaik_openfield145 \
   ```

2. **Edit YAMLs**

   * Edit `datasets/pv_bundle.dataset.yaml`.
   * Edit `resources/pv_bundle/parameter_photovoltaik_openfield145.resource.yaml`.

3. **Push back just that table**

   ```bash
   omi push-oep-one \
     --base-dir ./metadata \
     --dataset-id pv_bundle \
     --table parameter_photovoltaik_openfield145 \
     --token YOUR_OEP_TOKEN \
   ```

---

### B. Manage a dataset with many tables

1. Create/maintain YAMLs for all resources under `resources/my_dataset/`.
2. When ready, push all metadata to OEP:

   ```bash
   omi push-oep-all \
     --base-dir ./metadata \
     --dataset-id my_dataset \
     --token YOUR_OEP_TOKEN \
   ```

That’s it – this should be enough to drive everything from the command line without digging into the code.
