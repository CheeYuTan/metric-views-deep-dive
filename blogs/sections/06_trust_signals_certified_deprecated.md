## Trust Signals: Certified and Deprecated

Discover is not only about finding assets.

It should also help users understand which assets to trust.

For this demo, I created both certified and deprecated examples.

The certified example is a Metric View:

```text
credit_risk_metrics
```

It is tagged as certified and belongs to both the parent domain and the Credit Risk subdomain.

**Figure 5: Certification makes the trusted semantic asset explicit, in this case a Metric View for credit risk.**

`certified_metric_view_detail`

Source file:

`assets/part1_discover_domains/figure_05_certified_metric_view.png`

This is the asset I want users to trust when they need governed credit risk measures such as exposure amount, expected credit loss, and ECL rate.

The deprecated example is a legacy table:

```text
legacy_manual_fraud_extract
```

It is intentionally tagged as deprecated.

**Figure 6: Deprecated lifecycle status helps users avoid stale or legacy assets for new analysis.**

`deprecated_table_detail`

Source file:

`assets/part1_discover_domains/figure_06_deprecated_asset.png`

This is just as important as certification.

In real organizations, the problem is not only that users cannot find trusted assets. It is also that old extracts, spreadsheets, duplicated tables, and one-off dashboards continue to exist. If users can find those assets but cannot see that they are deprecated, they might accidentally use the wrong source.

This is where lifecycle metadata becomes part of trusted context:

- Certified tells users what to use.
- Deprecated tells users what not to use for new analysis.
- Domain tags tell users where the asset belongs.
- Subdomain tags tell users which business area the asset supports.

That combination is powerful because it changes the user experience from:

```text
I found a table. I hope it is right.
```

to:

```text
I found a certified metric in the right business context.
```
