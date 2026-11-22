# Northwind business analysis

Python-only analysis of the Northwind order data. It answers four
business questions and builds the webpage that presents them
(`docs/index.html`).

1. Which customer markets are growing or declining, and where should
   sales attention go?
2. How dependent is revenue on a few customers, and which important
   accounts have gone quiet?
3. Do bigger discounts sell more, or do they just give revenue away?
4. Which fast-selling products are about to run out, and are
   discontinued products still being bought?

## Reproduce everything

Use Python 3.11 or newer (only 3.13 has been tested). The dataset is
already in the repo at `data/Northwind_Database.xlsx`.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python run_all.py                  # rebuilds figures, tables, numbers, webpage
python verify_with_sql.py          # recomputes headline numbers with SQL
python -m unittest discover -s tests -t .   # runs all tests
```

`run_all.py` is deterministic: running it twice gives identical
numbers (a test checks this). Options:

```bash
python run_all.py --data path/to/Northwind_Database.xlsx \
                  --out outputs --site docs/index.html \
                  --repo-url https://github.com/YOU/REPO
```

Tested with Python 3.13, pandas 3.0.5, numpy 2.5.3, scipy 1.18.1,
matplotlib 3.11.2 and openpyxl 3.1.5. Other recent versions should
work but have not been tested.

## Where each number, figure and table on the webpage comes from

| Webpage item | Function | Output file |
| --- | --- | --- |
| Q1 chart | `markets.plot_market_growth` | `outputs/figures/q1_markets.png` |
| Q1 table, growth by country | `markets.market_growth` | `outputs/tables/q1_market_growth.csv` |
| Q1 headline numbers | `markets.growth_summary` | `outputs/results.json` (`q1`) |
| Q2 chart | `customers.plot_concentration` | `outputs/figures/q2_customers.png` |
| Q2 customer ranking | `customers.revenue_by_customer` | `outputs/tables/q2_revenue_by_customer.csv` |
| Q2 lapsed-accounts table | `customers.lapsed_accounts` | `outputs/tables/q2_lapsed_accounts.csv` |
| Q2 headline numbers | `customers.concentration_summary`, `customers.lapse_summary` | `outputs/results.json` (`q2`) |
| Q3 chart | `discounts.plot_discounts` | `outputs/figures/q3_discounts.png` |
| Q3 table, discount levels | `discounts.tier_table` | `outputs/tables/q3_discount_tiers.csv` |
| Q3 tests and dollars | `discounts.discount_tests`, `discounts.robustness` | `outputs/results.json` (`q3`) |
| Q4 chart | `inventory.plot_inventory` | `outputs/figures/q4_inventory.png` |
| Q4 product table | `inventory.product_cover` | `outputs/tables/q4_product_cover.csv` |
| Q4 headline numbers | `inventory.inventory_summary` | `outputs/results.json` (`q4`) |
| Delivery side check | `fulfillment.fulfillment_summary` | `outputs/results.json` (`side_check`), `outputs/tables/side_check_shippers.csv` |
| Whole page | `site.build_site` | `docs/index.html` |

The numbers quoted in the page text are filled in from
`results.json` and the tables above, so they cannot drift from the
analysis. A few fixed thresholds are written into the prose by hand
(for example "$5,000 or more" and "at least 70%" in question 1); they
match `DRIVER_MIN_GROWTH` in `markets.py` and the 0.7 cut-off in
`site.py`.

## Definitions

- **Net revenue** = `UnitPrice` x `Quantity` x (1 - `Discount`) from
  the `Orders Details` sheet. Freight is excluded. `Product.Price` is
  not used because it differs from the price charged on about 31% of
  order lines.
- **Discount** values are rounded to two decimals (the sheet stores
  0.05 as 0.0500000007).
- **Like-for-like growth** compares January through the last complete
  month (April) of 1998 with the same months of 1997. The data run
  from 4 July 1996 to 6 May 1998, so full years are not comparable.
- **Market** = the customer's country (99.5% of orders ship to the
  same country).
- **Lapsed account** = days since last order exceed the larger of
  90 days and 3 x the customer's own median gap between orders,
  measured at the date of the last order in the data.
- **Weeks of cover** = units in stock / average weekly units sold in
  the last 120 days. The Product sheet has no date, so stock is
  assumed current as of the last order.
- **Discount tiers** are 0, 5, 10, 15, 20 and 25%. Eight order lines
  with other discounts (1-4% and 6%) on one to three units are
  excluded from the discount analysis only.
- **Within-order comparison** (question 3) compares discounted and
  full-price lines inside the same order, using the 163 orders that
  contain both. Intervals resample whole customers (2,000 draws, fixed
  seed), because lines from one customer are not independent.

## Checks

- `verify_with_sql.py` loads the workbook into an in-memory SQLite
  database and recomputes revenue, orders, country changes, top-3
  share, discount means and dollars, weekly product demand and late
  orders with SQL. It compares each with `outputs/results.json`.
- `tests/test_analysis.py` checks the logic on small synthetic data
  and the full pipeline end to end.
- `tests/test_docstrings.py` checks every docstring against the rules
  in the `python-docstrings` skill (parameters in order, a `Returns:`
  or `Yields:` section, `Raises:` only where code raises, 72-character
  lines).

## Documentation

All functions carry Google-style docstrings written with the
`python-docstrings` skill. `DOCSTRING_REPORT.md` lists each
docstring, the assumptions made while writing them, and anything
noticed in the code.

## Publishing the webpage

The page is one self-contained file, `docs/index.html` (charts are
embedded). To host it on GitHub Pages: push the repo, then open
Settings > Pages, choose "Deploy from a branch", branch `main`,
folder `/docs`. Re-run `python run_all.py --repo-url <your repo URL>`
to add the repository link to the page footer.

## Layout

```
run_all.py                 runs everything
verify_with_sql.py         independent SQL cross-check
northwind_analysis/
  data.py                  load workbook, build order lines
  markets.py               question 1
  customers.py             question 2
  discounts.py             question 3
  inventory.py             question 4
  fulfillment.py           delivery side check
  plotting.py              shared chart style
  site.py                  webpage builder
tests/                     unit, pipeline and docstring tests
data/                      Northwind_Database.xlsx
outputs/                   figures, tables, results.json (generated)
docs/index.html            the webpage (generated)
```
