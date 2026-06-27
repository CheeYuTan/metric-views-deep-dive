## Custom Sections: Curating by Intent

Once a domain and subdomains exist, the next question is how to shape the domain page for the people and agents who will use it.

This is where Discover becomes more than a search result page.

Curators can customize the Discover page, domain pages, and subdomain pages. They can create custom sections, choose whether a section is powered by a search query or by manually selected assets, pin important assets, reorder manually selected assets, save drafts, and publish the page for consumers. The full curator workflow is covered in the [Discover page, domains, and subdomains](https://docs.databricks.com/aws/en/discover/discover-page) documentation.

That flexibility is useful because domains can support different browsing patterns.

A user might know the business area and browse by subdomain. Another user might know the type of context they need: certified metrics, recently updated assets, dashboards, Genie Spaces, notebooks, or deprecated assets to avoid.

So I think of the page structure this way:

- **Subdomains** help users narrow the business area.
- **Sections** help users find the right kind of asset or context.

In my Risk and Compliance example, I used sections such as:

- **Certified Metrics**
- **Recently Updated**
- **Curated Data Assets**

**Figure 4: Custom sections curate assets by intent, such as certified metrics, recent updates, and data assets.**

`risk_compliance_custom_sections`

Source file:

`assets/part1_discover_domains/figure_04_custom_sections.png`

This is only one possible layout. The important part is that the sections reflect user intent, not just another copy of the subdomain list.

In this example:

- **Certified Metrics** points users to governed KPI definitions.
- **Recently Updated** highlights fresh context for current review.
- **Curated Data Assets** gives users a path to the underlying certified tables and views.

Other domains might choose different sections. A finance domain might highlight planning dashboards and month-end close assets. A product domain might highlight adoption metrics and telemetry assets. A risk domain might highlight certified metrics, monitoring dashboards, and lifecycle signals.

For the blog series, this matters because trusted context is not just metadata attached to objects. It is also the curated experience that helps users and agents find the right context quickly.
