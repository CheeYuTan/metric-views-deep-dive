## Validation Is Part of the Operating Model

If a Metric View is going to be treated as certified, it should be validated.

In the companion notebook for this post, I compare the Metric View output against the explicit source-table calculation.

The notebook checks that:

```text
manual source calculation == Metric View calculation
```

for:

```text
exposure_amount
expected_credit_loss
ecl_rate
```

This is a small example, but the pattern matters.

Certification should not be just a label. For important metrics, teams should have tests or validation queries that prove the Metric View still matches the intended business definition.

That gives the organization more confidence that the metric is safe to reuse across:

- dashboards,
- SQL analysis,
- BI tools,
- Genie Spaces,
- and agent workflows.

Trusted context needs both metadata and validation.
