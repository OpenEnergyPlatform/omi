# Conversions

This module is used to collect all existing OEMetaData version conversions. Each step in the conversion chain is stored in its own sub module. OMI supports the OEMetaData starting from v1.5.2 previous version are only supported by omi version > v1.0.0.

Since OEMetaData version 2 we decided to use patch versions to only update content or documentation parts of the metadata specification. Therefore OMI will only implement conversion steps for minor versions since they will include all minor structural changes like changing JSON key names or adding new key:value pairs. More substantial changes to the JSON structure will be reflected in a major version change this would include changing the nested structure of the metadata.
