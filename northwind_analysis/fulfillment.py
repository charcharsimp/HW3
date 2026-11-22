"""Side check: delivery timeliness and freight cost by shipper."""

import pandas as pd
from scipy import stats


def fulfillment_summary(tables, lines):
    """Measure on-time shipping and compare the three shippers.

    An order is late when it shipped after its required date. Open
    orders with no ship date are counted but not scored.

    Args:
        tables (dict[str, pandas.DataFrame]): Output of
            ``data.load_tables``.
        lines (pandas.DataFrame): Order lines from
            ``data.build_order_lines``.

    Returns:
        tuple[dict[str, Any], pandas.DataFrame]: Overall results
        (on-time rate, open orders, chi-square p-value across
        shippers, freight as a share of revenue) and a per-shipper
        table of orders, late rate, days to ship and freight.
    """
    orders = tables["Orders"]
    shipped = orders.dropna(subset=["ShippedDate"]).copy()
    shipped["Late"] = shipped["ShippedDate"] > shipped["RequiredDate"]
    shipped["DaysToShip"] = (
        shipped["ShippedDate"] - shipped["OrderDate"]
    ).dt.days
    shipped = shipped.merge(
        tables["Shippers"][["ShipperID", "CompanyName"]],
        left_on="ShipVia",
        right_on="ShipperID",
    )
    by_shipper = (
        shipped.groupby("CompanyName")
        .agg(
            Orders=("OrderID", "size"),
            LateOrders=("Late", "sum"),
            LateRate=("Late", "mean"),
            MeanDaysToShip=("DaysToShip", "mean"),
            MeanFreight=("Freight", "mean"),
        )
        .reset_index()
    )
    contingency = pd.crosstab(shipped["ShipVia"], shipped["Late"])
    chi_p = stats.chi2_contingency(contingency)[1]
    summary = {
        "orders_shipped": int(len(shipped)),
        "late_orders": int(shipped["Late"].sum()),
        "on_time_rate": float(1 - shipped["Late"].mean()),
        "open_orders": int(orders["ShippedDate"].isna().sum()),
        "shipper_chi2_p": float(chi_p),
        "freight_share_of_revenue": float(
            orders["Freight"].sum() / lines["NetRevenue"].sum()
        ),
    }
    return summary, by_shipper
