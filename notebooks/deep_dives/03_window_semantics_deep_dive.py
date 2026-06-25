# Databricks notebook source
# MAGIC %md
# MAGIC # Deep Dive 03 - Window Semantics
# MAGIC
# MAGIC This notebook supports the window semantics article.
# MAGIC
# MAGIC Value delivered:
# MAGIC
# MAGIC - Current, cumulative, YTD, rolling, leading, and prior-year windows.
# MAGIC - Inclusive versus exclusive trailing windows.
# MAGIC - Semiadditive balances.
# MAGIC - Date hierarchy design.

# COMMAND ----------

dbutils.widgets.text("catalog", "lakemeter_catalog", "Catalog")
dbutils.widgets.text("schema", "metric_views_lod_demo", "Schema")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

spark.sql(f"USE CATALOG `{catalog}`")
spark.sql(f"USE SCHEMA `{schema}`")

mv = f"{catalog}.{schema}.finance_metric_view"
print(f"Metric View: {mv}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Window Measure Anatomy
# MAGIC
# MAGIC ```mermaid
# MAGIC flowchart TB
# MAGIC   ORDER["order<br/>fiscal_month"]
# MAGIC   RANGE["range<br/>current / cumulative / trailing / leading"]
# MAGIC   SEMI["semiadditive<br/>last / first"]
# MAGIC   OFFSET["offset<br/>-12 month"]
# MAGIC   MEASURE["window measure"]
# MAGIC
# MAGIC   ORDER --> MEASURE
# MAGIC   RANGE --> MEASURE
# MAGIC   SEMI --> MEASURE
# MAGIC   OFFSET --> MEASURE
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Current, Running, YTD, Rolling, Prior Year, and Leading

# COMMAND ----------

display(
    spark.sql(
        f"""
SELECT
  fiscal_month,
  region,
  MEASURE(current_month_revenue) AS current_month_revenue,
  MEASURE(running_total_revenue) AS running_total_revenue,
  MEASURE(ytd_revenue) AS ytd_revenue,
  MEASURE(rolling_12_month_revenue) AS rolling_12_month_revenue,
  MEASURE(next_month_revenue) AS next_month_revenue,
  MEASURE(prior_year_revenue) AS prior_year_revenue,
  MEASURE(yoy_revenue_growth_pct) AS yoy_revenue_growth_pct
FROM {mv}
WHERE fiscal_month >= DATE'2025-01-01'
GROUP BY ALL
ORDER BY fiscal_month, region
"""
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Sanity Checks
# MAGIC
# MAGIC Things to verify:
# MAGIC
# MAGIC - January YTD equals January current-month revenue.
# MAGIC - Prior-year revenue is populated for 2025 because the dataset includes 2024.
# MAGIC - YoY growth is calculated from current month and prior year.

# COMMAND ----------

checks = spark.sql(
    f"""
SELECT
  region,
  MEASURE(current_month_revenue) AS current_month_revenue,
  MEASURE(ytd_revenue) AS ytd_revenue,
  MEASURE(prior_year_revenue) AS prior_year_revenue
FROM {mv}
WHERE fiscal_month = DATE'2025-01-01'
GROUP BY ALL
ORDER BY region
"""
)
display(checks)

for row in checks.collect():
    assert abs(row["current_month_revenue"] - row["ytd_revenue"]) < 0.0001
    assert row["prior_year_revenue"] is not None

# COMMAND ----------

# MAGIC %md
# MAGIC ## Inclusive vs Exclusive Trailing Windows

# COMMAND ----------

display(
    spark.sql(
        f"""
SELECT
  fiscal_month,
  region,
  MEASURE(current_month_revenue) AS current_month_revenue,
  MEASURE(trailing_3_month_revenue_exclusive) AS trailing_3_exclusive,
  MEASURE(trailing_3_month_revenue_inclusive) AS trailing_3_inclusive
FROM {mv}
WHERE fiscal_month BETWEEN DATE'2025-01-01' AND DATE'2025-06-01'
GROUP BY ALL
ORDER BY fiscal_month, region
"""
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Sanity Check
# MAGIC
# MAGIC The inclusive and exclusive trailing windows should differ once enough months exist, because inclusive includes the anchor month while exclusive excludes it and looks one period further back.

# COMMAND ----------

diffs = spark.sql(
    f"""
SELECT
  fiscal_month,
  region,
  MEASURE(trailing_3_month_revenue_exclusive) AS trailing_3_exclusive,
  MEASURE(trailing_3_month_revenue_inclusive) AS trailing_3_inclusive
FROM {mv}
WHERE fiscal_month BETWEEN DATE'2025-01-01' AND DATE'2025-06-01'
GROUP BY ALL
"""
)
display(diffs)

non_zero_differences = [
    row
    for row in diffs.collect()
    if row["trailing_3_inclusive"] is not None
    and row["trailing_3_exclusive"] is not None
    and abs(row["trailing_3_inclusive"] - row["trailing_3_exclusive"]) > 0.0001
]
assert non_zero_differences, "Expected inclusive and exclusive trailing windows to differ for at least one row."

# COMMAND ----------

# MAGIC %md
# MAGIC ## Semiadditive Balances
# MAGIC
# MAGIC Balances should aggregate across entities and products, but not across time.

# COMMAND ----------

display(
    spark.sql(
        f"""
SELECT
  fiscal_quarter,
  entity_name,
  account_category,
  MEASURE(month_end_balance) AS month_end_balance
FROM {mv}
WHERE statement_section = 'Balance Sheet'
  AND fiscal_year = 2025
GROUP BY ALL
ORDER BY fiscal_quarter, entity_name, account_category
"""
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Sanity Check
# MAGIC
# MAGIC A naive quarter sum of monthly balances should differ from the semiadditive Metric View result. This is why the semantic layer matters.

# COMMAND ----------

display(
    spark.sql(
        f"""
SELECT
  b.fiscal_quarter,
  b.entity_name,
  b.account_category,
  b.metric_view_balance,
  n.naive_quarter_sum,
  n.naive_quarter_sum - b.metric_view_balance AS overstatement
FROM (
  SELECT
    fiscal_quarter,
    entity_name,
    account_category,
    MEASURE(month_end_balance) AS metric_view_balance
  FROM {mv}
  WHERE statement_section = 'Balance Sheet'
    AND fiscal_year = 2025
  GROUP BY ALL
) b
JOIN (
  SELECT
    fiscal_quarter,
    entity_name,
    account_category,
    SUM(balance_amount) AS naive_quarter_sum
  FROM {catalog}.{schema}.finance_semantic_base
  WHERE source_grain = 'BALANCE'
    AND fiscal_year = 2025
  GROUP BY ALL
) n
ON b.fiscal_quarter = n.fiscal_quarter
AND b.entity_name = n.entity_name
AND b.account_category = n.account_category
ORDER BY b.fiscal_quarter, b.entity_name, b.account_category
"""
    )
)

overstatement_rows = spark.sql(
    f"""
SELECT
  b.fiscal_quarter,
  b.entity_name,
  b.account_category,
  n.naive_quarter_sum - b.metric_view_balance AS overstatement
FROM (
  SELECT
    fiscal_quarter,
    entity_name,
    account_category,
    MEASURE(month_end_balance) AS metric_view_balance
  FROM {mv}
  WHERE statement_section = 'Balance Sheet'
    AND fiscal_year = 2025
  GROUP BY ALL
) b
JOIN (
  SELECT
    fiscal_quarter,
    entity_name,
    account_category,
    SUM(balance_amount) AS naive_quarter_sum
  FROM {catalog}.{schema}.finance_semantic_base
  WHERE source_grain = 'BALANCE'
    AND fiscal_year = 2025
  GROUP BY ALL
) n
ON b.fiscal_quarter = n.fiscal_quarter
AND b.entity_name = n.entity_name
AND b.account_category = n.account_category
"""
).collect()

assert overstatement_rows, "Expected rows for semiadditive comparison."
assert all(row["overstatement"] > 0 for row in overstatement_rows), "Naive quarter balance should overstate the semiadditive balance."

