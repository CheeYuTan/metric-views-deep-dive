# Databricks Metric Views Deep Dive Part 1: Materialization

Companion repo for the article:

[Databricks Metric Views Deep Dive Part 1: Materialization Without Breaking the Semantic Layer](https://medium.com/@cheeyutcy/databricks-metric-views-deep-dive-part-1-materialization-without-breaking-the-semantic-layer-a0da85c1926a?source=friends_link&sk=ab2c03b750fdc9b6f3376ee216587bdb)

This repo contains the notebooks and screenshots needed to reproduce the materialization walkthrough.

## Included Assets

### Notebooks

- `notebooks/deep_dives/00_materialization_base_tables.py`
  - Creates the finance fact and dimension tables used in the article.
  - Generates `986,850` fact rows.

- `notebooks/deep_dives/01_materialization_deep_dive.py`
  - Creates the non-materialized Metric View.
  - Creates the materialized Metric View.
  - Demonstrates exact match, rollup match, unaggregated match, and source fallback.

### Article Draft and Sections

- `blogs/01_materialization_deep_dive.md`
- `blogs/sections/materialization_architecture.md`
- `blogs/sections/automatic_query_rewrite.md`
- `blogs/sections/materialization_closing.md`

### Query Profile Screenshots

- `assets/query_profiles/`

These screenshots are used in the article to show which materialization path Databricks selected.

## Run Order

Import and run these notebooks in Databricks:

1. `notebooks/deep_dives/00_materialization_base_tables.py`
2. `notebooks/deep_dives/01_materialization_deep_dive.py`

## Latest Validated Run

The materialization notebooks were validated on the Lakemeter Databricks workspace:

https://fe-vm-lakemeter.cloud.databricks.com/?o=335310294452632#job/352265414516911/run/30223876085768
