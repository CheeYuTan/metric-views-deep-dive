# Databricks notebook source
# MAGIC %md
# MAGIC # Part 2 - Metric Views as the Certified KPI Layer
# MAGIC
# MAGIC This notebook supports the second article in the **Building Trusted Enterprise Context in Databricks** series.
# MAGIC
# MAGIC Part 1 showed how Discover and Domains help people, BI tools, and agents answer:
# MAGIC
# MAGIC > Where should I look?
# MAGIC
# MAGIC Part 2 answers the next question:
# MAGIC
# MAGIC > Which KPI definition should I trust?
# MAGIC
# MAGIC The example continues with the synthetic `Risk and Compliance` domain. It uses the Metric Views created by `00_risk_compliance_discover_assets`.

# COMMAND ----------

dbutils.widgets.text("catalog", "steven_discover_domains", "Catalog")
dbutils.widgets.text("schema", "risk_compliance_context_demo", "Schema")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
qualified_schema = f"`{catalog}`.`{schema}`"

spark.sql(f"USE CATALOG `{catalog}`")
spark.sql(f"USE SCHEMA `{schema}`")

credit_mv = f"{catalog}.{schema}.credit_risk_metrics"
fraud_mv = f"{catalog}.{schema}.fraud_risk_metrics"
exec_mv = f"{catalog}.{schema}.risk_compliance_executive_metrics"

print(f"Using schema: {catalog}.{schema}")
print(f"Credit Risk Metric View: {credit_mv}")
print(f"Fraud Risk Metric View: {fraud_mv}")
print(f"Executive Metric View: {exec_mv}")

# COMMAND ----------

def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def scalar(query: str, column: str = "value"):
    return spark.sql(query).collect()[0][column]

# COMMAND ----------

# MAGIC %md
# MAGIC ## Why Metric Views Are the Next Layer
# MAGIC
# MAGIC Discover and Domains organize the trusted context.
# MAGIC
# MAGIC Metric Views define the trusted calculations inside that context.
# MAGIC
# MAGIC In this demo:
# MAGIC
# MAGIC ```text
# MAGIC Risk and Compliance -> Credit Risk -> credit_risk_metrics
# MAGIC ```
# MAGIC
# MAGIC The source table gives us data. The Metric View gives us a governed query contract.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   table_name,
# MAGIC   table_type,
# MAGIC   comment
# MAGIC FROM information_schema.tables
# MAGIC WHERE table_catalog = '${catalog}'
# MAGIC   AND table_schema = '${schema}'
# MAGIC   AND table_name IN (
# MAGIC     'credit_risk_exposures',
# MAGIC     'credit_risk_portfolio_summary',
# MAGIC     'credit_risk_metrics',
# MAGIC     'fraud_risk_metrics',
# MAGIC     'risk_compliance_executive_metrics'
# MAGIC   )
# MAGIC ORDER BY table_name

# COMMAND ----------

# MAGIC %md
# MAGIC ## Source Data Is Not the KPI Contract
# MAGIC
# MAGIC The source table is useful, but it does not tell every downstream consumer how to calculate the KPI.
# MAGIC
# MAGIC For credit risk, a user could manually aggregate `expected_credit_loss` and `exposure_amount`. But if every dashboard writes that logic independently, definitions drift.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   product_line,
# MAGIC   risk_band,
# MAGIC   SUM(exposure_amount) AS exposure_amount,
# MAGIC   SUM(expected_credit_loss) AS expected_credit_loss,
# MAGIC   SUM(expected_credit_loss) / NULLIF(SUM(exposure_amount), 0) AS ecl_rate
# MAGIC FROM credit_risk_exposures
# MAGIC GROUP BY ALL
# MAGIC ORDER BY product_line, risk_band

# COMMAND ----------

# MAGIC %md
# MAGIC ## Metric Views Make the KPI Reusable
# MAGIC
# MAGIC With a Metric View, users query the business measure instead of rewriting the aggregation logic.
# MAGIC
# MAGIC The query is smaller, and more importantly, the metric definition is governed in Unity Catalog.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   product_line,
# MAGIC   risk_band,
# MAGIC   MEASURE(exposure_amount) AS exposure_amount,
# MAGIC   MEASURE(expected_credit_loss) AS expected_credit_loss,
# MAGIC   MEASURE(ecl_rate) AS ecl_rate
# MAGIC FROM credit_risk_metrics
# MAGIC GROUP BY ALL
# MAGIC ORDER BY product_line, risk_band

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validate the Contract
# MAGIC
# MAGIC The Metric View should produce the same results as the explicit source-table calculation.
# MAGIC
# MAGIC This check is not just a test. It is the operating model: certified KPIs should be validated.

# COMMAND ----------

comparison = spark.sql(
    """
WITH manual AS (
  SELECT
    product_line,
    risk_band,
    SUM(exposure_amount) AS exposure_amount,
    SUM(expected_credit_loss) AS expected_credit_loss,
    SUM(expected_credit_loss) / NULLIF(SUM(exposure_amount), 0) AS ecl_rate
  FROM credit_risk_exposures
  GROUP BY ALL
),
metric_view AS (
  SELECT
    product_line,
    risk_band,
    MEASURE(exposure_amount) AS exposure_amount,
    MEASURE(expected_credit_loss) AS expected_credit_loss,
    MEASURE(ecl_rate) AS ecl_rate
  FROM credit_risk_metrics
  GROUP BY ALL
)
SELECT
  COUNT(*) AS mismatches
FROM manual m
FULL OUTER JOIN metric_view v
  ON m.product_line = v.product_line
  AND m.risk_band = v.risk_band
WHERE
  ABS(COALESCE(m.exposure_amount, 0) - COALESCE(v.exposure_amount, 0)) > 0.001
  OR ABS(COALESCE(m.expected_credit_loss, 0) - COALESCE(v.expected_credit_loss, 0)) > 0.001
  OR ABS(COALESCE(m.ecl_rate, 0) - COALESCE(v.ecl_rate, 0)) > 0.000001
"""
).collect()[0]["mismatches"]

print(f"Credit risk Metric View mismatches: {comparison}")
require(comparison == 0, "Metric View results should match manual source calculation")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Certification Makes the Trust Signal Visible
# MAGIC
# MAGIC In Part 1, the domain page showed certified and deprecated assets.
# MAGIC
# MAGIC Here we verify that the Metric Views are tagged as certified and assigned to the right business context.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   table_name,
# MAGIC   tag_name,
# MAGIC   tag_value
# MAGIC FROM information_schema.table_tags
# MAGIC WHERE catalog_name = '${catalog}'
# MAGIC   AND schema_name = '${schema}'
# MAGIC   AND table_name IN (
# MAGIC     'credit_risk_metrics',
# MAGIC     'fraud_risk_metrics',
# MAGIC     'risk_compliance_executive_metrics'
# MAGIC   )
# MAGIC ORDER BY table_name, tag_name

# COMMAND ----------

certified_metric_views = scalar(
    f"""
SELECT COUNT(DISTINCT table_name) AS value
FROM `{catalog}`.information_schema.table_tags
WHERE schema_name = '{schema}'
  AND table_name IN ('credit_risk_metrics', 'fraud_risk_metrics', 'risk_compliance_executive_metrics')
  AND tag_name = 'system.certification_status'
  AND tag_value = 'certified'
"""
)

require(certified_metric_views == 3, f"Expected 3 certified Metric Views, found {certified_metric_views}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Metric Views Work Across Interfaces
# MAGIC
# MAGIC The same Metric View can support SQL users, dashboards, BI tools, and Genie Spaces.
# MAGIC
# MAGIC That is the point of treating it as the certified KPI layer. The calculation is defined once, then reused by many experiences.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   risk_area,
# MAGIC   MEASURE(exposure_amount) AS exposure_amount,
# MAGIC   MEASURE(loss_or_exposure_metric) AS loss_or_exposure_metric,
# MAGIC   MEASURE(average_risk_rate) AS average_risk_rate
# MAGIC FROM risk_compliance_executive_metrics
# MAGIC GROUP BY ALL
# MAGIC ORDER BY risk_area

# COMMAND ----------

# MAGIC %md
# MAGIC ## What This Sets Up
# MAGIC
# MAGIC This notebook deliberately stays simple.
# MAGIC
# MAGIC It does not try to cover every advanced Metric View feature. The goal is to show where Metric Views sit in the trusted-context story:
# MAGIC
# MAGIC ```text
# MAGIC Discover and Domains -> where should I look?
# MAGIC Metric Views -> which KPI definition should I trust?
# MAGIC ```
# MAGIC
# MAGIC The next step is advanced metric semantics: level of detail, window semantics, and agent metadata.

# COMMAND ----------

print("Metric Views certified KPI layer checks completed successfully.")
