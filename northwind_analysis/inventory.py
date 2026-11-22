"""Question 4: which products risk running out of stock."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from northwind_analysis import plotting

DEMAND_WINDOW_DAYS = 120
COVER_ALERT_WEEKS = 2.0
LOW_STATUSES = ("Low stock, nothing on order", "Low stock, order inbound")


def product_cover(lines, products, categories):
    """Estimate weeks of stock cover for every product.

    Weekly demand is the average over the last
    ``DEMAND_WINDOW_DAYS`` days of order history. The Product sheet
    has no date, so its stock levels are assumed current as of the
    last order.

    Args:
        lines (pandas.DataFrame): Order lines from
            ``data.build_order_lines``.
        products (pandas.DataFrame): The ``Product`` sheet.
        categories (pandas.DataFrame): The ``Categories`` sheet.

    Returns:
        pandas.DataFrame: One row per product with stock, units on
        order, weekly units and revenue, weeks of cover with and
        without units on order, and a ``Status`` label.
    """
    end = lines["OrderDate"].max()
    recent = lines[
        lines["OrderDate"] > end - pd.Timedelta(days=DEMAND_WINDOW_DAYS)
    ]
    weeks = DEMAND_WINDOW_DAYS / 7
    demand = recent.groupby("ProductID").agg(
        Units=("Quantity", "sum"), Revenue=("NetRevenue", "sum")
    )
    cols = [
        "ProductID",
        "ProductName",
        "CategoryID",
        "UnitsInStock",
        "UnitsOnOrder",
        "ReorderLevel",
        "Discontinued",
    ]
    table = (
        products[cols]
        .merge(
            categories[["CategoryID", "CategoryName"]],
            on="CategoryID",
            how="left",
        )
        .merge(demand, on="ProductID", how="left")
        .fillna({"Units": 0, "Revenue": 0})
    )
    table["Discontinued"] = table["Discontinued"].astype(bool)
    table["WeeklyUnits"] = table["Units"] / weeks
    table["WeeklyRevenue"] = table["Revenue"] / weeks
    selling = table["WeeklyUnits"] > 0
    table["WeeksCover"] = (
        table["UnitsInStock"] / table["WeeklyUnits"]
    ).where(selling)
    table["WeeksCoverWithOrder"] = (
        (table["UnitsInStock"] + table["UnitsOnOrder"])
        / table["WeeklyUnits"]
    ).where(selling)
    low = table["WeeksCover"] < COVER_ALERT_WEEKS
    table["Status"] = np.select(
        [
            table["Discontinued"] & selling,
            table["Discontinued"],
            ~selling,
            low & (table["UnitsOnOrder"] == 0),
            low,
        ],
        [
            "Discontinued, still selling",
            "Discontinued, no recent sales",
            "Active, no recent sales",
            LOW_STATUSES[0],
            LOW_STATUSES[1],
        ],
        default="Adequate",
    )
    return table


def inventory_summary(table):
    """Summarise stock-out exposure and discontinued-product sales.

    Args:
        table (pandas.DataFrame): Output of ``product_cover``.

    Returns:
        dict[str, Any]: Counts of active selling products and of
        those with low cover, weekly revenue exposed, and the sales
        and stock position of discontinued products still selling.
    """
    active = table[~table["Discontinued"] & (table["WeeklyUnits"] > 0)]
    low = active[active["Status"].isin(LOW_STATUSES)]
    none_ordered = active[active["Status"] == LOW_STATUSES[0]]
    gone = table[table["Status"] == "Discontinued, still selling"]
    empty = gone[gone["UnitsInStock"] == 0]
    total_weekly = float(table["WeeklyRevenue"].sum())
    return {
        "window_days": DEMAND_WINDOW_DAYS,
        "alert_weeks": COVER_ALERT_WEEKS,
        "active_selling": int(len(active)),
        "low_cover": int(len(low)),
        "low_cover_share": float(len(low) / len(active)),
        "low_cover_weekly_revenue": float(low["WeeklyRevenue"].sum()),
        "low_cover_revenue_share": float(
            low["WeeklyRevenue"].sum() / active["WeeklyRevenue"].sum()
        ),
        "nothing_on_order": int(len(none_ordered)),
        "nothing_on_order_weekly_revenue": float(
            none_ordered["WeeklyRevenue"].sum()
        ),
        "discontinued_selling": int(len(gone)),
        "discontinued_weekly_revenue": float(gone["WeeklyRevenue"].sum()),
        "discontinued_revenue_share": float(
            gone["WeeklyRevenue"].sum() / total_weekly
        ),
        "discontinued_out_of_stock": int(len(empty)),
        "discontinued_out_of_stock_weekly_revenue": float(
            empty["WeeklyRevenue"].sum()
        ),
    }


def plot_inventory(table, path, top_n=12):
    """Draw weeks of cover for the best-selling low-stock products.

    Args:
        table (pandas.DataFrame): Output of ``product_cover``.
        path (str | pathlib.Path): Output PNG path.
        top_n (int): Number of products shown, by weekly revenue.

    Returns:
        pathlib.Path: The path that was written.
    """
    plotting.apply_style()
    colors = plotting.COLORS
    risk = (
        table[table["Status"].isin(LOW_STATUSES)]
        .nlargest(top_n, "WeeklyRevenue")
        .iloc[::-1]
        .reset_index(drop=True)
    )
    fig, ax = plt.subplots(figsize=(10.5, 6))
    inbound = risk["WeeksCoverWithOrder"] - risk["WeeksCover"]
    ax.barh(
        risk["ProductName"],
        risk["WeeksCover"],
        color=colors["blue"],
        label="Weeks of cover in stock",
    )
    ax.barh(
        risk["ProductName"],
        inbound,
        left=risk["WeeksCover"],
        color=colors["light_blue"],
        hatch="//",
        edgecolor="white",
        label="Extra weeks if units on order arrive",
    )
    ax.axvline(
        COVER_ALERT_WEEKS,
        color=colors["orange"],
        linestyle="--",
        linewidth=1.6,
    )
    ax.text(
        COVER_ALERT_WEEKS + 0.05,
        len(risk) - 0.35,
        "2-week alert line",
        color=colors["orange"],
        fontsize=10,
        va="bottom",
    )
    reach = risk["WeeksCoverWithOrder"].max()
    ax.set_xlim(0, reach * 1.55)
    ax.set_ylim(-0.6, len(risk) + 0.5)
    for row, item in risk.iterrows():
        ax.text(
            0.995,
            row,
            f"{item['WeeksCover']:.1f} wks  |  "
            f"{plotting.money(item['WeeklyRevenue'])}/wk",
            transform=ax.get_yaxis_transform(),
            ha="right",
            va="center",
            fontsize=9,
        )
    ax.text(
        0.995,
        len(risk) - 0.35,
        "In-stock cover  |  sales",
        transform=ax.get_yaxis_transform(),
        ha="right",
        va="bottom",
        fontsize=9,
        fontweight="bold",
    )
    ax.set_xlabel("Weeks of cover at the last 120 days' sales rate")
    ax.set_title(
        "Best-selling products with under two weeks of stock",
        loc="left",
        pad=14,
    )
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.45, -0.14),
        ncol=2,
        frameon=False,
    )
    fig.tight_layout()
    return plotting.save_figure(fig, path)
