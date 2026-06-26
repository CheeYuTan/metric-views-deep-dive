## Automatic Query Rewrite: Exact, Rollup, Unaggregated, and Source Fallback

Once materializations exist, users still query the Metric View.

They do **not** query the generated materialization objects directly.

For example, users write:

```sql
SELECT
  fiscal_year,
  fiscal_month,
  region,
  MEASURE(revenue) AS revenue
FROM mat_finance_metric_view_materialized
WHERE fiscal_year = 2025
GROUP BY ALL;
```

Behind the scenes, query optimization decides which physical path to use.

The decision order is:

1. Exact match
2. Rollup match
3. Unaggregated match
4. Source fallback

That means Databricks tries to use the fastest valid materialization first. If no materialization can answer the query, it falls back to the source tables.

## 1. Exact Match

Exact match happens when the query asks for the same grain that was already precomputed.

Our aggregated materialization is defined at this grain:

```text
fiscal_year + fiscal_month + region + product_family + account_category
```

So this query is an exact match:

```sql
SELECT
  fiscal_year,
  fiscal_month,
  region,
  product_family,
  account_category,
  MEASURE(revenue) AS revenue
FROM mat_finance_metric_view_materialized
WHERE fiscal_year = 2025
GROUP BY ALL;
```

After running it, open Query Profile.

You should see the query scanning the generated materialization table ending in:

```text
month_region_product_account_1
```

Screenshot:

![Exact match scans the aggregated materialization](https://raw.githubusercontent.com/CheeYuTan/metric-views-deep-dive/main/assets/query_profiles/exact_match.png)

What this shows:

Databricks does not need to perform another grouping step. The query asks for the exact same dimensions and measure that were already precomputed.

This is the cleanest materialization hit.

## 2. Rollup Match

Rollup match happens when the query asks for a coarser grain than the materialization.

This query removes `product_family` and `account_category`:

```sql
SELECT
  fiscal_year,
  fiscal_month,
  region,
  MEASURE(revenue) AS revenue
FROM mat_finance_metric_view_materialized
WHERE fiscal_year = 2025
GROUP BY ALL;
```

The query grain is now:

```text
fiscal_year + fiscal_month + region
```

The materialization grain is still:

```text
fiscal_year + fiscal_month + region + product_family + account_category
```

Because `revenue` is additive, Databricks can scan the detailed aggregate and roll it up.

Screenshot:

![Rollup match scans the same aggregate and groups again](https://raw.githubusercontent.com/CheeYuTan/metric-views-deep-dive/main/assets/query_profiles/rollup_match.png)

What this shows:

The query profile still scans:

```text
month_region_product_account_1
```

But this time there is a `Grouping Aggregate` operator above the scan.

That is the rollup. Databricks reads the detailed precomputed result and aggregates it to the requested grain.

This is why choosing the right materialized grain matters. A detailed enough aggregated materialization can serve multiple coarser queries.

## 3. Unaggregated Match

Not every measure can roll up from an aggregated materialization.

For example:

```sql
COUNT(DISTINCT customer_id)
```

Distinct counts are non-additive. You cannot calculate distinct customers by summing distinct customers from smaller groups, because the same customer can appear in multiple groups.

So this query should not use the aggregated `month_region_product_account` materialization:

```sql
SELECT
  fiscal_year,
  fiscal_month,
  region,
  MEASURE(unique_customers) AS unique_customers
FROM mat_finance_metric_view_materialized
WHERE fiscal_year = 2025
GROUP BY ALL;
```

Instead, Databricks can use the unaggregated materialization:

```text
semantic_snapshot_1
```

Screenshot:

![Unaggregated match scans semantic snapshot](https://raw.githubusercontent.com/CheeYuTan/metric-views-deep-dive/main/assets/query_profiles/unaggregated_match.png)

What this shows:

Databricks scans the prepared row-level materialization.

This avoids recomputing the fact-to-dimension joins and field expressions, while still calculating the distinct count correctly at query time.

This is the main value of unaggregated materialization: it is a broad fallback path for query shapes or measures that do not fit an aggregate materialization.

## 4. Source Fallback

Finally, what happens if no materialization can answer the query?

To demonstrate this, create a Metric View with only an aggregated materialization:

```yaml
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
```

This materialization can help with revenue queries.

But it cannot answer this distinct-customer query:

```sql
SELECT
  fiscal_year,
  fiscal_month,
  region,
  MEASURE(unique_customers) AS unique_customers
FROM mat_finance_metric_view_agg_only
WHERE fiscal_year = 2025
GROUP BY ALL;
```

There is no exact aggregate for `unique_customers`.

There is no unaggregated materialization.

So Databricks falls back to the source path.

Screenshot:

![Source fallback scans source tables](https://raw.githubusercontent.com/CheeYuTan/metric-views-deep-dive/main/assets/query_profiles/source_fallback.png)

What this shows:

The profile no longer shows:

```text
month_region_product_account
semantic_snapshot
```

Instead, the plan expands back to the underlying source path and scans the fact and dimension tables needed by the Metric View joins.

This is the final fallback.

## Summary

The rewrite behavior can be summarized like this:

**Exact match**

The query asks for the same dimensions and measures that were precomputed.

Result: scan the aggregated materialization directly.

**Rollup match**

The query asks for fewer dimensions, and the measure is additive.

Result: scan the aggregated materialization and aggregate it further.

**Unaggregated match**

The query cannot use the aggregate, but a row-level prepared snapshot exists.

Result: scan the unaggregated materialization.

**Source fallback**

No materialization can answer the query.

Result: scan the source fact and dimension tables.

The important part is that users do not need to choose these paths manually.

They keep querying the Metric View.

Databricks chooses the best available physical path.
