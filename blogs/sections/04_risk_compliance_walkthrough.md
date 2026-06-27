## Example Domain: Risk and Compliance

For the walkthrough, I created a synthetic banking-oriented domain:

```text
Risk and Compliance
```

The domain description is intentionally written in business language, not Databricks product language:

> Risk and Compliance represents the bank's enterprise-wide responsibility to operate within risk appetite, meet regulatory obligations, and maintain effective oversight of financial and non-financial risk.

That distinction is important. A domain should not merely say, "this contains datasets, dashboards, Metric Views, and Genie Spaces." It should explain what the business area means and why someone would start there.

The subdomains are:

- **Credit Risk**
- **Fraud Risk**
- **AML and KYC**
- **Operational Risk**
- **Regulatory Reporting**

This gives the domain enough breadth to feel like a real enterprise risk function, while still giving users a practical way to narrow the context.

**Figure 2: A Risk and Compliance domain page can explain the business area and provide subdomains for narrower risk functions.**

`risk_compliance_domain_page`

Source file:

`assets/part1_discover_domains/figure_02_risk_compliance_domain.png`

Each subdomain has its own business description. For example, Fraud Risk is described around suspicious behavior, investigation, confirmed loss, and controls. That is more useful than describing the assets themselves.

**Figure 3: Subdomains give users a focused view, such as Fraud Risk, without creating another top-level domain.**

`fraud_risk_subdomain_page`

Source file:

`assets/part1_discover_domains/figure_03_fraud_risk_subdomain.png`

The result is a discovery path that matches how a banking user thinks:

```text
I am working on risk and compliance.
I specifically care about fraud risk.
Show me the certified assets and context for that area.
```

This is where Discover becomes more than a search page. It becomes an opinionated entry point into trusted context.
