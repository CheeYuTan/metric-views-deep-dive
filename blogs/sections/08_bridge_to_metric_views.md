## From Discover to Metric Views

Discover and Domains answer the first question:

> Where should I look?

But they do not answer every question.

Once a user lands in the right domain, the next question is:

> Which KPI definition should I trust?

That is where Metric Views come in.

In the Risk and Compliance demo, `credit_risk_metrics`, `fraud_risk_metrics`, and `risk_compliance_executive_metrics` are examples of governed Metric Views. They define reusable measures and fields, and they can carry certification, comments, display names, synonyms, and formatting metadata.

This is why Discover and Metric Views fit together:

- Discover helps users find the right business context.
- Domains and subdomains organize assets around business responsibility.
- Metric Views define the governed KPIs inside that context.
- Agent metadata helps AI/BI tools understand the language of those metrics.
- Materialization helps those trusted definitions stay fast in production.

This is also where the materialization topic fits later in the series. Materialization is not the first thing readers need to understand. But once Metric Views become the trusted KPI layer, performance matters. That post becomes the production-readiness chapter of the series:

**Metric Views in Production: Materialization Without Breaking the Semantic Layer**

The next post in the series will go deeper into Metric Views as the certified KPI layer.
