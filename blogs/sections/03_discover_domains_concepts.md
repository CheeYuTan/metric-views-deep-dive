## Discover and Domains: The First Context Layer

Databricks Discover is a curated browsing experience for data and analytics assets. Instead of forcing every person or agent to begin from catalog and schema navigation, Discover lets them browse by business context.

Domains are where that business context starts to take shape. A domain brings related assets together in a way that matches how the business works: risk, finance, operations, customer, product, and so on. When a domain becomes broad, subdomains help people narrow the context without falling back to technical names. Databricks covers the full curator and consumer workflow in the [Discover page, domains, and subdomains](https://docs.databricks.com/aws/en/discover/discover-page) documentation.

That design matters.

Catalogs and schemas are technical organization. Domains are business organization.

The same asset can be found in two very different ways.

Technical path:

```text
steven_discover_domains.risk_compliance_context_demo.credit_risk_metrics
```

Business path:

```text
Risk and Compliance -> Credit Risk -> Certified Metrics
```

The technical path works if you already know the catalog, schema, and object name.

The business path works if you only know the question you are trying to answer:

```text
Where do I find the trusted credit risk metrics?
```

That is what Domains and Discover add: business navigation on top of governed technical assets.

This is the key mental model:

```text
Domain = business responsibility
Subdomain = narrower business area
Section = curated path to the right type of asset
```
