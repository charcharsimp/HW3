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
| Download links on the page | `site.copy_downloads` | `docs/downloads/` (copies of the CSV tables and `results.json`) |

The numbers quoted in the page text are filled in from
`results.json` and the tables above, so they cannot drift from the
analysis. Thresholds such as the $5,000 growth floor, the 90-day lapse
floor and the 5% base discount are read from the constants in the
analysis modules. The one fixed threshold written into the prose is
the 70% "one account" cut-off in question 1 (`site.py`).

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

## How the webpage shows its reasoning

Each question has a short answer, bulleted findings and a "How we got
this" block. The block walks through the calculation with the real
numbers and links to the CSV tables, `results.json` and the code. The
page ends with a "Check our work" section, including a spreadsheet
formula that reproduces total net revenue from the `Orders Details`
sheet. The table and `results.json` links point at `docs/downloads/`,
so upload that folder with `docs/index.html`. Code links go to the
files on GitHub: they use `--repo-url` when you pass it and otherwise
work out the repository from the `github.io` address of the page.

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
folder `/docs`. Upload `docs/downloads/` with the page, or its links
will be broken. Re-run `python run_all.py --repo-url <your repo URL>`
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
docs/downloads/            tables and results.json linked from the page
SKILL.md                   the python-docstrings skill used for docstrings
assignment/                the assignment brief
```
