# Data Model

The dashboard serves:

- source summary
- runs
- grouped comparison rows
- shortlist compare inputs
- tradeoff and rollup views derived from the filtered run set
- artifact listings, previews, and download paths

The run model is the same normalized local shape used by `ablation-analysis`:

- source
- project or experiment
- run_id
- name
- group
- status
- start and end time
- metrics
- params
- tags
- artifact_root
- path
- history_count

The dashboard summary also tracks:

- source_details
- warnings
- status_counts
- available_metrics
- available_variant_keys
- timestamps
