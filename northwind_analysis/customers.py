"""Question 2: how concentrated is revenue, and who is lapsing."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

from northwind_analysis import plotting

IDLE_FLOOR_DAYS = 90
IDLE_GAP_MULTIPLE = 3
TRAILING_DAYS = 365


def revenue_by_customer(lines):
    """Rank customers by lifetime net revenue.

    Args:
        lines (pandas.DataFrame): Order lines from
            ``data.build_order_lines``.

    Returns:
        pandas.DataFrame: One row per customer, largest first, with
        revenue, share of total, cumulative share, and rank.
    """
    table = (
        lines.groupby(
            ["CustomerID", "CompanyName", "Country"], as_index=False
        )["NetRevenue"]
        .sum()
        .rename(columns={"NetRevenue": "Revenue"})
        .sort_values("Revenue", ascending=False)
        .reset_index(drop=True)
    )
    table["Rank"] = table.index + 1
    table["Share"] = table["Revenue"] / table["Revenue"].sum()
    table["CumShare"] = table["Share"].cumsum()
    return table


def concentration_summary(
    by_customer, lines, prev_year, cur_year, last_month
):
    """Measure how much revenue the largest customers account for.

    Args:
        by_customer (pandas.DataFrame): Output of
            ``revenue_by_customer``.
        lines (pandas.DataFrame): Order lines from
            ``data.build_order_lines``.
        prev_year (int): Earlier year of the like-for-like check.
        cur_year (int): Later year of the like-for-like check.
        last_month (int): Last calendar month (1-12) included.

    Returns:
        dict[str, Any]: Lifetime top-1, top-3, top-10 and top-20
        shares, customers needed for 80% of revenue, the top-3
        names, and top-3 and top-10 shares in each comparison year.
    """
    out = {
        "customers": int(len(by_customer)),
        "top3_names": by_customer["CompanyName"].head(3).tolist(),
        "top1_share": float(by_customer["Share"].iloc[0]),
        "top3_share": float(by_customer["Share"].head(3).sum()),
        "top10_share": float(by_customer["Share"].head(10).sum()),
        "top20_share": float(by_customer["Share"].head(20).sum()),
        "customers_for_80pct": int(
            (by_customer["CumShare"] < 0.8).sum() + 1
        ),
    }
    for tag, year in (("prev", prev_year), ("cur", cur_year)):
        part = lines[
            (lines["Year"] == year) & (lines["Month"] <= last_month)
        ]
        revenue = (
            part.groupby("CustomerID")["NetRevenue"]
            .sum()
            .sort_values(ascending=False)
        )
        out[f"top3_share_{tag}"] = float(
            revenue.head(3).sum() / revenue.sum()
        )
        out[f"top10_share_{tag}"] = float(
            revenue.head(10).sum() / revenue.sum()
        )
    return out


def lapsed_accounts(lines):
    """Flag customers silent for much longer than their usual gap.

    A customer is flagged when the days since their last order
    exceed the larger of ``IDLE_FLOOR_DAYS`` and
    ``IDLE_GAP_MULTIPLE`` times their own median gap between orders.
    "Today" is the date of the latest order in the data.

    Args:
        lines (pandas.DataFrame): Order lines from
            ``data.build_order_lines``.

    Returns:
        pandas.DataFrame: One row per customer with order count,
        last order, idle days, typical gap, threshold, lifetime and
        trailing-year revenue, and a ``Lapsed`` flag.
    """
    end = lines["OrderDate"].max()
    orders = lines.drop_duplicates("OrderID")[
        ["OrderID", "CustomerID", "OrderDate"]
    ]
    rows = []
    for customer, group in orders.groupby("CustomerID"):
        dates = group["OrderDate"].sort_values()
        gaps = dates.diff().dropna().dt.days
        rows.append(
            {
                "CustomerID": customer,
                "Orders": int(len(dates)),
                "LastOrder": dates.iloc[-1],
                "IdleDays": int((end - dates.iloc[-1]).days),
                "TypicalGapDays": (
                    float(gaps.median()) if len(gaps) >= 2 else np.nan
                ),
            }
        )
    table = pd.DataFrame(rows)
    names = lines.drop_duplicates("CustomerID")[
        ["CustomerID", "CompanyName", "Country"]
    ]
    table = table.merge(names, on="CustomerID")
    table["ThresholdDays"] = np.maximum(
        IDLE_FLOOR_DAYS,
        IDLE_GAP_MULTIPLE * table["TypicalGapDays"].fillna(0),
    )
    table["Lapsed"] = table["IdleDays"] > table["ThresholdDays"]
    lifetime = lines.groupby("CustomerID")["NetRevenue"].sum()
    recent = lines[
        lines["OrderDate"] > end - pd.Timedelta(days=TRAILING_DAYS)
    ]
    trailing = recent.groupby("CustomerID")["NetRevenue"].sum()
    table["LifetimeRevenue"] = table["CustomerID"].map(lifetime)
    table["TrailingYearRevenue"] = (
        table["CustomerID"].map(trailing).fillna(0.0)
    )
    return table.sort_values(
        ["Lapsed", "LifetimeRevenue"], ascending=[False, False]
    ).reset_index(drop=True)


def lapse_summary(lapsed):
    """Summarise the lapsed-account flags.

    Args:
        lapsed (pandas.DataFrame): Output of ``lapsed_accounts``.

    Returns:
        dict[str, Any]: Number of lapsed accounts, their share of
        trailing-year revenue, and the largest lapsed account.
    """
    flagged = lapsed[lapsed["Lapsed"]]
    top = flagged.iloc[0]
    return {
        "lapsed_accounts": int(len(flagged)),
        "lapsed_trailing_share": float(
            flagged["TrailingYearRevenue"].sum()
            / lapsed["TrailingYearRevenue"].sum()
        ),
        "lapsed_trailing_revenue": float(
            flagged["TrailingYearRevenue"].sum()
        ),
        "largest_lapsed": top["CompanyName"],
        "largest_lapsed_country": top["Country"],
        "largest_lapsed_idle_days": int(top["IdleDays"]),
        "largest_lapsed_typical_gap": float(top["TypicalGapDays"]),
        "largest_lapsed_trailing": float(top["TrailingYearRevenue"]),
        "largest_lapsed_lifetime": float(top["LifetimeRevenue"]),
    }


def plot_concentration(by_customer, lapsed, summary, path):
    """Draw the revenue concentration curve and top-10 customers.

    Args:
        by_customer (pandas.DataFrame): Output of
            ``revenue_by_customer``.
        lapsed (pandas.DataFrame): Output of ``lapsed_accounts``.
        summary (dict[str, Any]): Output of
            ``concentration_summary``.
        path (str | pathlib.Path): Output PNG path.

    Returns:
        pathlib.Path: The path that was written.
    """
    plotting.apply_style()
    colors = plotting.COLORS
    fig, (left, right) = plt.subplots(
        1, 2, figsize=(12, 5.4), gridspec_kw={"width_ratios": [1, 1.2]}
    )
    count = len(by_customer)
    ranks = np.arange(1, count + 1)
    cumulative = by_customer["CumShare"].to_numpy() * 100
    left.plot(ranks, cumulative, color=colors["blue"], linewidth=2.4)
    for k in (3, 10, summary["customers_for_80pct"]):
        left.scatter(k, cumulative[k - 1], color=colors["dark"], zorder=3)
        left.annotate(
            f"Top {k}: {cumulative[k - 1]:.0f}%",
            (k, cumulative[k - 1]),
            textcoords="offset points",
            xytext=(10, -14),
            fontsize=10,
        )
    left.set_xlim(0, count)
    left.set_ylim(0, 102)
    left.set_xlabel("Customers ranked by lifetime revenue (1 = largest)")
    left.set_ylabel("Cumulative share of revenue (%)")
    left.set_title("A few accounts carry the business", loc="left")
    top = by_customer.head(10).iloc[::-1]
    flagged = set(lapsed.loc[lapsed["Lapsed"], "CustomerID"])
    bar_colors = [
        colors["orange"] if c in flagged else colors["blue"]
        for c in top["CustomerID"]
    ]
    labels = [
        f"{name[:30]} ({country})"
        for name, country in zip(top["CompanyName"], top["Country"])
    ]
    right.barh(labels, top["Revenue"], color=bar_colors)
    right.xaxis.set_major_formatter(FuncFormatter(plotting.money))
    right.set_xlabel("Lifetime net revenue (USD)")
    right.set_title("Ten largest customers", loc="left")
    right.legend(
        handles=[
            Patch(color=colors["blue"], label="Ordering normally"),
            Patch(
                color=colors["orange"],
                label="Silent much longer than usual",
            ),
        ],
        loc="lower right",
        frameon=False,
    )
    fig.tight_layout()
    return plotting.save_figure(fig, path)
