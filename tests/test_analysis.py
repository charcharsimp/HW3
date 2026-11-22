"""Tests for the analysis logic and the full pipeline."""

import json
import re
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

import run_all
from northwind_analysis import (
    customers,
    data,
    discounts,
    inventory,
    markets,
)

ROOT = Path(__file__).resolve().parent.parent
WORKBOOK = ROOT / "data" / "Northwind_Database.xlsx"


def make_lines(rows):
    """Build a small order-line table for tests.

    Args:
        rows (list[tuple]): Tuples of (OrderID, CustomerID, Country,
            date string, ProductID, UnitPrice, Quantity, Discount).

    Returns:
        pandas.DataFrame: Table shaped like
        ``data.build_order_lines`` output.
    """
    lines = pd.DataFrame(
        rows,
        columns=[
            "OrderID",
            "CustomerID",
            "Country",
            "OrderDate",
            "ProductID",
            "UnitPrice",
            "Quantity",
            "Discount",
        ],
    )
    lines["OrderDate"] = pd.to_datetime(lines["OrderDate"])
    lines["CompanyName"] = "Co " + lines["CustomerID"]
    lines["GrossRevenue"] = lines["UnitPrice"] * lines["Quantity"]
    lines["DiscountAmount"] = lines["GrossRevenue"] * lines["Discount"]
    lines["NetRevenue"] = lines["GrossRevenue"] - lines["DiscountAmount"]
    lines["Year"] = lines["OrderDate"].dt.year
    lines["Month"] = lines["OrderDate"].dt.month
    return lines


class TestComparisonWindow(unittest.TestCase):
    def test_mid_month_end_drops_partial_month(self):
        dates = pd.Series(pd.to_datetime(["1997-01-02", "1998-05-06"]))
        self.assertEqual(data.comparison_window(dates), (1997, 1998, 4))

    def test_month_end_is_complete(self):
        dates = pd.Series(pd.to_datetime(["1997-01-02", "1998-04-30"]))
        self.assertEqual(data.comparison_window(dates), (1997, 1998, 4))

    def test_early_january_falls_back_to_december(self):
        dates = pd.Series(pd.to_datetime(["1997-01-02", "1998-01-05"]))
        self.assertEqual(data.comparison_window(dates), (1996, 1997, 12))


class TestOrderLines(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tables = data.load_tables(WORKBOOK)
        cls.lines = data.build_order_lines(cls.tables)

    def test_no_rows_lost_or_duplicated(self):
        self.assertEqual(
            len(self.lines), len(self.tables["Orders Details"])
        )

    def test_discounts_rounded(self):
        self.assertTrue(
            np.allclose(self.lines["Discount"], self.lines["Discount"].round(2))
        )
        self.assertEqual(
            set(self.lines["Discount"].round(2).unique()) - set(discounts.TIERS),
            {0.01, 0.02, 0.03, 0.04, 0.06},
        )

    def test_revenue_identity(self):
        net = (
            self.lines["UnitPrice"]
            * self.lines["Quantity"]
            * (1 - self.lines["Discount"])
        )
        self.assertTrue(np.allclose(net, self.lines["NetRevenue"]))

    def test_missing_workbook_raises(self):
        with self.assertRaises(FileNotFoundError):
            data.load_tables(ROOT / "nope.xlsx")


class TestMarkets(unittest.TestCase):
    def setUp(self):
        self.lines = make_lines(
            [
                (1, "A", "X", "1997-02-01", 1, 10.0, 100, 0.0),
                (2, "A", "X", "1998-02-01", 1, 10.0, 300, 0.0),
                (3, "B", "X", "1998-03-01", 1, 10.0, 200, 0.0),
                (4, "C", "Y", "1997-03-01", 1, 10.0, 500, 0.0),
                (5, "C", "Y", "1998-03-01", 1, 10.0, 100, 0.0),
                (6, "A", "X", "1998-09-01", 1, 10.0, 999, 0.0),
            ]
        )

    def test_changes_use_matching_months_only(self):
        table = markets.market_growth(self.lines, 1997, 1998, 4)
        x = table.set_index("Country").loc["X"]
        self.assertEqual(x["RevenuePrev"], 1000.0)
        self.assertEqual(x["RevenueCur"], 5000.0)
        self.assertEqual(x["Change"], 4000.0)
        y = table.set_index("Country").loc["Y"]
        self.assertEqual(y["Change"], -4000.0)

    def test_driver_share_only_for_material_growth(self):
        table = markets.market_growth(self.lines, 1997, 1998, 4)
        x = table.set_index("Country").loc["X"]
        self.assertTrue(np.isnan(x["DriverShareOfChange"]))

    def test_driver_share_when_material(self):
        lines = make_lines(
            [
                (1, "A", "X", "1997-02-01", 1, 10.0, 100, 0.0),
                (2, "A", "X", "1998-02-01", 1, 10.0, 1100, 0.0),
                (3, "B", "X", "1998-03-01", 1, 10.0, 200, 0.0),
            ]
        )
        table = markets.market_growth(lines, 1997, 1998, 4)
        row = table.iloc[0]
        self.assertEqual(row["DriverAccount"], "Co A")
        self.assertAlmostEqual(row["DriverShareOfChange"], 10000 / 12000)

    def test_small_base_has_no_percent(self):
        table = markets.market_growth(self.lines, 1997, 1998, 4)
        x = table.set_index("Country").loc["X"]
        self.assertTrue(np.isnan(x["PctChange"]))


class TestCustomers(unittest.TestCase):
    def setUp(self):
        rows = []
        order = 0
        for day in ("1998-01-01", "1998-01-11", "1998-01-21", "1998-01-31"):
            order += 1
            rows.append((order, "REG", "X", day, 1, 10.0, 10, 0.0))
        order += 1
        rows.append((order, "NEW", "X", "1998-04-30", 1, 10.0, 10, 0.0))
        order += 1
        rows.append((order, "OLD", "X", "1997-01-01", 1, 10.0, 10, 0.0))
        order += 1
        rows.append((order, "REG", "X", "1998-05-06", 1, 10.0, 10, 0.0))
        self.lines = make_lines(rows)

    def test_ranking_and_cumulative_share(self):
        table = customers.revenue_by_customer(self.lines)
        self.assertEqual(table["CustomerID"].iloc[0], "REG")
        self.assertAlmostEqual(table["CumShare"].iloc[-1], 1.0)
        self.assertTrue(table["Share"].is_monotonic_decreasing)

    def test_lapse_rule(self):
        table = customers.lapsed_accounts(self.lines).set_index("CustomerID")
        self.assertFalse(table.loc["REG", "Lapsed"])
        self.assertFalse(table.loc["NEW", "Lapsed"])
        self.assertTrue(table.loc["OLD", "Lapsed"])

    def test_threshold_scales_with_typical_gap(self):
        rows = [
            (i + 1, "SLOW", "X", d, 1, 10.0, 10, 0.0)
            for i, d in enumerate(
                ["1997-01-01", "1997-06-01", "1997-11-01"]
            )
        ]
        rows.append((9, "OTHER", "X", "1998-05-06", 1, 10.0, 10, 0.0))
        table = customers.lapsed_accounts(make_lines(rows))
        slow = table.set_index("CustomerID").loc["SLOW"]
        self.assertGreater(
            slow["ThresholdDays"], customers.IDLE_FLOOR_DAYS
        )
        # Silent 186 days, but they usually wait about 152 between
        # orders, so a 456-day threshold means they are not lapsed.
        self.assertGreater(slow["IdleDays"], customers.IDLE_FLOOR_DAYS)
        self.assertFalse(slow["Lapsed"])


class TestDiscounts(unittest.TestCase):
    def test_off_tier_lines_excluded(self):
        lines = make_lines(
            [
                (1, "A", "X", "1998-01-01", 1, 10.0, 5, 0.0),
                (2, "A", "X", "1998-01-01", 1, 10.0, 5, 0.03),
                (3, "A", "X", "1998-01-01", 1, 10.0, 5, 0.05),
            ]
        )
        self.assertEqual(len(discounts.tier_lines(lines)), 2)

    def test_tier_table_values(self):
        lines = make_lines(
            [
                (1, "A", "X", "1998-01-01", 1, 10.0, 10, 0.0),
                (2, "A", "X", "1998-01-01", 1, 10.0, 20, 0.0),
                (3, "A", "X", "1998-01-01", 1, 10.0, 30, 0.25),
                (4, "A", "X", "1998-01-01", 1, 10.0, 50, 0.25),
            ]
        )
        table = discounts.tier_table(lines).set_index("Discount")
        self.assertEqual(table.loc[0.0, "MeanQty"], 15.0)
        self.assertEqual(table.loc[0.25, "MeanQty"], 40.0)
        self.assertAlmostEqual(table.loc[0.25, "DiscountDollars"], 200.0)
        self.assertAlmostEqual(
            table["ShareOfDiscountDollars"].sum(), 1.0
        )


class TestRobustness(unittest.TestCase):
    def setUp(self):
        rows = []
        order = 0
        # Ten customers. Big customers get discounts and order more,
        # but inside each order a discounted line equals a full one.
        for i in range(10):
            big = i < 5
            for _ in range(3):
                order += 1
                qty = 40 if big else 10
                disc = 0.25 if big else 0.0
                rows.append((order, f"C{i}", "X", "1998-01-01", 1, 10.0, qty, 0.0))
                rows.append((order, f"C{i}", "X", "1998-01-01", 2, 10.0, qty, disc))
        self.lines = make_lines(rows)

    def test_between_order_gap_vanishes_within_order(self):
        result = discounts.robustness(self.lines)
        self.assertEqual(result["orders_with_both"], 15)
        self.assertAlmostEqual(result["within_order_diff"], 0.0)
        self.assertEqual(result["within_order_higher"], 0)
        self.assertEqual(result["within_order_lower"], 0)
        self.assertGreater(result["lift_ci_low"], 0.0)

    def test_breakeven_for_25_vs_5(self):
        result = discounts.robustness(self.lines)
        self.assertAlmostEqual(
            result["breakeven_lift_25_vs_5"], 0.95 / 0.75 - 1
        )

    def test_intervals_are_reproducible(self):
        first = discounts.robustness(self.lines)
        second = discounts.robustness(self.lines)
        # NaN-aware: this toy data has no 5% lines, so some fields
        # are NaN, and NaN != NaN under plain equality.
        np.testing.assert_equal(first, second)


class TestInventory(unittest.TestCase):
    def test_status_labels(self):
        lines = make_lines(
            [
                (1, "A", "X", "1998-05-01", 1, 10.0, 70, 0.0),
                (2, "A", "X", "1998-05-01", 2, 10.0, 70, 0.0),
                (3, "A", "X", "1998-05-01", 3, 10.0, 70, 0.0),
                (4, "A", "X", "1998-05-01", 4, 10.0, 70, 0.0),
            ]
        )
        weekly = 70 / (inventory.DEMAND_WINDOW_DAYS / 7)
        products = pd.DataFrame(
            {
                "ProductID": [1, 2, 3, 4, 5],
                "ProductName": list("abcde"),
                "CategoryID": [1] * 5,
                "UnitsInStock": [1, 1, int(weekly * 10), 0, 5],
                "UnitsOnOrder": [0, 50, 0, 0, 0],
                "ReorderLevel": [0] * 5,
                "Discontinued": [False, False, False, True, False],
            }
        )
        cats = pd.DataFrame({"CategoryID": [1], "CategoryName": ["c"]})
        table = inventory.product_cover(lines, products, cats)
        status = dict(zip(table["ProductID"], table["Status"]))
        self.assertEqual(status[1], "Low stock, nothing on order")
        self.assertEqual(status[2], "Low stock, order inbound")
        self.assertEqual(status[3], "Adequate")
        self.assertEqual(status[4], "Discontinued, still selling")
        self.assertEqual(status[5], "Active, no recent sales")

    def test_old_sales_outside_window_ignored(self):
        lines = make_lines(
            [
                (1, "A", "X", "1997-01-01", 1, 10.0, 70, 0.0),
                (2, "A", "X", "1998-05-01", 2, 10.0, 7, 0.0),
            ]
        )
        products = pd.DataFrame(
            {
                "ProductID": [1, 2],
                "ProductName": ["a", "b"],
                "CategoryID": [1, 1],
                "UnitsInStock": [10, 10],
                "UnitsOnOrder": [0, 0],
                "ReorderLevel": [0, 0],
                "Discontinued": [False, False],
            }
        )
        cats = pd.DataFrame({"CategoryID": [1], "CategoryName": ["c"]})
        table = inventory.product_cover(lines, products, cats)
        self.assertEqual(table.loc[0, "WeeklyUnits"], 0.0)


class TestPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "outputs"
        cls.site = Path(cls.tmp.name) / "docs" / "index.html"
        cls.results = run_all.run(
            WORKBOOK, cls.out, cls.site, "https://github.com/example/repo"
        )

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_headline_numbers_are_stable(self):
        r = self.results
        self.assertEqual(r["meta"]["orders"], 830)
        self.assertAlmostEqual(r["meta"]["net_revenue"], 1265793.04, 2)
        self.assertEqual(r["q1"]["orders_prev"], 123)
        self.assertEqual(r["q1"]["orders_cur"], 256)
        self.assertAlmostEqual(r["q1"]["growth_multiple"], 2.207, 3)
        self.assertEqual(r["q2"]["customers_for_80pct"], 34)
        self.assertEqual(r["q2"]["lapsed_accounts"], 8)
        self.assertEqual(r["q2"]["largest_lapsed"], "Mère Paillarde")
        self.assertEqual(r["q3"]["lines_excluded"], 8)
        self.assertEqual(r["q3"]["orders_with_both"], 163)
        self.assertAlmostEqual(r["q3"]["within_order_diff"], 1.8228, 3)
        self.assertLess(r["q3"]["within_order_ci_low"], 0)
        self.assertLess(
            r["q3"]["depth_ci_high_pct"],
            r["q3"]["breakeven_lift_25_vs_5"],
        )
        self.assertEqual(r["q4"]["low_cover"], 28)
        self.assertEqual(r["side_check"]["late_orders"], 37)

    def test_outputs_exist(self):
        for name in (
            "q1_markets",
            "q2_customers",
            "q3_discounts",
            "q4_inventory",
        ):
            png = self.out / "figures" / f"{name}.png"
            self.assertGreater(png.stat().st_size, 20_000, name)
        self.assertTrue((self.out / "results.json").exists())
        for csv in (
            "q1_market_growth",
            "q2_revenue_by_customer",
            "q2_lapsed_accounts",
            "q3_discount_tiers",
            "q4_product_cover",
            "side_check_shippers",
        ):
            self.assertTrue((self.out / "tables" / f"{csv}.csv").exists())

    def test_results_json_round_trips(self):
        saved = json.loads(
            (self.out / "results.json").read_text(encoding="utf-8")
        )
        self.assertEqual(saved["q4"]["low_cover"], 28)

    def test_page_has_all_sections_and_no_broken_values(self):
        html = self.site.read_text(encoding="utf-8")
        for anchor in ("q1", "q2", "q3", "q4", "notes"):
            self.assertIn(f"id='{anchor}'", html.replace('"', "'"))
        text = re.sub(r"<style.*?</style>", "", html, flags=re.S)
        text = re.sub(r"data:image/png;base64,[A-Za-z0-9+/=]+", "", text)
        text = re.sub(r"<[^>]+>", " ", text)
        self.assertIsNone(re.search(r"\bnan\b|\bNone\b|\binf\b", text))
        self.assertEqual(html.count("<img "), 4)
        self.assertIn("https://github.com/example/repo", html)

    def test_every_image_has_alt_text(self):
        html = self.site.read_text(encoding="utf-8")
        for tag in re.findall(r"<img [^>]*>", html):
            self.assertRegex(tag, r"alt='[^']{20,}")

    def test_rerun_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            again = run_all.run(
                WORKBOOK, Path(tmp) / "o", Path(tmp) / "i.html"
            )
        self.assertEqual(
            json.dumps(again, default=run_all._native, sort_keys=True),
            json.dumps(
                self.results, default=run_all._native, sort_keys=True
            ),
        )


if __name__ == "__main__":
    unittest.main()
