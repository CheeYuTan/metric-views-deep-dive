## Why Agents Need Metric Views

Agents do not only need access to data.

They need stable business definitions.

If an agent is asked:

```text
Which credit risk segment has the highest expected loss?
```

it needs to know more than which table contains credit data. It needs to know:

- which fields are safe to group by,
- which measure represents expected credit loss,
- whether the measure is certified,
- whether the source is deprecated,
- and whether there is a governed object it should query instead of improvising SQL.

Metric Views help because they provide a stable query surface:

```text
fields + measures + comments + metadata + certification
```

That is the difference between:

```text
An agent generating a best-effort SQL query
```

and:

```text
An agent querying a certified business metric
```

This is why Metric Views are a natural next layer after Domains. Domains route the question to the right business context. Metric Views provide the trusted KPI contract inside that context.
