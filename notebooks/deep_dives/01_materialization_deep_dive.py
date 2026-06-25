# Databricks notebook source
# MAGIC %md
# MAGIC # Deep Dive 01 - Metric View Materialization
# MAGIC
# MAGIC This notebook supports the first article in the deep-dive series.
# MAGIC
# MAGIC Value delivered:
# MAGIC
# MAGIC - Create a materialized Metric View variant.
# MAGIC - Compare manual grouping, base Metric View, and materialized Metric View.
# MAGIC - Prove exact match, rollup match, and non-additive fallback using `EXPLAIN EXTENDED`.
# MAGIC
# MAGIC Prerequisite:
# MAGIC
# MAGIC Run:
# MAGIC
# MAGIC - `01_generate_synthetic_finance_data`
# MAGIC - `02_design_metric_view_semantic_layer`

# COMMAND ----------

from time import perf_counter
import time

dbutils.widgets.text("catalog", "lakemeter_catalog", "Catalog")
dbutils.widgets.text("schema", "metric_views_lod_demo", "Schema")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

spark.sql(f"USE CATALOG `{catalog}`")
spark.sql(f"USE SCHEMA `{schema}`")

base_view = f"{catalog}.{schema}.finance_semantic_base"
base_mv = f"{catalog}.{schema}.finance_metric_view"
mat_mv = f"{catalog}.{schema}.finance_metric_view_materialized"

print(f"Base view: {base_view}")
print(f"Base Metric View: {base_mv}")
print(f"Materialized Metric View: {mat_mv}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Architecture
# MAGIC
# MAGIC ```mermaid
# MAGIC flowchart TB
# MAGIC   BASE["finance_metric_view<br/>semantic contract"]
# MAGIC   MAT["finance_metric_view_materialized<br/>optimization layer"]
# MAGIC   PIPE["Managed Lakeflow pipeline"]
# MAGIC   SNAP["semantic_snapshot<br/>unaggregated materialization"]
# MAGIC   AGG["exec_month_region_category<br/>aggregated materialization"]
# MAGIC   USER["User query<br/>SELECT ... MEASURE(...)"]
# MAGIC   OPT["Optimizer rewrite"]
# MAGIC
# MAGIC   BASE --> MAT
# MAGIC   MAT --> PIPE
# MAGIC   PIPE --> SNAP
# MAGIC   PIPE --> AGG
# MAGIC   USER --> OPT
# MAGIC   OPT --> AGG
# MAGIC   OPT --> SNAP
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Materialized Variant
# MAGIC
# MAGIC The base Metric View stays clean and non-materialized. This materialized variant re-exposes the dashboard-facing measures and adds physical acceleration.

# COMMAND ----------

spark.sql(
    f"""
CREATE OR REPLACE VIEW {mat_mv}
WITH METRICS
LANGUAGE YAML
AS $$
version: 1.1
comment: |-
  Materialized variant of finance_metric_view for query acceleration demos.
source: {base_mv}
fields:
  - name: fiscal_year
    expr: fiscal_year
    display_name: Fiscal Year
  - name: fiscal_month
    expr: fiscal_month
    display_name: Fiscal Month
  - name: region
    expr: region
    display_name: Region
  - name: entity_name
    expr: entity_name
    display_name: Entity
  - name: product_family
    expr: product_family
    display_name: Product Family
  - name: account_category
    expr: account_category
    display_name: Account Category
  - name: statement_section
    expr: statement_section
    display_name: Statement Section
  - name: fiscal_quarter
    expr: fiscal_quarter
    display_name: Fiscal Quarter
measures:
  - name: actual_revenue
    expr: MEASURE(actual_revenue)
    display_name: Actual Revenue
  - name: actual_expense
    expr: MEASURE(actual_expense)
    display_name: Actual Expense
  - name: actual_cogs
    expr: MEASURE(actual_cogs)
    display_name: Actual COGS
  - name: actual_opex
    expr: MEASURE(actual_opex)
    display_name: Actual Opex
  - name: transaction_count
    expr: MEASURE(transaction_count)
    display_name: Transaction Count
  - name: month_end_balance
    expr: MEASURE(month_end_balance)
    display_name: Month-End Balance
materialization:
  schedule: every 6 hours
  mode: relaxed
  materialized_views:
    - name: semantic_snapshot
      type: unaggregated
    - name: exec_month_region_category
      type: aggregated
      dimensions:
        - fiscal_year
        - fiscal_month
        - region
        - account_category
      measures:
        - actual_revenue
        - actual_expense
        - actual_cogs
        - actual_opex
$$
"""
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Wait for Refresh

# COMMAND ----------

def latest_refresh_status(metric_view_name: str) -> str | None:
    rows = spark.sql(f"DESCRIBE EXTENDED {metric_view_name}").collect()
    for row in rows:
        if row["col_name"] == "Latest Refresh Status":
            return row["data_type"]
    return None

deadline = time.time() + 600
status = latest_refresh_status(mat_mv)
while status != "Succeeded" and time.time() < deadline:
    print(f"Waiting for materialization refresh. Current status: {status}")
    time.sleep(15)
    status = latest_refresh_status(mat_mv)

if status != "Succeeded":
    raise TimeoutError(f"Materialization refresh did not succeed. Last status: {status}")

display(spark.sql(f"DESCRIBE EXTENDED {mat_mv}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Compare Query Paths

# COMMAND ----------

manual_sql = f"""
SELECT
  fiscal_year,
  fiscal_month,
  region,
  account_category,
  SUM(amount) FILTER (WHERE source_grain = 'GL' AND scenario_name = 'Actual' AND account_category = 'Revenue') AS actual_revenue
FROM {base_view}
WHERE fiscal_year = 2025
GROUP BY ALL
"""

base_mv_sql = f"""
SELECT
  fiscal_year,
  fiscal_month,
  region,
  account_category,
  MEASURE(actual_revenue) AS actual_revenue
FROM {base_mv}
WHERE fiscal_year = 2025
GROUP BY ALL
"""

mat_mv_sql = f"""
SELECT
  fiscal_year,
  fiscal_month,
  region,
  account_category,
  MEASURE(actual_revenue) AS actual_revenue
FROM {mat_mv}
WHERE fiscal_year = 2025
GROUP BY ALL
"""

def timed_count(label: str, query: str) -> tuple[str, int, float]:
    start = perf_counter()
    rows = spark.sql(query).collect()
    return label, len(rows), perf_counter() - start

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
# MAGIC ## Assert Optimizer Rewrite Paths

# COMMAND ----------

rewrite_queries = {
    "exact_match": {
        "expected": "exec_month_region_category",
        "sql": f"""
          SELECT fiscal_year, fiscal_month, region, account_category, MEASURE(actual_revenue) AS actual_revenue
          FROM {mat_mv}
          WHERE fiscal_year = 2025
          GROUP BY ALL
        """,
    },
    "rollup_match": {
        "expected": "exec_month_region_category",
        "sql": f"""
          SELECT fiscal_year, fiscal_month, region, MEASURE(actual_revenue) AS actual_revenue
          FROM {mat_mv}
          WHERE fiscal_year = 2025
          GROUP BY ALL
        """,
    },
    "non_additive_fallback": {
        "expected": "semantic_snapshot",
        "sql": f"""
          SELECT fiscal_year, fiscal_month, region, MEASURE(transaction_count) AS transaction_count
          FROM {mat_mv}
          WHERE fiscal_year = 2025
          GROUP BY ALL
        """,
    },
}

evidence = []
for scenario, config in rewrite_queries.items():
    plan = "\n".join(row[0] for row in spark.sql(f"EXPLAIN EXTENDED {config['sql']}").collect())
    evidence_lines = [line.strip() for line in plan.splitlines() if "__materialization_mat_" in line]
    evidence.append((scenario, config["expected"], config["expected"] in plan, "\n".join(evidence_lines[:3])))

evidence_df = spark.createDataFrame(evidence, ["scenario", "expected_materialization", "used_expected", "evidence_lines"])
display(evidence_df)

failures = [row["scenario"] for row in evidence_df.collect() if not row["used_expected"]]
if failures:
    raise AssertionError(f"Materialization expectations failed: {failures}")

