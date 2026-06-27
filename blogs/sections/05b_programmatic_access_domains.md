## Programmatic Access: Reading the Metadata Behind Discover

The Discover page is the curated experience, but the metadata behind it is not a black box.

For customers who want to inspect, validate, or automate parts of their domain setup, the most reliable programmatic entry point is the governed tag layer.

The important distinction is:

```text
Discover experience = curated in the UI
Domain membership = backed by governed tags
Asset lifecycle = exposed through tags such as system.certification_status
```

That means we can answer useful questions programmatically:

- Which governed tags back my domains and subdomains?
- Which tables, views, and Metric Views are assigned to a domain?
- Which assets are certified or deprecated?
- Which dashboards, Genie Spaces, notebooks, and apps carry domain tags?

I added a companion notebook for this:

```text
notebooks/deep_dives/03_discover_domains_programmatic_access.py
```

The notebook is widget-driven, so a customer can point it at their own catalog, optional schema, domain tag prefix, and certification tag.

Figure to capture here:

**Figure 8: The programmatic access notebook uses widgets so teams can inspect their own catalog, schema, domain tag, and lifecycle tag.**

Suggested screenshot:

```text
Notebook widgets at the top of 03_discover_domains_programmatic_access.py
```

Validated run:

```text
https://dbc-0db33bdb-d775.cloud.databricks.com/?o=7474659426247147#job/67615880918892/run/1017280921217491
```

In the notebook, I use three programmatic surfaces.

First, I query Unity Catalog tag metadata through `information_schema.table_tags`. This is useful for tables, views, and Metric Views:

```sql
SELECT
  catalog_name,
  schema_name,
  table_name,
  tag_name,
  tag_value
FROM information_schema.table_tags
WHERE tag_name = '<domain tag>'
   OR tag_name LIKE '<domain tag>/%';
```

This gives a domain and subdomain inventory from the assets that are visible to the current user.

Figure to capture here:

**Figure 9: Assigned tags can be queried from Unity Catalog metadata to reconstruct which assets belong to a domain or subdomain.**

Suggested screenshot:

```text
Notebook output: Domain/Subdomain Inventory From Tags
```

Second, I compare assigned tags with governed tag policies. This matters because Discover Domains and subdomains should be backed by governed tags, not random free-form labels.

Figure to capture here:

**Figure 10: A domain tag should correspond to a governed tag policy, not just an arbitrary label.**

Suggested screenshot:

```text
Notebook output: Check Whether Assigned Domain Tags Are Governed
```

Third, I use workspace entity tag assignments for assets that do not live in Unity Catalog tables, such as dashboards, Genie Spaces, notebooks, and apps.

For example, the same Risk and Compliance domain can include:

```text
Unity Catalog assets:
- tables
- views
- Metric Views

Workspace assets:
- dashboards
- Genie Spaces
- notebooks
- apps
```

Figure to capture here:

**Figure 11: Workspace asset tag assignments expose domain metadata for dashboards, Genie Spaces, notebooks, and apps.**

Suggested screenshot:

```text
Notebook output: Workspace Asset Tag Assignments
```

Finally, lifecycle tags can also be inspected programmatically. This is useful because certification and deprecation are part of the trust story.

Figure to capture here:

**Figure 12: Certification and deprecation tags can be queried as lifecycle signals for trusted context.**

Suggested screenshot:

```text
Notebook output: Certification and Lifecycle View
```

This is the technical side of the same story: Discover gives people and agents a curated front door, while governed tags and tag assignments make the membership inspectable and automatable.

There is still a boundary to be aware of. Programmatic access is strong for governed tags, tag policies, and tag assignments. The curated page experience itself, including descriptions, custom sections, pinning, ordering, drafts, and publishing, remains a Discover curator workflow in the UI.
