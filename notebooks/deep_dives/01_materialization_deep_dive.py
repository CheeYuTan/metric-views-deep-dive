# Databricks notebook source
# MAGIC %md
# MAGIC # Deep Dive 01 - Metric View Materialization
# MAGIC
# MAGIC This notebook supports the first article in the deep-dive series.
# MAGIC
# MAGIC It focuses only on **materialization for Metric Views**.
# MAGIC
# MAGIC Prerequisite:
# MAGIC
# MAGIC Run `00_materialization_base_tables` first. That notebook creates:
# MAGIC
# MAGIC - `mat_fact_finance_daily`: large daily finance fact table
# MAGIC - `mat_dim_*`: dimensions
# MAGIC - `mat_dim_*`: dimension tables that the Metric View joins to the fact table
# MAGIC
# MAGIC Why a separate setup notebook?
# MAGIC
# MAGIC Materialization is a performance feature. A tiny dataset hides the point. This deep dive uses a larger fact/dimension model so the optimizer rewrite is easier to reason about.

# COMMAND ----------

from time import perf_counter
import time

dbutils.widgets.text("catalog", "lakemeter_catalog", "Catalog")
dbutils.widgets.text("schema", "metric_views_lod_demo", "Schema")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

spark.sql(f"USE CATALOG `{catalog}`")
spark.sql(f"USE SCHEMA `{schema}`")

base_source = f"{catalog}.{schema}.mat_fact_finance_daily"
base_mv = f"{catalog}.{schema}.mat_finance_metric_view"
full_mat_mv = f"{catalog}.{schema}.mat_finance_metric_view_materialized"
agg_only_mv = f"{catalog}.{schema}.mat_finance_metric_view_agg_only"

print(f"Base fact source: {base_source}")
print(f"Base Metric View: {base_mv}")
print(f"Full materialized Metric View: {full_mat_mv}")
print(f"Aggregated-only Metric View: {agg_only_mv}")

# COMMAND ----------

def render_mermaid(diagram: str) -> None:
    displayHTML(
        f"""
        <div class="mermaid">
        {diagram}
        </div>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <script>
        mermaid.initialize({{startOnLoad: false, securityLevel: "loose"}});
        mermaid.run();
        </script>
        """
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## What Materialization Does
# MAGIC
# MAGIC Materialization lets the Metric View stay the **business contract**, while Databricks manages physical acceleration behind it.
# MAGIC
# MAGIC Key idea:
# MAGIC
# MAGIC The user still queries `MEASURE(revenue)`. The optimizer decides whether to read from an aggregated materialization, an unaggregated materialization, or the source.

# COMMAND ----------

render_mermaid(
    """
flowchart TB
  USER["User query<br/>SELECT ... MEASURE(...)"]
  MV["Metric View<br/>fields + measures"]
  PIPE["Managed Lakeflow pipeline"]
  UNAGG["Unaggregated materialization<br/>prepared source snapshot"]
  AGG["Aggregated materialization<br/>precomputed dashboard grain"]
  OPT["Optimizer<br/>aggregate-aware rewrite"]

  MV --> PIPE
  PIPE --> UNAGG
  PIPE --> AGG
  USER --> OPT
  OPT --> AGG
  OPT --> UNAGG
  OPT --> MV
"""
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Requirements and Status
# MAGIC
# MAGIC Materialization for Metric Views is documented as **Public Preview**.
# MAGIC
# MAGIC Requirements and caveats to teach explicitly:
# MAGIC
# MAGIC - Serverless compute must be enabled because Lakeflow Spark Declarative Pipelines maintain the materializations.
# MAGIC - A SQL warehouse or compute resource must run a supported runtime.
# MAGIC - `mode` is currently `relaxed`.
# MAGIC - Refresh has a lifecycle and can be asynchronous.
# MAGIC - Queries may see different freshness depending on whether they hit a materialization or fall back to source.
# MAGIC - RLS, column masks, ABAC policies, and invoker-dependent expressions are restricted.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create the Non-Materialized Metric View
# MAGIC
# MAGIC This is the semantic contract. It has no materialization block.

# COMMAND ----------

spark.sql(
    f"""
CREATE OR REPLACE VIEW {base_mv}
WITH METRICS
LANGUAGE YAML
AS $$
version: 1.1
comment: |-
  Non-materialized finance Metric View for materialization comparison.
source: {base_source}
joins:
  - name: calendar
    source: {catalog}.{schema}.mat_dim_calendar
    on: source.transaction_date = calendar.calendar_date
  - name: entity
    source: {catalog}.{schema}.mat_dim_entity
    on: source.entity_id = entity.entity_id
  - name: product
    source: {catalog}.{schema}.mat_dim_product
    on: source.product_id = product.product_id
  - name: segment
    source: {catalog}.{schema}.mat_dim_segment
    on: source.segment_id = segment.segment_id
  - name: account
    source: {catalog}.{schema}.mat_dim_account
    on: source.account_id = account.account_id
fields:
  - name: fiscal_year
    expr: calendar.fiscal_year
  - name: fiscal_month
    expr: calendar.fiscal_month
  - name: fiscal_quarter
    expr: calendar.fiscal_quarter
  - name: region
    expr: entity.region
  - name: entity_name
    expr: entity.entity_name
  - name: country
    expr: entity.country
  - name: product_family
    expr: product.product_family
  - name: product_name
    expr: product.product_name
  - name: segment_group
    expr: segment.segment_group
  - name: account_category
    expr: account.account_category
  - name: sales_motion
    expr: CASE
      WHEN product.product_family = 'Digital Platforms' AND segment.segment_group = 'Enterprise' THEN 'Strategic Platform'
      WHEN product.product_family = 'Analytics' THEN 'Analytics Motion'
      ELSE 'Standard Motion'
      END
measures:
  - name: revenue
    expr: SUM(amount) FILTER (WHERE account.account_category = 'Revenue')
    display_name: Revenue
  - name: cogs
    expr: SUM(amount) FILTER (WHERE account.account_category = 'COGS')
    display_name: COGS
  - name: opex
    expr: SUM(amount) FILTER (WHERE account.account_category = 'Opex')
    display_name: Opex
  - name: gross_profit
    expr: MEASURE(revenue) - MEASURE(cogs)
    display_name: Gross Profit
  - name: ebitda
    expr: MEASURE(revenue) - MEASURE(cogs) - MEASURE(opex)
    display_name: EBITDA
  - name: transaction_count
    expr: COUNT(DISTINCT transaction_id)
    display_name: Transaction Count
  - name: unique_customers
    expr: COUNT(DISTINCT customer_id)
    display_name: Unique Customers
  - name: revenue_per_customer
    expr: MEASURE(revenue) / NULLIF(MEASURE(unique_customers), 0)
    display_name: Revenue per Customer
$$
"""
)

display(spark.sql(f"DESCRIBE EXTENDED {base_mv}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Materialized Variant With Both Types
# MAGIC
# MAGIC This view demonstrates both materialization types:
# MAGIC
# MAGIC - `semantic_snapshot`: unaggregated materialization for expensive source preparation.
# MAGIC - `month_region_product_account`: aggregated materialization for common dashboard grains.
# MAGIC
# MAGIC Aggregated materialization design:
# MAGIC
# MAGIC - Include common `GROUP BY` fields.
# MAGIC - Include filter fields such as `fiscal_year`.
# MAGIC - Materialize at the most detailed grain needed for expected rollups.
# MAGIC - Use additive measures for rollup matching.

# COMMAND ----------

spark.sql(
    f"""
CREATE OR REPLACE VIEW {full_mat_mv}
WITH METRICS
LANGUAGE YAML
AS $$
version: 1.1
comment: |-
  Materialized Metric View with unaggregated and aggregated materializations.
source: {base_mv}
fields:
  - name: fiscal_year
    expr: fiscal_year
  - name: fiscal_month
    expr: fiscal_month
  - name: fiscal_quarter
    expr: fiscal_quarter
  - name: region
    expr: region
  - name: entity_name
    expr: entity_name
  - name: product_family
    expr: product_family
  - name: account_category
    expr: account_category
  - name: sales_motion
    expr: sales_motion
measures:
  - name: revenue
    expr: MEASURE(revenue)
  - name: cogs
    expr: MEASURE(cogs)
  - name: opex
    expr: MEASURE(opex)
  - name: ebitda
    expr: MEASURE(ebitda)
  - name: transaction_count
    expr: MEASURE(transaction_count)
  - name: unique_customers
    expr: MEASURE(unique_customers)
materialization:
  schedule: every 6 hours
  mode: relaxed
  materialized_views:
    - name: semantic_snapshot
      type: unaggregated
    - name: month_region_product_account
      type: aggregated
      dimensions:
        - fiscal_year
        - fiscal_month
        - region
        - product_family
        - account_category
      measures:
        - revenue
        - cogs
        - opex
$$
"""
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Wait for Refresh
# MAGIC
# MAGIC Materializations must finish materializing before query rewrite can use them.

# COMMAND ----------

def latest_refresh_status(metric_view_name: str) -> str | None:
    rows = spark.sql(f"DESCRIBE EXTENDED {metric_view_name}").collect()
    for row in rows:
        if row["col_name"] == "Latest Refresh Status":
            return row["data_type"]
    return None


deadline = time.time() + 900
status = latest_refresh_status(full_mat_mv)
while status != "Succeeded" and time.time() < deadline:
    print(f"Waiting for refresh. Current status: {status}")
    time.sleep(15)
    status = latest_refresh_status(full_mat_mv)

if status != "Succeeded":
    raise TimeoutError(f"Materialization refresh did not succeed. Last status: {status}")

display(spark.sql(f"DESCRIBE EXTENDED {full_mat_mv}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Automatic Query Rewrite: The Decision Tree
# MAGIC
# MAGIC The key feature is not just that materialized data exists. The key feature is that the optimizer can automatically choose the best materialized path for a Metric View query.
# MAGIC
# MAGIC Databricks documents the rewrite order as:
# MAGIC
# MAGIC 1. **Exact match**: use a materialization with the same grouping dimensions and requested measures.
# MAGIC 2. **Rollup match**: use a more detailed aggregate materialization and roll it up, if measures are additive.
# MAGIC 3. **Unaggregated match**: use the prepared source snapshot if no aggregate can serve the query.
# MAGIC 4. **Source fallback**: read from the original source if no materialization can serve the query.
# MAGIC
# MAGIC The rest of this notebook tests each path with `EXPLAIN EXTENDED`.

# COMMAND ----------

render_mermaid(
    """
flowchart TB
  Q["Metric View query"]
  E{"Exact aggregate match?"}
  R{"Rollup from aggregate possible?"}
  U{"Unaggregated materialization exists?"}
  S["Read source tables/view"]
  EXACT["Use aggregated materialization<br/>exact match"]
  ROLLUP["Use aggregated materialization<br/>rollup match"]
  UNAGG["Use unaggregated materialization<br/>prepared source snapshot"]

  Q --> E
  E -->|yes| EXACT
  E -->|no| R
  R -->|yes| ROLLUP
  R -->|no| U
  U -->|yes| UNAGG
  U -->|no| S
"""
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Compare Query Paths
# MAGIC
# MAGIC This is directional. Cache and warehouse state affect timing.
# MAGIC
# MAGIC The stronger proof is in the query plans below.

# COMMAND ----------

manual_sql = f"""
SELECT
  c.fiscal_year,
  c.fiscal_month,
  e.region,
  p.product_family,
  a.account_category,
  SUM(f.amount) FILTER (WHERE a.account_category = 'Revenue') AS revenue
FROM {catalog}.{schema}.mat_fact_finance_daily f
JOIN {catalog}.{schema}.mat_dim_calendar c
  ON f.transaction_date = c.calendar_date
JOIN {catalog}.{schema}.mat_dim_entity e
  ON f.entity_id = e.entity_id
JOIN {catalog}.{schema}.mat_dim_product p
  ON f.product_id = p.product_id
JOIN {catalog}.{schema}.mat_dim_account a
  ON f.account_id = a.account_id
WHERE c.fiscal_year = 2025
GROUP BY ALL
"""

base_mv_sql = f"""
SELECT
  fiscal_year,
  fiscal_month,
  region,
  product_family,
  account_category,
  MEASURE(revenue) AS revenue
FROM {base_mv}
WHERE fiscal_year = 2025
GROUP BY ALL
"""

mat_mv_sql = f"""
SELECT
  fiscal_year,
  fiscal_month,
  region,
  product_family,
  account_category,
  MEASURE(revenue) AS revenue
FROM {full_mat_mv}
WHERE fiscal_year = 2025
GROUP BY ALL
"""

def timed_count(label: str, query: str) -> tuple[str, int, float]:
    start = perf_counter()
    rows = spark.sql(query).collect()
    elapsed = perf_counter() - start
    return label, len(rows), elapsed

display(
    spark.createDataFrame(
        [
            timed_count("manual_source_grouping", manual_sql),
            timed_count("base_metric_view", base_mv_sql),
            timed_count("materialized_metric_view", mat_mv_sql),
        ],
        ["query_pattern", "row_count", "elapsed_seconds"],
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exact Match, Rollup Match, and Unaggregated Fallback

# COMMAND ----------

render_mermaid(
    """
flowchart TB
  EXACT["Exact match<br/>same dimensions + subset of measures"]
  ROLLUP["Rollup match<br/>fewer dimensions + additive measures"]
  UNAGG["Unaggregated fallback<br/>non-additive or varied query shape"]

  EXACT --> AGG["month_region_product_account"]
  ROLLUP --> AGG
  UNAGG --> SNAP["semantic_snapshot"]
"""
)

# COMMAND ----------

rewrite_queries = {
    "exact_match": {
        "expected": "month_region_product_account",
        "sql": f"""
          SELECT fiscal_year, fiscal_month, region, product_family, account_category, MEASURE(revenue) AS revenue
          FROM {full_mat_mv}
          WHERE fiscal_year = 2025
          GROUP BY ALL
        """,
    },
    "rollup_match": {
        "expected": "month_region_product_account",
        "sql": f"""
          SELECT fiscal_year, fiscal_month, region, MEASURE(revenue) AS revenue
          FROM {full_mat_mv}
          WHERE fiscal_year = 2025
          GROUP BY ALL
        """,
    },
    "unaggregated_fallback_for_distinct": {
        "expected": "semantic_snapshot",
        "sql": f"""
          SELECT fiscal_year, fiscal_month, region, MEASURE(unique_customers) AS unique_customers
          FROM {full_mat_mv}
          WHERE fiscal_year = 2025
          GROUP BY ALL
        """,
    },
}

evidence = []
for scenario, config in rewrite_queries.items():
    plan = "\n".join(row[0] for row in spark.sql(f"EXPLAIN EXTENDED {config['sql']}").collect())
    materialization_lines = [line.strip() for line in plan.splitlines() if "__materialization_mat_" in line]
    evidence.append(
        (
            scenario,
            config["expected"],
            config["expected"] in plan,
            "\n".join(materialization_lines[:3]),
        )
    )

evidence_df = spark.createDataFrame(
    evidence,
    ["scenario", "expected_materialization", "used_expected_materialization", "evidence_lines"],
)
display(evidence_df)

failures = [row["scenario"] for row in evidence_df.collect() if not row["used_expected_materialization"]]
if failures:
    raise AssertionError(f"Materialization expectations failed: {failures}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Source Fallback
# MAGIC
# MAGIC To show true source fallback, create an aggregated-only materialized Metric View.
# MAGIC
# MAGIC Because it has no unaggregated materialization, a query that cannot use the aggregate must fall back to the source.

# COMMAND ----------

spark.sql(
    f"""
CREATE OR REPLACE VIEW {agg_only_mv}
WITH METRICS
LANGUAGE YAML
AS $$
version: 1.1
source: {base_mv}
fields:
  - name: fiscal_year
    expr: fiscal_year
  - name: fiscal_month
    expr: fiscal_month
  - name: region
    expr: region
  - name: product_family
    expr: product_family
  - name: account_category
    expr: account_category
measures:
  - name: revenue
    expr: MEASURE(revenue)
  - name: unique_customers
    expr: MEASURE(unique_customers)
materialization:
  schedule: every 6 hours
  mode: relaxed
  materialized_views:
    - name: revenue_only_aggregate
      type: aggregated
      dimensions:
        - fiscal_year
        - fiscal_month
        - region
        - product_family
        - account_category
      measures:
        - revenue
$$
"""
)

deadline = time.time() + 900
status = latest_refresh_status(agg_only_mv)
while status != "Succeeded" and time.time() < deadline:
    print(f"Waiting for aggregated-only refresh. Current status: {status}")
    time.sleep(15)
    status = latest_refresh_status(agg_only_mv)

if status != "Succeeded":
    raise TimeoutError(f"Aggregated-only refresh did not succeed. Last status: {status}")

source_fallback_plan = "\n".join(
    row[0]
    for row in spark.sql(
        f"""
EXPLAIN EXTENDED
SELECT fiscal_year, fiscal_month, region, MEASURE(unique_customers) AS unique_customers
FROM {agg_only_mv}
WHERE fiscal_year = 2025
GROUP BY ALL
"""
    ).collect()
)

print(source_fallback_plan)
assert "revenue_only_aggregate" not in source_fallback_plan

# COMMAND ----------

# MAGIC %md
# MAGIC ## Query Rewrite Mode: Why `relaxed` Matters
# MAGIC
# MAGIC The materialization block uses:
# MAGIC
# MAGIC ```yaml
# MAGIC materialization:
# MAGIC   mode: relaxed
# MAGIC ```
# MAGIC
# MAGIC In `relaxed` mode, the optimizer checks whether a materialization has the fields and measures needed to answer the query. It does **not** fully validate every freshness or session setting concern before rewrite.
# MAGIC
# MAGIC Practical implication:
# MAGIC
# MAGIC - A query that matches a materialization uses the last successful refresh.
# MAGIC - A query that does not match can fall back to live source data.
# MAGIC - If consistency matters more than absolute freshness, an unaggregated materialization can help keep varied query shapes on the same prepared snapshot.
# MAGIC - Align the refresh schedule with the upstream source pipeline.

# COMMAND ----------

render_mermaid(
    """
flowchart LR
  Q["Query"]
  CHECK["Relaxed rewrite check<br/>Has needed fields/measures?"]
  MAT["Use last refreshed materialization"]
  SRC["Fallback to source"]

  Q --> CHECK
  CHECK -->|match| MAT
  CHECK -->|no match| SRC
"""
)

# COMMAND ----------

display(
    spark.createDataFrame(
        [
            ("Freshness", "Relaxed mode does not prove the materialization is fresher than source for every query."),
            ("SQL settings", "Relaxed mode does not fully compare settings such as timezone or ANSI mode."),
            ("Determinism", "Relaxed mode does not fully prove every materialized expression is deterministic."),
            ("Design response", "Schedule materialization after source updates, or use an unaggregated materialization for snapshot consistency."),
        ],
        ["relaxed_mode_topic", "teaching_note"],
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Additive Measure Rules
# MAGIC
# MAGIC Rollup matching depends on additive measures.
# MAGIC
# MAGIC In this notebook:
# MAGIC
# MAGIC - `revenue`, `cogs`, and `opex` are additive and can roll up from `month_region_product_account`.
# MAGIC - `unique_customers` is `COUNT(DISTINCT customer_id)`, so it is non-additive and should not roll up from partial aggregates.
# MAGIC
# MAGIC The docs list additive functions such as `SUM`, `COUNT`, `MIN`, `MAX`, boolean aggregates, and bitwise aggregates. Distinct aggregates, medians, percentiles, window measures, and measures that combine multiple aggregate functions are not good rollup candidates.

# COMMAND ----------

display(
    spark.createDataFrame(
        [
            ("revenue", "SUM via source Metric View", "Yes", "Can roll up from aggregated materialization."),
            ("cogs", "SUM via source Metric View", "Yes", "Can roll up from aggregated materialization."),
            ("opex", "SUM via source Metric View", "Yes", "Can roll up from aggregated materialization."),
            ("unique_customers", "COUNT(DISTINCT customer_id)", "No", "Needs exact match, unaggregated match, or source fallback."),
            ("revenue_per_customer", "Revenue divided by distinct customers", "No", "Composed from a non-additive denominator."),
        ],
        ["measure", "definition_pattern", "rollup_candidate", "why"],
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Materialization Lifecycle
# MAGIC
# MAGIC Important lifecycle behavior to remember:
# MAGIC
# MAGIC - Creating a Metric View with materialization triggers an initial refresh.
# MAGIC - While the refresh is running, the Metric View remains queryable, but rewrite might fall back to source until materializations are ready.
# MAGIC - Modifying the Metric View updates the definition immediately.
# MAGIC - Existing materializations are not used for rewrite until the next refresh completes.
# MAGIC - Changing the schedule does not itself trigger a refresh.
# MAGIC - If no schedule is defined, you need manual refreshes after the initial update.

# COMMAND ----------

display(
    spark.createDataFrame(
        [
            ("Create with materialization", "Managed Lakeflow pipeline is created and initial refresh starts."),
            ("Query during initial refresh", "Metric View is queryable; rewrite may fall back to source until materialization is ready."),
            ("Modify definition", "Definition changes immediately; materialization use resumes after refresh."),
            ("Change schedule", "Schedule changes do not automatically trigger a refresh."),
            ("Manual refresh", f"REFRESH MATERIALIZED VIEW {full_mat_mv}"),
        ],
        ["lifecycle_event", "behavior"],
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## How to Verify Materialization
# MAGIC
# MAGIC The docs describe two verification paths:
# MAGIC
# MAGIC 1. `DESCRIBE EXTENDED` to inspect refresh information.
# MAGIC 2. `EXPLAIN EXTENDED` or Query Profile to verify query rewrite.
# MAGIC
# MAGIC In this notebook, we use `DESCRIBE EXTENDED` and `EXPLAIN EXTENDED` because they are reproducible in notebook cells.

# COMMAND ----------

refresh_info = spark.sql(f"DESCRIBE EXTENDED {full_mat_mv}").where(
    "col_name IN ('Latest Refresh Status', 'Latest Refresh', 'Refresh Schedule')"
)
display(refresh_info)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Known Restrictions and Operational Notes
# MAGIC
# MAGIC These are not all safe to force in a demo notebook, but they are important for production design:
# MAGIC
# MAGIC - Materialization is not supported when the Metric View or source tables use RLS, column masks, or ABAC policies.
# MAGIC - Invoker-dependent expressions such as `current_user()` and `is_member()` are not supported with materialization.
# MAGIC - After materialization is created, changing owner has restrictions.
# MAGIC - For Metric Views with one-to-many joins, only exact match is eligible.
# MAGIC - Refreshing materializations incurs Lakeflow usage.
# MAGIC - Materialized views use incremental refresh whenever possible, subject to the same kinds of source and plan restrictions as regular materialized views.

# COMMAND ----------

display(
    spark.createDataFrame(
        [
            ("Security policies", "RLS, column masks, and ABAC can prevent materialization."),
            ("Invoker-dependent expressions", "Avoid current_user(), is_member(), and similar expressions in materialized Metric Views."),
            ("Ownership", "Owner changes are restricted after materialization exists."),
            ("One-to-many joins", "Only exact match is eligible for materialized Metric Views with one-to-many joins."),
            ("Billing", "Refresh work runs through managed Lakeflow pipelines and incurs usage."),
            ("Incremental refresh", "Used when possible, subject to materialized view limitations."),
        ],
        ["topic", "production_note"],
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Documentation Coverage Checklist
# MAGIC
# MAGIC This checklist maps the notebook to the major sections of the Databricks materialization documentation.

# COMMAND ----------

display(
    spark.createDataFrame(
        [
            ("Definition phase", "Create Metric View YAML with materialization block.", "Covered"),
            ("Query execution", "Compare manual, base Metric View, and materialized Metric View queries.", "Covered"),
            ("Requirements", "Serverless/Public Preview/runtime caveats explained.", "Covered"),
            ("Configuration reference", "schedule, mode, unaggregated, aggregated.", "Covered"),
            ("Relaxed mode", "Freshness/settings/determinism caveats explained.", "Covered"),
            ("Aggregated type", "month_region_product_account materialization.", "Covered"),
            ("Unaggregated type", "semantic_snapshot materialization.", "Covered"),
            ("Exact match", "Assert plan uses month_region_product_account.", "Covered"),
            ("Rollup match", "Assert plan uses month_region_product_account for coarser query.", "Covered"),
            ("Unaggregated match", "Assert non-additive query uses semantic_snapshot.", "Covered"),
            ("Source fallback", "Aggregated-only view proves no aggregate path for unique_customers.", "Covered"),
            ("Additive measures", "Table explains additive and non-additive candidates.", "Covered"),
            ("Verify materialization", "DESCRIBE EXTENDED and EXPLAIN EXTENDED examples.", "Covered"),
            ("Lifecycle", "Create, modify, schedule, manual refresh behavior explained.", "Covered"),
            ("Known restrictions", "Security, invoker-dependent, owner, one-to-many, billing notes.", "Covered"),
        ],
        ["documentation_topic", "notebook_evidence", "status"],
    )
)

