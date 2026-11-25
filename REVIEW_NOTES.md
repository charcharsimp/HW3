# Review notes

A full review of the code, the numbers and the webpage. Issues are
listed with what was done about them. Verification after the fixes:
43 tests pass, 26 SQL cross-checks pass, and an independent script
that reads the raw workbook with `openpyxl` agrees with the page.

## Bugs and risks fixed

| # | Issue | Fix |
| --- | --- | --- |
| 1 | The discount section said any discount lifts order size. Larger orders are the ones that get discounts, so the claim was overstated. | Added a same-order comparison, customer-level intervals and a break-even calculation (`discounts.robustness`). The page now says the same-order gap is +8% and not distinguishable from zero. |
| 2 | The page and the README described the eight excluded discount lines wrongly. | Corrected to "1-4% and 6%, one to three units". |
| 3 | Figure captions and alt text contained typed-in numbers that could drift from the data. | They are now built from `results.json` and the tables. |
| 4 | The "largest lapsed account" was picked by position in a table. A one-off buyer would have printed "nan" for its usual gap. | `lapse_summary` picks the largest flagged account that has a usual gap, falls back sensibly, and raises a clear error when nothing is flagged. |
| 5 | The inventory chart hard-coded "2 weeks" and "120 days". | Read from `COVER_ALERT_WEEKS` and `DEMAND_WINDOW_DAYS`. |
| 6 | Value labels on the discount chart used fixed offsets. | Offsets scale with the data. |
| 7 | The bootstrap code relied on a pandas `apply` that returns arrays, and warned on empty samples. | Plain dictionary grouping, explicit empty-sample guards, no warnings. |
| 8 | `run_all.run` only worked with `Path` arguments. | Arguments are converted to `Path`. |
| 9 | Some conclusions were typed into the text ("revenue more than doubled", "orders doubling", "fulfillment is not where to spend attention"). | Now computed from the numbers, or conditional on the test result. |
| 10 | Question 1 had no view over time, although the question is about growth over time. | Added a monthly revenue chart with the compared months shaded. |
| 11 | The discount charts did not show the main finding (the gain mostly disappears inside one order). | Added an estimates chart with intervals and the break-even line. |
| 12 | The light-theme warning colour was below the 4.5:1 contrast target. | Darkened. |
| 13 | `DOCSTRING_REPORT.md` was out of date. | Regenerated from the code (every function documented, none missing). |

## Checked and found correct

- Net revenue totals, order counts, country changes, top-customer
  shares, discount means and dollars, weekly product demand and late
  orders all match an independent SQL calculation.
- 54 figures recomputed straight from the raw workbook match the page.
- The data have no missing prices, quantities or discounts, no zero
  or negative values, no duplicate order-product lines, and no
  shipping date before an order date.
- Price on the order line differs from `Product.Price` on 30.5% of
  lines (exact and tolerance-based comparisons agree), so revenue
  uses the order-line price.

## Limits that remain

- **Observational data.** Discounts were not assigned at random, so the
  analysis cannot prove cause and effect. The page recommends a
  randomized test.
- **No cost data.** Every figure is revenue, not profit.
- **Stock date unknown.** The Product sheet has no date, so stock is
  assumed current as of the last order.
- **Judgement calls.** The lapse rule (90 days or three times the
  usual gap) and the two-week stock alert are choices, stated on the
  page.
- **Environment.** Tested with Python 3.13, pandas 3.0.5, numpy 2.5.3,
  scipy 1.18.1 and matplotlib 3.11.2 only. Other versions were not
  available to test.
- **Google Sheet.** The linked Google Sheet could only be read in part
  (its Categories tab matched). The code reads the Excel file in
  `data/`.

## Also noticed (not changed)

- The first month of data starts on 4 July 1996, so July 1996 is a
  nearly full month and is marked partial on the chart.
- Customers with fewer than three orders have no usual gap, so the
  lapse rule falls back to the 90-day floor for them.
