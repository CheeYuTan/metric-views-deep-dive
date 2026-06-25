-- Databricks SQL setup script for the Metric Views LOD finance semantics demo.
-- Edit the catalog and schema before running if needed.

USE CATALOG main;
CREATE SCHEMA IF NOT EXISTS metric_views_lod_demo;
USE SCHEMA metric_views_lod_demo;

CREATE OR REPLACE TABLE dim_account AS
SELECT * FROM VALUES
  ('A4000','Product Revenue','Revenue','P&L','Revenue'),
  ('A4010','Service Revenue','Revenue','P&L','Revenue'),
  ('A5000','Cost of Goods Sold','COGS','P&L','Expense'),
  ('A6100','Sales Expense','Opex','P&L','Expense'),
  ('A6200','Technology Expense','Opex','P&L','Expense'),
  ('A1000','Cash Balance','Cash','Balance Sheet','Asset'),
  ('A1100','Accounts Receivable','Receivables','Balance Sheet','Asset'),
  ('A2000','Deferred Revenue','Deferred Revenue','Balance Sheet','Liability')
AS dim_account(account_id, account_name, account_category, statement_section, normal_balance);

CREATE OR REPLACE TABLE dim_product AS
SELECT * FROM VALUES
  ('P01','Payments API','Digital Platforms','Platform'),
  ('P02','Data Exchange','Digital Platforms','Platform'),
  ('P03','Risk Analytics','Analytics','Software'),
  ('P04','Treasury Insights','Analytics','Software'),
  ('P05','Advisory Services','Services','Services')
AS dim_product(product_id, product_name, product_family, business_unit);

CREATE OR REPLACE TABLE dim_entity AS
SELECT * FROM VALUES
  ('E_SG','Singapore Entity','Singapore','APJ'),
  ('E_AU','Australia Entity','Australia','APJ'),
  ('E_US','US Entity','United States','AMER'),
  ('E_UK','UK Entity','United Kingdom','EMEA')
AS dim_entity(entity_id, entity_name, country, region);

CREATE OR REPLACE TABLE dim_customer_segment AS
SELECT * FROM VALUES
  ('S_ENT','Enterprise','Strategic'),
  ('S_MM','Mid-Market','Commercial'),
  ('S_SMB','SMB','Commercial')
AS dim_customer_segment(segment_id, segment_name, segment_group);

CREATE OR REPLACE TABLE dim_scenario AS
SELECT * FROM VALUES
  ('ACTUAL','Actual'),
  ('BUDGET','Budget'),
  ('FORECAST','Forecast')
AS dim_scenario(scenario_id, scenario_name);

CREATE OR REPLACE TABLE dim_calendar AS
WITH dates AS (
  SELECT explode(sequence(to_date('2024-01-01'), to_date('2025-12-31'), interval 1 day)) AS calendar_date
)
SELECT
  calendar_date,
  date_trunc('MONTH', calendar_date) AS fiscal_month,
  concat(year(calendar_date), '-Q', quarter(calendar_date)) AS fiscal_quarter,
  year(calendar_date) AS fiscal_year,
  make_date(year(calendar_date), 1, 1) AS fiscal_year_start,
  last_day(calendar_date) AS month_end_date
FROM dates;

CREATE OR REPLACE TABLE fact_gl_transactions AS
WITH dates AS (
  SELECT calendar_date
  FROM dim_calendar
  WHERE dayofmonth(calendar_date) IN (3, 9, 15, 21, 27)
),
combos AS (
  SELECT
    d.calendar_date,
    e.entity_id,
    p.product_id,
    s.segment_id,
    a.account_id,
    row_number() OVER (ORDER BY d.calendar_date, e.entity_id, p.product_id, s.segment_id, a.account_id) AS rn
  FROM dates d
  CROSS JOIN dim_entity e
  CROSS JOIN dim_product p
  CROSS JOIN dim_customer_segment s
  CROSS JOIN dim_account a
  WHERE a.statement_section = 'P&L'
)
SELECT
  concat('TXN-', rn) AS transaction_id,
  calendar_date AS posting_date,
  entity_id,
  product_id,
  segment_id,
  account_id,
  'ACTUAL' AS scenario_id,
  CASE
    WHEN account_id IN ('A4000','A4010') THEN round(12000 + pmod(rn * 37, 7000), 2)
    WHEN account_id = 'A5000' THEN round(3500 + pmod(rn * 23, 3000), 2)
    ELSE round(1800 + pmod(rn * 19, 2400), 2)
  END AS amount
FROM combos;

CREATE OR REPLACE TABLE fact_monthly_targets AS
WITH months AS (
  SELECT DISTINCT fiscal_month
  FROM dim_calendar
),
combos AS (
  SELECT
    m.fiscal_month,
    e.entity_id,
    p.product_id,
    s.segment_id,
    a.account_id,
    sc.scenario_id,
    row_number() OVER (ORDER BY m.fiscal_month, e.entity_id, p.product_id, s.segment_id, a.account_id, sc.scenario_id) AS rn
  FROM months m
  CROSS JOIN dim_entity e
  CROSS JOIN dim_product p
  CROSS JOIN dim_customer_segment s
  CROSS JOIN dim_account a
  CROSS JOIN dim_scenario sc
  WHERE a.statement_section = 'P&L'
    AND sc.scenario_id IN ('BUDGET','FORECAST')
)
SELECT
  concat('TGT-', rn) AS target_id,
  fiscal_month,
  entity_id,
  product_id,
  segment_id,
  account_id,
  scenario_id,
  CASE
    WHEN account_id IN ('A4000','A4010') THEN round(370000 + pmod(rn * 113, 90000), 2)
    WHEN account_id = 'A5000' THEN round(125000 + pmod(rn * 71, 45000), 2)
    ELSE round(70000 + pmod(rn * 53, 32000), 2)
  END AS target_amount
FROM combos;

CREATE OR REPLACE TABLE fact_month_end_balances AS
WITH months AS (
  SELECT DISTINCT month_end_date
  FROM dim_calendar
),
combos AS (
  SELECT
    m.month_end_date,
    e.entity_id,
    p.product_id,
    s.segment_id,
    a.account_id,
    row_number() OVER (ORDER BY m.month_end_date, e.entity_id, p.product_id, s.segment_id, a.account_id) AS rn
  FROM months m
  CROSS JOIN dim_entity e
  CROSS JOIN dim_product p
  CROSS JOIN dim_customer_segment s
  CROSS JOIN dim_account a
  WHERE a.statement_section = 'Balance Sheet'
)
SELECT
  concat('BAL-', rn) AS balance_id,
  month_end_date,
  entity_id,
  product_id,
  segment_id,
  account_id,
  'ACTUAL' AS scenario_id,
  CASE
    WHEN account_id = 'A1000' THEN round(1500000 + pmod(rn * 907, 350000), 2)
    WHEN account_id = 'A1100' THEN round(900000 + pmod(rn * 577, 225000), 2)
    ELSE round(500000 + pmod(rn * 431, 160000), 2)
  END AS balance_amount
FROM combos;

CREATE OR REPLACE VIEW finance_semantic_base AS
WITH gl AS (
  SELECT
    transaction_id AS source_record_id,
    'GL' AS source_grain,
    posting_date AS event_date,
    date_trunc('MONTH', posting_date) AS fiscal_month,
    entity_id,
    product_id,
    segment_id,
    account_id,
    scenario_id,
    amount,
    CAST(NULL AS DOUBLE) AS balance_amount
  FROM fact_gl_transactions
),
targets AS (
  SELECT
    target_id AS source_record_id,
    'TARGET' AS source_grain,
    fiscal_month AS event_date,
    fiscal_month,
    entity_id,
    product_id,
    segment_id,
    account_id,
    scenario_id,
    target_amount AS amount,
    CAST(NULL AS DOUBLE) AS balance_amount
  FROM fact_monthly_targets
),
balances AS (
  SELECT
    balance_id AS source_record_id,
    'BALANCE' AS source_grain,
    month_end_date AS event_date,
    date_trunc('MONTH', month_end_date) AS fiscal_month,
    entity_id,
    product_id,
    segment_id,
    account_id,
    scenario_id,
    CAST(NULL AS DOUBLE) AS amount,
    balance_amount
  FROM fact_month_end_balances
)
SELECT
  b.source_record_id,
  b.source_grain,
  b.event_date,
  b.fiscal_month,
  c.fiscal_quarter,
  c.fiscal_year,
  c.fiscal_year_start,
  b.entity_id,
  e.entity_name,
  e.country,
  e.region,
  b.product_id,
  p.product_name,
  p.product_family,
  p.business_unit,
  b.segment_id,
  s.segment_name,
  s.segment_group,
  b.account_id,
  a.account_name,
  a.account_category,
  a.statement_section,
  a.normal_balance,
  b.scenario_id,
  sc.scenario_name,
  b.amount,
  b.balance_amount
FROM (
  SELECT * FROM gl
  UNION ALL
  SELECT * FROM targets
  UNION ALL
  SELECT * FROM balances
) b
JOIN dim_calendar c
  ON b.event_date = c.calendar_date
JOIN dim_entity e
  ON b.entity_id = e.entity_id
JOIN dim_product p
  ON b.product_id = p.product_id
JOIN dim_customer_segment s
  ON b.segment_id = s.segment_id
JOIN dim_account a
  ON b.account_id = a.account_id
JOIN dim_scenario sc
  ON b.scenario_id = sc.scenario_id;
