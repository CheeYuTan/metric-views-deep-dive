## Opening: AI/BI Needs Trusted Context

When people talk about AI/BI, the conversation often jumps straight to models, prompts, dashboards, or agents.

But in enterprise analytics, the harder problem is usually context.

A model can generate SQL, but it still needs to know which data product is trusted, which metric definition is certified, which business area the question belongs to, and which assets other teams already rely on. A dashboard can show a number, but users still need to know whether the number came from the right definition. A business user can search a catalog, but they should not need to understand every schema, table, and naming convention before finding the right asset.

That is why I think the next important topic is not just "better dashboards" or "better agents."

It is **trusted context**.

Databricks has already explained the broader Genie Ontology vision in its official announcement: [Introducing Genie One, Genie Agents, and Genie Ontology](https://www.databricks.com/blog/introducing-genie-one-genie-ontology-and-genie-agents). I will use that as the north star for this series, but I do not want to repeat the product overview here.

Instead, this series is about the practical metadata layers inside Databricks that help people, BI tools, and agents start from trusted context instead of raw technical objects.

The first layer is Discover and Domains because they answer the first question:

> Where should I look?

Before a person or agent chooses a Metric View, dashboard, Genie Space, or notebook, it needs a business-friendly entry point into the lakehouse.
