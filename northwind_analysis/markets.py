"""Question 1: which customer markets are growing or declining."""

import calendar

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

from northwind_analysis import plotting

MIN_BASE = 2500.0
DRIVER_MIN_GROWTH = 5000.0
TOP_N = 5


def market_growth(lines, prev_year, cur_year, last_month):
    """Compare country revenue across the same months of two years.

    Args:
        lines (pandas.DataFrame): Order lines from
            ``data.build_order_lines``.
        prev_year (int): Earlier year of the comparison.
        cur_year (int): Later year of the comparison.
        last_month (int): Last calendar month (1-12) included.

    Returns:
        pandas.DataFrame: One row per country with revenue in each
            year, change, percent change (NaN when the earlier
            revenue is under ``MIN_BASE``), share of total growth,
            active customers, and the account behind most of the
            change. The account's share of the change is NaN unless
            the country grew by at least ``DRIVER_MIN_GROWTH``,
            because shares of a tiny or negative net change are
            not meaningful.
    """
    years = [prev_year, cur_year]
    window = lines[
        (lines["Month"] <= last_month) & lines["Year"].isin(years)
    ]
    by_country = window.pivot_table(
        index="Country",
        columns="Year",
        values="NetRevenue",
        aggfunc="sum",
        fill_value=0.0,
    ).reindex(columns=years, fill_value=0.0)
    table = pd.DataFrame(
        {
            "RevenuePrev": by_country[prev_year],
            "RevenueCur": by_country[cur_year],
        }
    )
    table["Change"] = table["RevenueCur"] - table["RevenuePrev"]
    pct = table["Change"] / table["RevenuePrev"].replace(0, np.nan)
    table["PctChange"] = pct.where(table["RevenuePrev"] >= MIN_BASE)
    table["ShareOfGrowth"] = table["Change"] / table["Change"].sum()
    active = (
        window[window["Year"] == cur_year]
        .groupby("Country")["CustomerID"]
        .nunique()
    )
    table["ActiveCustomers"] = (
        active.reindex(table.index).fillna(0).astype(int)
    )
    by_account = window.pivot_table(
        index=["Country", "CompanyName"],
        columns="Year",
        values="NetRevenue",
        aggfunc="sum",
        fill_value=0.0,
    ).reindex(columns=years, fill_value=0.0)
    by_account["Change"] = by_account[cur_year] - by_account[prev_year]
    drivers = {}
    for country, group in by_account.groupby(level="Country"):
        change = group["Change"]
        total = change.sum()
        key = change.idxmax() if total >= 0 else change.idxmin()
        share = (
            change.loc[key] / total
            if total >= DRIVER_MIN_GROWTH
            else np.nan
        )
        drivers[country] = (key[1], share)
    table = table.join(
        pd.DataFrame.from_dict(
            drivers,
            orient="index",
            columns=["DriverAccount", "DriverShareOfChange"],
        )
    )
    return table.sort_values("Change", ascending=False).reset_index()


def growth_summary(lines, table, prev_year, cur_year, last_month):
    """Summarise overall growth and where it came from.

    Args:
        lines (pandas.DataFrame): Order lines from
            ``data.build_order_lines``.
        table (pandas.DataFrame): Output of ``market_growth``.
        prev_year (int): Earlier year of the comparison.
        cur_year (int): Later year of the comparison.
        last_month (int): Last calendar month (1-12) included.

    Returns:
        dict[str, Any]: Revenue, orders, average order value and
        active customers for each year, growth ratios, the top
        growth markets and their share of growth, and counts of
        growing and declining markets.
    """
    window = lines[lines["Month"] <= last_month]
    out = {
        "prev_year": int(prev_year),
        "cur_year": int(cur_year),
        "window": f"Jan–{calendar.month_abbr[last_month]}",
    }
    for tag, year in (("prev", prev_year), ("cur", cur_year)):
        part = window[window["Year"] == year]
        revenue = float(part["NetRevenue"].sum())
        orders = int(part["OrderID"].nunique())
        out[f"revenue_{tag}"] = revenue
        out[f"orders_{tag}"] = orders
        out[f"customers_{tag}"] = int(part["CustomerID"].nunique())
        out[f"aov_{tag}"] = revenue / orders
    out["growth_multiple"] = out["revenue_cur"] / out["revenue_prev"]
    out["orders_growth"] = out["orders_cur"] / out["orders_prev"] - 1
    out["aov_growth"] = out["aov_cur"] / out["aov_prev"] - 1
    top = table.nlargest(TOP_N, "Change")
    out["top_markets"] = top["Country"].tolist()
    out["top_markets_share_of_growth"] = float(top["ShareOfGrowth"].sum())
    out["markets_up"] = int((table["Change"] > 0).sum())
    out["markets_down"] = int((table["Change"] < 0).sum())
    out["markets_total"] = int(len(table))
    return out


def plot_market_growth(table, summary, path):
    """Draw revenue change by country as a ranked bar chart.

    Args:
        table (pandas.DataFrame): Output of ``market_growth``.
        summary (dict[str, Any]): Output of ``growth_summary``.
        path (str | pathlib.Path): Output PNG path.

    Returns:
        pathlib.Path: The path that was written.
    """
    plotting.apply_style()
    colors = plotting.COLORS
    data = table.sort_values("Change").reset_index(drop=True)
    count = len(data)
    fig, ax = plt.subplots(figsize=(10.5, 8.4))
    ax.barh(
        data["Country"],
        data["Change"],
        color=[colors["blue"] if v >= 0 else colors["orange"]
               for v in data["Change"]],
    )
    ax.axvline(0, color=colors["dark"], linewidth=0.8)
    low = min(data["Change"].min(), 0.0)
    high = data["Change"].max()
    span = high - low
    ax.set_xlim(low - 0.04 * span, high + 0.66 * span)
    ax.set_ylim(-0.7, count + 0.5)
    ax.xaxis.set_major_formatter(FuncFormatter(plotting.money))
    for row, item in data.iterrows():
        change = item["Change"]
        if pd.notna(item["PctChange"]):
            note = f" ({item['PctChange']:+.0%})"
        elif item["RevenuePrev"] == 0:
            note = " (no sales before)"
        else:
            note = " (small base)"
        sign = "+" if change >= 0 else ""
        label = f"{sign}{plotting.money(change)}{note}"
        offset = 0.012 * span
        ax.text(
            max(change, 0.0) + offset,
            row,
            label,
            va="center",
            ha="left",
            fontsize=9,
        )
        if pd.notna(item["DriverShareOfChange"]):
            ax.text(
                0.995,
                row,
                f"{item['DriverShareOfChange']:.0%}",
                transform=ax.get_yaxis_transform(),
                ha="right",
                va="center",
                fontsize=9,
                color=colors["dark"],
            )
    ax.text(
        0.995,
        count - 0.1,
        "Largest account's\nshare of the growth",
        transform=ax.get_yaxis_transform(),
        ha="right",
        va="bottom",
        fontsize=9,
        fontweight="bold",
    )
    ax.set_xlabel(
        f"Change in net revenue, {summary['window']} "
        f"{summary['cur_year']} vs {summary['prev_year']} (USD)"
    )
    ax.set_title(
        "Revenue change by customer country", loc="left", pad=16
    )
    ax.legend(
        handles=[
            Patch(color=colors["blue"], label="Growth"),
            Patch(color=colors["orange"], label="Decline"),
        ],
        loc="lower right",
        bbox_to_anchor=(0.88, 0.02),
        frameon=False,
    )
    fig.text(
        0.01,
        -0.02,
        f"Percent change is shown only where the earlier-year "
        f"revenue was at least {MIN_BASE:,.0f} USD. Account share is "
        f"shown only for markets that grew by at least "
        f"{DRIVER_MIN_GROWTH:,.0f} USD.",
        fontsize=9,
        color=colors["grey"],
    )
    return plotting.save_figure(fig, path)
