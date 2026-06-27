# Building Trusted Context in Databricks

Companion repository for a blog series on building trusted enterprise context in Databricks for people, BI tools, dashboards, Genie, and AI agents.

The series starts with business discovery, then moves into certified KPI definitions, advanced Metric View semantics, production performance, and glossary/operating model.

## Published Posts

### Part 1: Discover and Domains

[Building Trusted Context in Databricks Part 1: Discover and Domains](https://medium.com/@cheeyutcy/building-trusted-context-in-databricks-part-1-discover-and-domains-3a669a866779?source=friends_link&sk=738faf29e871b890470767b19a976b32)

Question answered:

```text
Where should I look?
```

Companion assets:

- `blogs/01_trusted_context_discover_domains.md`
- `blogs/sections/`
- `assets/part1_discover_domains/`
- `docs/part1_screenshot_inventory.json`
- `notebooks/deep_dives/00_risk_compliance_discover_assets.py`
- `notebooks/deep_dives/01_risk_compliance_bi_asset_catalog.py`
- `notebooks/deep_dives/03_discover_domains_programmatic_access.py`
- `apps/risk_compliance_context_app/`

### Part 4: Metric Views in Production

[Databricks Metric Views Deep Dive Part 1: Materialization Without Breaking the Semantic Layer](https://medium.com/@cheeyutcy/databricks-metric-views-deep-dive-part-1-materialization-without-breaking-the-semantic-layer-a0da85c1926a?source=friends_link&sk=ab2c03b750fdc9b6f3376ee216587bdb)

Series framing:

```text
How do trusted Metric Views stay fast?
```

Companion assets:

- `notebooks/deep_dives/00_materialization_base_tables.py`
- `notebooks/deep_dives/01_materialization_deep_dive.py`
- `assets/query_profiles/`

## Planned Posts

### Part 2: Metric Views as the Certified KPI Layer

Status: placeholder / draft assets in progress.

Question answered:

```text
Which KPI definition should I trust?
```

Draft assets:

- `blogs/02_metric_views_certified_kpi_layer.md`
- `blogs/part2_sections/`
- `notebooks/deep_dives/02_metric_views_certified_kpi_layer.py`

### Part 3: Advanced Metric Semantics

Status: placeholder / draft assets in progress.

Question answered:

```text
How should the metric calculate?
```

Draft assets:

- `notebooks/deep_dives/02_level_of_detail_deep_dive.py`

Planned topics:

- Level of detail: "percent of what?"
- Window semantics
- Agent metadata

## Suggested Run Order

For Part 1 Risk and Compliance demo assets:

1. `notebooks/deep_dives/00_risk_compliance_discover_assets.py`
2. `notebooks/deep_dives/01_risk_compliance_bi_asset_catalog.py`
3. `notebooks/deep_dives/03_discover_domains_programmatic_access.py`

For Part 4 materialization:

1. `notebooks/deep_dives/00_materialization_base_tables.py`
2. `notebooks/deep_dives/01_materialization_deep_dive.py`
