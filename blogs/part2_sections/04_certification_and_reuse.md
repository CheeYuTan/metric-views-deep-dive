## Certification Makes the Metric Discoverable and Trustworthy

In Part 1, certification appeared as a trust signal in Discover.

In Part 2, certification becomes part of the Metric View operating model.

For this demo, the certified Metric Views are:

```text
credit_risk_metrics
fraud_risk_metrics
risk_compliance_executive_metrics
```

Each one belongs to the Risk and Compliance domain and has a certification lifecycle tag.

That matters because Metric Views are not just SQL convenience objects. They are Unity Catalog objects with governance around them:

- ownership,
- comments,
- permissions,
- tags,
- certification,
- and reusable query semantics.

This means a domain page can surface a Metric View as the trusted KPI definition, and downstream consumers can reuse it directly.

That is the connection between Part 1 and Part 2:

```text
Discover tells users and agents where the trusted context lives.
Metric Views define the trusted KPIs inside that context.
```
