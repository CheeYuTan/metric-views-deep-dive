-- Dashboard page: Executive Overview

SELECT
  fiscal_month,
  region,
  MEASURE(actual_revenue) AS actual_revenue,
  MEASURE(budget_revenue) AS budget_revenue,
  MEASURE(revenue_variance) AS revenue_variance,
  MEASURE(revenue_variance_pct) AS revenue_variance_pct,
  MEASURE(ebitda) AS ebitda,
  MEASURE(ebitda_margin_pct) AS ebitda_margin_pct
FROM main.metric_views_lod_demo.finance_metric_view
WHERE fiscal_year = 2025
GROUP BY ALL
ORDER BY fiscal_month, region;
