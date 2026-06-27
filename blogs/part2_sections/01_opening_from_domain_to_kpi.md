## From Domain to KPI

In Part 1, I focused on Discover and Domains.

The question there was:

> Where should I look?

For a risk and compliance team, the answer might be:

```text
Risk and Compliance -> Credit Risk
```

That gets a person, dashboard author, or agent into the right business context. But it does not fully answer the next question:

> Which KPI definition should I trust?

That is where Metric Views come in.

A domain tells you where the asset belongs. A Metric View defines what the metric means.

For this post, I will continue with the same synthetic Risk and Compliance example and use:

```text
Risk and Compliance -> Credit Risk -> credit_risk_metrics
```

The goal is not to repeat every Metric View feature. I already wrote a deeper finance example in [Beyond Simple Aggregations: Building Financial Analytics with Databricks Metric Views](https://medium.com/@cheeyutcy/beyond-simple-aggregations-building-financial-analytics-with-databricks-metric-views-59a829fc030f?source=friends_link&sk=6672b02c6a36cff06054fe44db143ff8), covering joins, nested measures, rolling metrics, YTD calculations, and semiadditive balances.

This post is narrower.

It explains where Metric Views fit in the trusted-context story: they are the certified KPI layer that downstream experiences can reuse.
