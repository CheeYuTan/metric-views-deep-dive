-- Validation queries for the Metric Views LOD finance semantics demo.

USE CATALOG main;
USE SCHEMA metric_views_lod_demo;

-- Inspect the Metric View definition and materialization status.
DESCRIBE EXTENDED finance_metric_view;

-- Fixed LOD: global and account-category denominators.
SELECT
  region,
  account_category,
  MEASURE(actual_revenue) AS actual_revenue,
  MEASURE(pct_of_global_revenue_fixed_lod) AS pct_of_global_revenue,
  MEASURE(pct_of_account_category_revenue_fixed_lod) AS pct_of_account_category_revenue
FROM finance_metric_view
WHERE fiscal_year = 2025
GROUP BY ALL
ORDER BY region, account_category;

-- Coarser LOD: entity contribution inside region.
SELECT
  region,
  entity_name,
  MEASURE(actual_revenue) AS entity_revenue,
  MEASURE(region_revenue_excluding_entity) AS region_revenue,
  MEASURE(pct_of_region_revenue) AS pct_of_region_revenue
FROM finance_metric_view
WHERE fiscal_year = 2025
GROUP BY ALL
ORDER BY region, entity_revenue DESC;

-- Window semantics: current, YTD, rolling 12, prior-year, and YoY growth.
SELECT
  fiscal_month,
  region,
  MEASURE(current_month_revenue) AS current_month_revenue,
  MEASURE(ytd_revenue) AS ytd_revenue,
  MEASURE(rolling_12_month_revenue) AS rolling_12_month_revenue,
  MEASURE(prior_year_revenue) AS prior_year_revenue,
  MEASURE(yoy_revenue_growth_pct) AS yoy_revenue_growth_pct
FROM finance_metric_view
WHERE fiscal_month >= DATE'2025-01-01'
GROUP BY ALL
ORDER BY fiscal_month, region;

-- Semiadditive validation: balances should not be summed across months.
SELECT
  fiscal_quarter,
  entity_name,
  account_category,
  MEASURE(month_end_balance) AS month_end_balance
FROM finance_metric_view
WHERE statement_section = 'Balance Sheet'
  AND fiscal_year = 2025
GROUP BY ALL
ORDER BY fiscal_quarter, entity_name, account_category;

-- Materialization verification. Look for materialization names in the plan.
EXPLAIN EXTENDED
SELECT
  fiscal_month,
  region,
  account_category,
  MEASURE(actual_revenue) AS actual_revenue
FROM finance_metric_view
WHERE fiscal_year = 2025
GROUP BY ALL;
