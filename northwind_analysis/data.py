"""Load the Northwind workbook and build the order-line table."""

from pathlib import Path

import pandas as pd

SHEETS = (
    "Customers",
    "Orders",
    "Orders Details",
    "Product",
    "Categories",
    "Shippers",
)


def load_tables(path):
    """Read the needed Northwind sheets from the Excel workbook.

    Args:
        path (str | pathlib.Path): Path to Northwind_Database.xlsx.

    Returns:
        dict[str, pandas.DataFrame]: Sheet name mapped to its table.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Workbook not found: {path}")
    with pd.ExcelFile(path) as workbook:
        return {name: workbook.parse(name) for name in SHEETS}


def build_order_lines(tables):
    """Join order details to orders and customers; add revenue.

    Revenue uses the price actually charged on each order line
    (``Orders Details.UnitPrice``), not ``Product.Price``, which
    differs on about 31% of lines. Discounts are rounded to two
    decimals to remove floating-point noise (0.0500000007 -> 0.05).

    Args:
        tables (dict[str, pandas.DataFrame]): Output of
            ``load_tables``.

    Returns:
        pandas.DataFrame: One row per order line with gross revenue,
        discount amount, net revenue, order and customer fields, and
        ``Year`` and ``Month`` of the order.

    Raises:
        ValueError: If any order line fails to match an order or a
            customer.
    """
    lines = tables["Orders Details"].copy()
    lines["Discount"] = lines["Discount"].round(2)
    lines["GrossRevenue"] = lines["UnitPrice"] * lines["Quantity"]
    lines["DiscountAmount"] = lines["GrossRevenue"] * lines["Discount"]
    lines["NetRevenue"] = (
        lines["GrossRevenue"] - lines["DiscountAmount"]
    )
    order_cols = [
        "OrderID",
        "CustomerID",
        "OrderDate",
        "RequiredDate",
        "ShippedDate",
        "Freight",
        "ShipVia",
    ]
    lines = lines.merge(
        tables["Orders"][order_cols],
        on="OrderID",
        how="left",
        validate="many_to_one",
    )
    lines = lines.merge(
        tables["Customers"][["CustomerID", "CompanyName", "Country"]],
        on="CustomerID",
        how="left",
        validate="many_to_one",
    )
    if lines[["CustomerID", "Country"]].isna().any().any():
        raise ValueError("Some order lines have no order or customer.")
    lines["Year"] = lines["OrderDate"].dt.year
    lines["Month"] = lines["OrderDate"].dt.month
    return lines


def data_checks(tables):
    """Measure two data-quality facts that justify modelling choices.

    Args:
        tables (dict[str, pandas.DataFrame]): Output of
            ``load_tables``.

    Returns:
        dict[str, float]: ``price_mismatch_share``, the share of
        order lines whose charged price differs from
        ``Product.Price``, and ``ship_country_match_share``, the
        share of orders shipped to the customer's own country.
    """
    details = tables["Orders Details"].merge(
        tables["Product"][["ProductID", "Price"]], on="ProductID"
    )
    orders = tables["Orders"].merge(
        tables["Customers"][["CustomerID", "Country"]], on="CustomerID"
    )
    return {
        "price_mismatch_share": float(
            (details["UnitPrice"] != details["Price"]).mean()
        ),
        "ship_country_match_share": float(
            (orders["ShipCountry"] == orders["Country"]).mean()
        ),
    }


def comparison_window(order_dates):
    """Pick matching months for a fair year-over-year comparison.

    The data stop part-way through a month, so the final partial
    month is dropped. Months January through the last complete month
    are then compared across the latest year and the year before it.

    Args:
        order_dates (pandas.Series): Order timestamps.

    Returns:
        tuple[int, int, int]: Previous year, current year, and the
        last complete calendar month (1-12) of the current year.
    """
    last = order_dates.max().normalize()
    month_end = last + pd.offsets.MonthEnd(0)
    if last == month_end:
        complete = last
    else:
        complete = last.replace(day=1) - pd.Timedelta(days=1)
    return complete.year - 1, complete.year, complete.month
