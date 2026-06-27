## More Than Tables: Context Across Asset Types

One thing I like about Discover is that the domain page is not limited to tables.

For this demo, I created a complete synthetic estate across the asset types shown in Discover:

- Dashboards
- Apps
- Genie Spaces
- Metric Views
- Tables
- Notebooks

That matters because business context does not live in one object type.

A risk analyst might start with a dashboard. A data engineer might inspect the underlying tables. A business user might ask a question in a Genie Space. A platform team might look at notebooks used to generate or validate assets. A governance team might care most about which Metric Views are certified.

All of these can be part of the same domain experience.

For the Risk and Compliance example, the curated estate includes:

```text
Dashboards:
- Risk and Compliance Executive Overview
- Credit Risk Portfolio Monitor
- Fraud Risk Operations Monitor
- AML and KYC Monitoring Dashboard
- Operational Risk Control Dashboard
- Regulatory Reporting Readiness Dashboard

Genie Spaces:
- Ask Risk and Compliance
- Ask Credit Risk
- Ask Fraud Risk
- Ask AML and KYC
- Ask Operational Risk
- Ask Regulatory Reporting

Metric Views:
- risk_compliance_executive_metrics
- credit_risk_metrics
- fraud_risk_metrics

App:
- risk-compliance-context-app

Notebooks:
- 00_risk_compliance_discover_assets
- 01_risk_compliance_bi_asset_catalog
```

The key point is not that every domain needs every asset type. The point is that a trusted domain can bring different asset types into one business context.
