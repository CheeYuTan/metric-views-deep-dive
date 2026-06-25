# Databricks notebook source
# MAGIC %md
# MAGIC # Deep Dive 02 - Level of Detail Expressions
# MAGIC
# MAGIC This notebook supports the LOD article.
# MAGIC
# MAGIC Value delivered:
# MAGIC
# MAGIC - Fixed LOD with `ANY_VALUE`.
# MAGIC - Fixed LOD filtering behavior.
# MAGIC - Coarser LOD with `range: all`.
# MAGIC - Multiple excluded fields.

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
# MAGIC ## LOD Mental Model
# MAGIC
# MAGIC ```mermaid
# MAGIC flowchart TB
# MAGIC   QUERY["Visible query grain"]
# MAGIC   NUM["Numerator at visible grain"]
# MAGIC   FIXED["Fixed denominator<br/>predefined partition"]
# MAGIC   COARSER["Coarser denominator<br/>exclude selected fields"]
# MAGIC   RATIO["Business ratio"]
# MAGIC
# MAGIC   QUERY --> NUM
# MAGIC   NUM --> RATIO
# MAGIC   FIXED --> RATIO
# MAGIC   COARSER --> RATIO
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fixed LOD: Percent of Global Revenue
# MAGIC
# MAGIC This query uses fiscal-year-aware fixed LOD denominators. That matters because the numerator is filtered to fiscal year 2025.

# COMMAND ----------

display(
    spark.sql(
        f"""
SELECT
  region,
  account_category,
  MEASURE(actual_revenue) AS actual_revenue,
  MEASURE(pct_of_global_revenue_year_fixed_lod) AS pct_of_global_revenue_2025,
  MEASURE(pct_of_account_category_revenue_year_fixed_lod) AS pct_of_account_category_revenue_2025
FROM {mv}
WHERE fiscal_year = 2025
GROUP BY ALL
ORDER BY region, account_category
"""
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fixed LOD Filtering Behavior
# MAGIC
# MAGIC The query filters to APJ.
# MAGIC
# MAGIC `pct_of_global_revenue_year_fixed_lod` uses the fiscal-year global denominator.
# MAGIC
# MAGIC `pct_of_apj_revenue_year_fixed_lod` uses a fiscal-year-aware APJ denominator because fiscal year and APJ are encoded in the LOD field expression.

# COMMAND ----------

display(
    spark.sql(
        f"""
SELECT
  region,
  product_family,
  MEASURE(actual_revenue) AS actual_revenue,
  MEASURE(pct_of_global_revenue_year_fixed_lod) AS pct_of_global_revenue_2025,
  MEASURE(pct_of_apj_revenue_year_fixed_lod) AS pct_of_apj_revenue_2025
FROM {mv}
WHERE fiscal_year = 2025
  AND region = 'APJ'
GROUP BY ALL
ORDER BY product_family
"""
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Sanity Check
# MAGIC
# MAGIC APJ product-family percentages should sum to approximately 1.0 because the denominator is APJ revenue for fiscal year 2025.

# COMMAND ----------

apj_pct_total = spark.sql(
    f"""
SELECT
  SUM(pct_of_apj_revenue_2025) AS pct_total
FROM (
  SELECT
    product_family,
    MEASURE(pct_of_apj_revenue_year_fixed_lod) AS pct_of_apj_revenue_2025
  FROM {mv}
  WHERE fiscal_year = 2025
    AND region = 'APJ'
  GROUP BY ALL
)
"""
).collect()[0]["pct_total"]

print(f"APJ product-family percentage total: {apj_pct_total}")
assert abs(apj_pct_total - 1.0) < 0.0001

# COMMAND ----------

# MAGIC %md
# MAGIC ## Coarser LOD: Percent of Region Revenue
# MAGIC
# MAGIC This denominator excludes `entity_name` from the query grain.

# COMMAND ----------

display(
    spark.sql(
        f"""
SELECT
  region,
  entity_name,
  MEASURE(actual_revenue) AS entity_revenue,
  MEASURE(region_revenue_excluding_entity) AS region_revenue,
  MEASURE(pct_of_region_revenue) AS pct_of_region_revenue
FROM {mv}
WHERE fiscal_year = 2025
GROUP BY ALL
ORDER BY region, entity_revenue DESC
"""
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Sanity Check
# MAGIC
# MAGIC Entity contribution percentages should sum to 1.0 within each region.

# COMMAND ----------

display(
    spark.sql(
        f"""
SELECT
  region,
  SUM(pct_of_region_revenue) AS pct_total
FROM (
  SELECT
    region,
    entity_name,
    MEASURE(pct_of_region_revenue) AS pct_of_region_revenue
  FROM {mv}
  WHERE fiscal_year = 2025
  GROUP BY ALL
)
GROUP BY region
ORDER BY region
"""
    )
)

region_totals = spark.sql(
    f"""
SELECT
  region,
  SUM(pct_of_region_revenue) AS pct_total
FROM (
  SELECT
    region,
    entity_name,
    MEASURE(pct_of_region_revenue) AS pct_of_region_revenue
  FROM {mv}
  WHERE fiscal_year = 2025
  GROUP BY ALL
)
GROUP BY region
"""
).collect()

for row in region_totals:
    assert abs(row["pct_total"] - 1.0) < 0.0001, f"{row['region']} total was {row['pct_total']}"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Coarser LOD With Multiple Excluded Fields

# COMMAND ----------

display(
    spark.sql(
        f"""
SELECT
  region,
  entity_name,
  product_family,
  MEASURE(actual_revenue) AS actual_revenue,
  MEASURE(revenue_excluding_entity_and_product_family) AS broader_revenue,
  MEASURE(pct_of_entity_product_visible_total) AS pct_of_visible_total
FROM {mv}
WHERE fiscal_year = 2025
  AND region = 'APJ'
GROUP BY ALL
ORDER BY entity_name, product_family
"""
    )
)

