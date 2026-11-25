"""Cross-check headline numbers with SQL instead of pandas logic."""

import json
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
TOLERANCE = 0.01


def load_database(path):
    """Copy the workbook sheets into an in-memory SQLite database.

    Args:
        path (pathlib.Path): Path to the Northwind workbook.

    Returns:
        sqlite3.Connection: Connection with tables ``orders``,
        ``details``, ``customers`` and ``product``.
    """
    con = sqlite3.connect(":memory:")
    sheets = {
        "Orders": "orders",
        "Orders Details": "details",
        "Customers": "customers",
        "Product": "product",
    }
    with pd.ExcelFile(path) as workbook:
        for sheet, name in sheets.items():
            frame = workbook.parse(sheet)
            frame = frame.astype(
                {
                    c: "string"
                    for c in frame.columns
                    if str(frame[c].dtype).startswith("datetime")
                }
            )
            frame.to_sql(name, con, index=False)
    return con


def scalar(con, sql, params=()):
    """Run a query that returns a single value.

    Args:
        con (sqlite3.Connection): Open database connection.
        sql (str): SQL text returning one row and one column.
        params (tuple[Any, ...]): Values bound to ``?`` markers.

    Returns:
        float: The single value returned by the query.
    """
    return con.execute(sql, params).fetchone()[0]


def check(label, expected, actual, failures):
    """Compare a reported number with the SQL result and print it.

    Args:
        label (str): Description shown in the output line.
        expected (float): Value reported by the pandas analysis.
        actual (float): Value recomputed with SQL.
        failures (list[str]): Collects labels of failed checks.

    Returns:
        None. Prints PASS or FAIL and appends to ``failures``.
    """
    scale = max(abs(expected), 1e-9)
    ok = abs(expected - actual) <= TOLERANCE * scale or (
        abs(expected - actual) < 0.01
    )
    print(f"{'PASS' if ok else 'FAIL'}  {label}: "
          f"{expected:,.4f} vs SQL {actual:,.4f}")
    if not ok:
        failures.append(label)


def main():
    """Verify the numbers in ``outputs/results.json`` with SQL.

    Args:
        None.

    Returns:
        None. Exits with status 1 if any check fails.
    """
    results = json.loads(
        (ROOT / "outputs" / "results.json").read_text(encoding="utf-8")
    )
    con = load_database(ROOT / "data" / "Northwind_Database.xlsx")
    net = "d.UnitPrice * d.Quantity * (1 - ROUND(d.Discount, 2))"
    join = "details d JOIN orders o ON o.OrderID = d.OrderID"
    failures = []

    total = scalar(con, f"SELECT SUM({net}) FROM {join}")
    check("Total net revenue", results["meta"]["net_revenue"], total,
          failures)
    check("Orders", results["meta"]["orders"],
          scalar(con, "SELECT COUNT(DISTINCT OrderID) FROM orders"),
          failures)

    q1 = results["q1"]
    for tag, year in (("prev", q1["prev_year"]), ("cur", q1["cur_year"])):
        sql = (
            f"SELECT SUM({net}) FROM {join} "
            "WHERE substr(o.OrderDate, 1, 4) = ? "
            "AND CAST(substr(o.OrderDate, 6, 2) AS INTEGER) <= 4"
        )
        check(f"Jan-Apr {year} revenue", q1[f"revenue_{tag}"],
              scalar(con, sql, (str(year),)), failures)
        sql = (
            "SELECT COUNT(*) FROM orders o "
            "WHERE substr(o.OrderDate, 1, 4) = ? "
            "AND CAST(substr(o.OrderDate, 6, 2) AS INTEGER) <= 4"
        )
        check(f"Jan-Apr {year} orders", q1[f"orders_{tag}"],
              scalar(con, sql, (str(year),)), failures)
    country_sql = (
        f"SELECT SUM(CASE WHEN substr(o.OrderDate,1,4)='1998' "
        f"THEN {net} ELSE -{net} END) "
        f"FROM {join} JOIN customers c ON c.CustomerID = o.CustomerID "
        "WHERE c.Country = ? AND substr(o.OrderDate,1,4) IN "
        "('1997','1998') AND CAST(substr(o.OrderDate,6,2) AS INTEGER)"
        " <= 4"
    )
    table = pd.read_csv(ROOT / "outputs" / "tables" /
                        "q1_market_growth.csv")
    for country in ("USA", "Germany", "Denmark"):
        expected = float(table.loc[table["Country"] == country,
                                   "Change"].iloc[0])
        check(f"{country} change", expected,
              scalar(con, country_sql, (country,)), failures)

    monthly = pd.read_csv(ROOT / "outputs" / "tables" /
                          "q1_monthly_revenue.csv")
    for label in ("1997-01", "1998-04", "1998-05"):
        row = monthly[monthly["Month"].str.startswith(label)].iloc[0]
        check(f"Monthly revenue {label}", float(row["Revenue"]),
              scalar(con, f"SELECT SUM({net}) FROM {join} "
                     "WHERE substr(o.OrderDate, 1, 7) = ?", (label,)),
              failures)
    check("Sum of monthly revenue", float(monthly["Revenue"].sum()),
          total, failures)

    top3 = con.execute(
        f"SELECT SUM(rev) FROM (SELECT SUM({net}) AS rev FROM {join} "
        "GROUP BY o.CustomerID ORDER BY rev DESC LIMIT 3)"
    ).fetchone()[0]
    check("Top-3 customer share", results["q2"]["top3_share"],
          top3 / total, failures)

    q3 = results["q3"]
    qty_sql = (
        "SELECT AVG(Quantity) FROM details WHERE {}"
    )
    check("Mean units, no discount", q3["mean_qty_none"],
          scalar(con, qty_sql.format("ROUND(Discount, 2) = 0")),
          failures)
    check("Mean units, discounted", q3["mean_qty_discounted"],
          scalar(con, qty_sql.format(
              "ROUND(Discount, 2) IN (0.05, 0.1, 0.15, 0.2, 0.25)")),
          failures)
    check("Discount dollars (6 tiers)", q3["total_discount_dollars"],
          scalar(con, "SELECT SUM(UnitPrice * Quantity * "
                 "ROUND(Discount, 2)) FROM details WHERE "
                 "ROUND(Discount, 2) IN (0, 0.05, 0.1, 0.15, 0.2, 0.25)"),
          failures)

    tiers = "(0, 0.05, 0.1, 0.15, 0.2, 0.25)"
    mixed = (
        "WITH t AS (SELECT OrderID, "
        "AVG(CASE WHEN r = 0 THEN Quantity END) AS f, "
        "AVG(CASE WHEN r > 0 THEN Quantity END) AS d "
        "FROM (SELECT OrderID, Quantity, ROUND(Discount, 2) AS r "
        f"FROM details WHERE ROUND(Discount, 2) IN {tiers}) "
        "GROUP BY OrderID HAVING f IS NOT NULL AND d IS NOT NULL) "
    )
    check("Within-order orders with both",
          q3["orders_with_both"],
          scalar(con, mixed + "SELECT COUNT(*) FROM t"), failures)
    check("Within-order mean difference (units)",
          q3["within_order_diff"],
          scalar(con, mixed + "SELECT AVG(d - f) FROM t"), failures)
    check("Within-order: discounted line larger",
          q3["within_order_higher"],
          scalar(con, mixed + "SELECT SUM(d > f) FROM t"), failures)
    check("Within-order: discounted line smaller",
          q3["within_order_lower"],
          scalar(con, mixed + "SELECT SUM(d < f) FROM t"), failures)
    check("Full-price units, orders with a discounted line",
          q3["full_in_mixed_orders"],
          scalar(con, mixed + "SELECT AVG(Quantity) FROM details "
                 "WHERE ROUND(Discount, 2) = 0 "
                 "AND OrderID IN (SELECT OrderID FROM t)"), failures)
    check("Full-price units, orders with no discount",
          q3["full_in_plain_orders"],
          scalar(con, "SELECT AVG(Quantity) FROM details "
                 "WHERE ROUND(Discount, 2) = 0 AND OrderID NOT IN "
                 "(SELECT OrderID FROM details WHERE ROUND(Discount, 2)"
                 " IN (0.05, 0.1, 0.15, 0.2, 0.25))"), failures)

    end = scalar(con, "SELECT MAX(OrderDate) FROM orders")
    recent = (
        f"SELECT SUM(d.Quantity) FROM {join} "
        f"WHERE o.OrderDate > date(?, '-120 days') AND d.ProductID = ?"
    )
    cover = pd.read_csv(ROOT / "outputs" / "tables" /
                        "q4_product_cover.csv")
    for name in ("Côte de Blaye", "Chang"):
        row = cover[cover["ProductName"] == name].iloc[0]
        units = scalar(con, recent, (end[:10], int(row["ProductID"])))
        check(f"{name} weekly units", float(row["WeeklyUnits"]),
              units / (120 / 7), failures)

    late = scalar(
        con,
        "SELECT SUM(ShippedDate > RequiredDate) FROM orders "
        "WHERE ShippedDate IS NOT NULL",
    )
    check("Late shipped orders", results["side_check"]["late_orders"],
          late, failures)

    print()
    if failures:
        print(f"{len(failures)} check(s) FAILED: {failures}")
        sys.exit(1)
    print("All SQL cross-checks passed.")


if __name__ == "__main__":
    main()
