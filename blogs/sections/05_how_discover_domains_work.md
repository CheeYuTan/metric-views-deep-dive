## How It Works: Domains Are Business Context Backed by Governed Tags

After seeing the domain page, it is useful to understand what is happening underneath.

Discover is the user-facing experience. Governed tags are the metadata mechanism that makes domain membership consistent.

In this example, the top-level domain is backed by a governed tag:

```text
Risk and Compliance
```

Each subdomain is backed by a governed tag that uses the parent domain as a prefix:

```text
Risk and Compliance/Credit Risk
Risk and Compliance/Fraud Risk
Risk and Compliance/AML and KYC
Risk and Compliance/Operational Risk
Risk and Compliance/Regulatory Reporting
```

When an asset is assigned to a domain or subdomain, that domain context becomes visible in Discover. This is why the same asset can appear as a technical object in Unity Catalog and as a business asset in Discover.

For example:

```text
steven_discover_domains.risk_compliance_context_demo.credit_risk_metrics
```

can also be discovered through:

```text
Risk and Compliance -> Credit Risk
```

This is the important design point:

```text
Catalog and schema tell you where the object lives.
Domain and subdomain tell you what business context it belongs to.
Certification tells you whether it should be trusted.
Deprecation tells you whether it should be avoided for new work.
```

The same mechanism also supports different asset types. A domain can bring together tables, views, Metric Views, dashboards, Genie Spaces, notebooks, and apps because the shared context is metadata, not a folder path.

There are two practical details worth knowing:

1. Subdomain tags are independent from parent domain tags. If an asset belongs to `Risk and Compliance/Fraud Risk`, curators should still make sure it is surfaced appropriately in the parent domain experience.
2. Tag and domain metadata are plain text. Do not put sensitive names, customer identifiers, or confidential information into tag names, subtitles, or descriptions.

That is the balance: Discover makes the experience business-friendly, while governed tags keep the organization of that experience consistent and manageable.
