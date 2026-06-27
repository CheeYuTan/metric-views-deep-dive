import os
from http.server import BaseHTTPRequestHandler, HTTPServer


PORT = int(os.environ.get("DATABRICKS_APP_PORT", "8000"))


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Risk and Compliance Context Portal</title>
  <style>
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: #1f2933;
      background: #f7f8fa;
    }
    header {
      background: #111827;
      color: white;
      padding: 32px 40px;
    }
    main {
      padding: 32px 40px;
      max-width: 1180px;
      margin: 0 auto;
    }
    h1, h2, h3 {
      margin: 0 0 12px;
    }
    p {
      line-height: 1.5;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 16px;
      margin: 20px 0 32px;
    }
    .card {
      background: white;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      padding: 18px;
      box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    .tag {
      display: inline-block;
      border-radius: 999px;
      padding: 4px 10px;
      font-size: 12px;
      margin-right: 6px;
      background: #e0f2fe;
      color: #075985;
    }
    .certified {
      background: #dcfce7;
      color: #166534;
    }
    .deprecated {
      background: #fee2e2;
      color: #991b1b;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      background: white;
      border-radius: 12px;
      overflow: hidden;
    }
    th, td {
      text-align: left;
      border-bottom: 1px solid #e5e7eb;
      padding: 12px 14px;
      vertical-align: top;
    }
    th {
      background: #f3f4f6;
      font-weight: 600;
    }
  </style>
</head>
<body>
  <header>
    <h1>Risk and Compliance Context Portal</h1>
    <p>Synthetic demo app for trusted Databricks Discover context: domains, subdomains, certified assets, dashboards, Genie Spaces, and deprecated assets.</p>
  </header>
  <main>
    <section class="grid">
      <div class="card">
        <h2>Domain</h2>
        <p><strong>Risk and Compliance</strong></p>
        <p>Enterprise risk oversight, compliance controls, financial crime, and regulatory accountability.</p>
      </div>
      <div class="card">
        <h2>Trust Signals</h2>
        <p><span class="tag certified">certified</span> curated Metric Views, dashboards, Genie Spaces, and source assets</p>
        <p><span class="tag deprecated">deprecated</span> legacy extract retained to demonstrate lifecycle status</p>
      </div>
      <div class="card">
        <h2>Warehouse</h2>
        <p>Designed for screenshots in the <code>steven_discover_domains</code> workspace.</p>
      </div>
    </section>

    <h2>Subdomains</h2>
    <section class="grid">
      <div class="card"><h3>Credit Risk</h3><p>Credit exposure, expected credit loss, portfolio quality, and early warning signals.</p></div>
      <div class="card"><h3>Fraud Risk</h3><p>Fraud alerts, suspicious activity, confirmed losses, and investigation context.</p></div>
      <div class="card"><h3>AML and KYC</h3><p>Customer due diligence, KYC refresh, risk ratings, monitoring alerts, and escalations.</p></div>
      <div class="card"><h3>Operational Risk</h3><p>Operational incidents, control effectiveness, open issues, and resilience indicators.</p></div>
      <div class="card"><h3>Regulatory Reporting</h3><p>Reporting due dates, evidence completeness, report readiness, and accountability.</p></div>
    </section>

    <h2>Recommended Discover Sections</h2>
    <table>
      <thead>
        <tr><th>Section</th><th>Example assets</th><th>Why it matters</th></tr>
      </thead>
      <tbody>
        <tr><td>Start Here</td><td>Risk and Compliance Executive Overview, Ask Risk and Compliance</td><td>Gives business users an immediate entry point.</td></tr>
        <tr><td>Certified Metric Views</td><td>credit_risk_metrics, fraud_risk_metrics, risk_compliance_executive_metrics</td><td>Shows governed KPI definitions.</td></tr>
        <tr><td>Operational Drilldowns</td><td>Fraud Risk Operations Monitor, AML and KYC Monitoring Dashboard, Operational Risk Control Dashboard</td><td>Routes users to the right workflow.</td></tr>
        <tr><td>Lifecycle Signals</td><td>legacy_manual_fraud_extract</td><td>Demonstrates how deprecated assets should be visible but discouraged.</td></tr>
      </tbody>
    </table>
  </main>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML.encode("utf-8"))


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Serving on port {PORT}")
    server.serve_forever()
