## Example: Credit Risk Metrics

In the Risk and Compliance domain, I created a synthetic Credit Risk subdomain.

The source table is:

```text
credit_risk_exposures
```

It contains synthetic exposure amount, probability of default, loss given default, and expected credit loss values.

A user could manually aggregate the source table:

```sql
SELECT
  product_line,
  risk_band,
  SUM(exposure_amount) AS exposure_amount,
  SUM(expected_credit_loss) AS expected_credit_loss,
  SUM(expected_credit_loss) / NULLIF(SUM(exposure_amount), 0) AS ecl_rate
FROM credit_risk_exposures
GROUP BY ALL;
```

That works once.

But if every downstream tool repeats this logic, the organization is back to metric sprawl.

Instead, the certified Metric View exposes the same business logic as reusable measures:

```sql
SELECT
  product_line,
  risk_band,
  MEASURE(exposure_amount) AS exposure_amount,
  MEASURE(expected_credit_loss) AS expected_credit_loss,
  MEASURE(ecl_rate) AS ecl_rate
FROM credit_risk_metrics
GROUP BY ALL;
```

This is the trust boundary.

The dashboard author, SQL user, BI tool, and agent should not each invent an ECL formula. They should reuse the certified measure from `credit_risk_metrics`.
