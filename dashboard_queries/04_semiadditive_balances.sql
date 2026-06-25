-- Dashboard page: Semiadditive Balances
-- Month-end balances should aggregate across entities and products, but not across time.

SELECT
  fiscal_quarter,
  entity_name,
  product_family,
  account_category,
  MEASURE(month_end_balance) AS month_end_balance
FROM main.metric_views_lod_demo.finance_metric_view
WHERE statement_section = 'Balance Sheet'
  AND fiscal_year = 2025
GROUP BY ALL
ORDER BY fiscal_quarter, entity_name, product_family, account_category;
