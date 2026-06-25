-- Dashboard/support query: Materialization verification
-- After the materialization refresh completes, inspect the plan for materialization names.

EXPLAIN EXTENDED
SELECT
  fiscal_month,
  region,
  account_category,
  MEASURE(actual_revenue) AS actual_revenue,
  MEASURE(actual_expense) AS actual_expense
FROM main.metric_views_lod_demo.finance_metric_view
WHERE fiscal_year = 2025
GROUP BY ALL;

-- Manual refresh command if needed:
-- REFRESH MATERIALIZED VIEW main.metric_views_lod_demo.finance_metric_view;
