## What Metric Views Add

A table stores data.

A dashboard visualizes data.

A Metric View defines the governed business calculation.

That distinction matters because many KPI problems are not caused by missing data. They are caused by duplicated logic:

- one dashboard calculates expected credit loss one way,
- another notebook calculates it slightly differently,
- a BI semantic layer creates another variation,
- an agent generates SQL using whatever table and formula it can infer.

Metric Views give teams a stable contract:

```text
Use this field.
Use this measure.
Use this join logic.
Use this filter.
Use this KPI definition.
```

In Databricks SQL, users query measures through the `MEASURE()` function. That is a small syntax detail with an important meaning: users are asking for a governed measure, not rewriting the aggregation themselves.

For example, instead of asking every dashboard author to calculate expected credit loss and ECL rate manually, a Metric View can expose:

```text
MEASURE(expected_credit_loss)
MEASURE(ecl_rate)
```

The table is the input.

The Metric View is the certified KPI definition.
