"""Question 3: what do discounts buy, and what do they cost."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter
from scipy import stats

from northwind_analysis import plotting

TIERS = (0.0, 0.05, 0.10, 0.15, 0.20, 0.25)
BASE_DISCOUNT = 0.05
BOOTSTRAP_DRAWS = 2000
SEED = 20261122


def tier_lines(lines):
    """Keep order lines at the six standard discount levels.

    Eight lines carry other discounts (1-4% and 6%) on one to three
    units each; they are left out of the tier analysis.

    Args:
        lines (pandas.DataFrame): Order lines from
            ``data.build_order_lines``.

    Returns:
        pandas.DataFrame: The lines whose discount is 0, 5, 10, 15,
        20 or 25 percent.
    """
    return lines[lines["Discount"].isin(TIERS)]


def tier_table(lines):
    """Summarise quantity and cost at each discount level.

    Args:
        lines (pandas.DataFrame): Order lines from
            ``data.build_order_lines``.

    Returns:
        pandas.DataFrame: One row per discount level with line
        count, mean and median units per line, a 95% confidence
        interval for the mean, discount dollars given, each tier's
        share of those dollars, and net revenue per line.
    """
    rows = []
    for tier, group in tier_lines(lines).groupby("Discount"):
        qty = group["Quantity"]
        count = len(qty)
        half = stats.t.ppf(0.975, count - 1) * qty.std(ddof=1) / np.sqrt(
            count
        )
        rows.append(
            {
                "Discount": float(tier),
                "Lines": int(count),
                "MeanQty": float(qty.mean()),
                "CILow": float(qty.mean() - half),
                "CIHigh": float(qty.mean() + half),
                "MedianQty": float(qty.median()),
                "DiscountDollars": float(group["DiscountAmount"].sum()),
                "NetRevenue": float(group["NetRevenue"].sum()),
                "NetRevenuePerLine": float(group["NetRevenue"].mean()),
            }
        )
    table = pd.DataFrame(rows)
    table["ShareOfDiscountDollars"] = (
        table["DiscountDollars"] / table["DiscountDollars"].sum()
    )
    return table


def discount_tests(lines):
    """Test whether discounts, and deeper discounts, lift quantity.

    Args:
        lines (pandas.DataFrame): Order lines from
            ``data.build_order_lines``.

    Returns:
        dict[str, Any]: Mean units with and without a discount and
        Welch and Mann-Whitney p-values; Kruskal-Wallis and Spearman
        results across the 5-25% tiers; a within-product paired
        comparison; and the dollars given beyond a 5% discount.
    """
    used = tier_lines(lines)
    none = used.loc[used["Discount"] == 0, "Quantity"]
    some = used.loc[used["Discount"] > 0, "Quantity"]
    welch = stats.ttest_ind(some, none, equal_var=False)
    mann = stats.mannwhitneyu(some, none, alternative="two-sided")
    tiers = [
        used.loc[used["Discount"] == t, "Quantity"] for t in TIERS[1:]
    ]
    kruskal = stats.kruskal(*tiers)
    deep = used[used["Discount"] > 0]
    spearman = stats.spearmanr(deep["Discount"], deep["Quantity"])
    low = used.loc[used["Discount"] == BASE_DISCOUNT, "Quantity"]
    high = used.loc[used["Discount"] == TIERS[-1], "Quantity"]
    low_vs_high = stats.mannwhitneyu(low, high, alternative="two-sided")
    paired = (
        used.assign(Discounted=used["Discount"] > 0)
        .groupby(["ProductID", "Discounted"])["Quantity"]
        .mean()
        .unstack()
        .dropna()
    )
    wilcoxon = stats.wilcoxon(paired[True], paired[False])
    excess = float(
        (
            used["GrossRevenue"]
            * (used["Discount"] - BASE_DISCOUNT).clip(lower=0)
        ).sum()
    )
    total_discount = float(used["DiscountAmount"].sum())
    return {
        "lines_used": int(len(used)),
        "lines_excluded": int(len(lines) - len(used)),
        "share_lines_discounted": float((used["Discount"] > 0).mean()),
        "mean_qty_none": float(none.mean()),
        "mean_qty_discounted": float(some.mean()),
        "qty_lift": float(some.mean() / none.mean() - 1),
        "welch_p": float(welch.pvalue),
        "mannwhitney_p": float(mann.pvalue),
        "kruskal_p_5_to_25": float(kruskal.pvalue),
        "spearman_rho_depth": float(spearman.statistic),
        "spearman_p_depth": float(spearman.pvalue),
        "p_5_vs_25": float(low_vs_high.pvalue),
        "paired_products": int(len(paired)),
        "paired_share_higher": float((paired[True] > paired[False]).mean()),
        "paired_p": float(wilcoxon.pvalue),
        "total_discount_dollars": total_discount,
        "discount_pct_of_gross": float(
            total_discount / used["GrossRevenue"].sum()
        ),
        "excess_over_5pct_dollars": excess,
        "excess_share_of_discount": excess / total_discount,
        "excess_pct_of_net_revenue": float(
            excess / used["NetRevenue"].sum()
        ),
    }


def _customer_interval(groups, statistic):
    """Bootstrap a 95% interval by resampling whole customers.

    Order lines from one customer are not independent, so customers
    (not lines) are the resampling unit.

    Args:
        groups (list[Any]): One item per customer, in the form
            ``statistic`` expects.
        statistic (Callable[[list[Any]], float]): Maps a resampled
            list of customer items to one number.

    Returns:
        tuple[float, float]: The 2.5th and 97.5th percentiles over
        ``BOOTSTRAP_DRAWS`` resamples drawn with the fixed ``SEED``.
    """
    rng = np.random.default_rng(SEED)
    count = len(groups)
    draws = [
        statistic([groups[i] for i in rng.integers(0, count, count)])
        for _ in range(BOOTSTRAP_DRAWS)
    ]
    if np.isnan(draws).all():
        return float("nan"), float("nan")
    low, high = np.nanpercentile(draws, [2.5, 97.5])
    return float(low), float(high)


def robustness(lines):
    """Check the discount findings against buyer and order effects.

    Discounted lines are larger, but larger orders may be the ones
    that get discounts. This compares discounted and full-price lines
    inside the same order, gives intervals that respect clustering by
    customer, and bounds how much extra volume a 25% discount could
    be buying relative to a 5% one.

    Args:
        lines (pandas.DataFrame): Order lines from
            ``data.build_order_lines``.

    Returns:
        dict[str, Any]: A customer-resampled interval for the lift of
        discounted over full-price lines; units on full-price lines in
        orders with and without a discounted line; the within-order
        difference, its interval and a sign test; and the 25%-minus-5%
        difference in units with its interval and the break-even
        increase a 25% discount needs.
    """
    used = tier_lines(lines)
    by_customer = {
        cid: (
            grp.loc[grp["Discount"] == 0, "Quantity"].to_numpy(),
            grp.loc[grp["Discount"] > 0, "Quantity"].to_numpy(),
        )
        for cid, grp in used.groupby("CustomerID")
    }

    def lift(sample):
        """Compute the discounted-over-full-price lift of a sample.

        Args:
            sample (list[tuple[numpy.ndarray, numpy.ndarray]]):
                Resampled customers, each holding full-price and
                discounted line quantities.

        Returns:
            float: Mean discounted units over mean full-price units,
            minus one, or NaN when the sample lacks either kind.
        """
        none = np.concatenate([item[0] for item in sample])
        some = np.concatenate([item[1] for item in sample])
        if len(none) == 0 or len(some) == 0:
            return np.nan
        return some.mean() / none.mean() - 1

    lift_low, lift_high = _customer_interval(
        list(by_customer.values()), lift
    )
    diffs, full_in_mixed, by_owner = [], [], {}
    plain = []
    for _, order in used.groupby("OrderID"):
        full = order.loc[order["Discount"] == 0, "Quantity"]
        some = order.loc[order["Discount"] > 0, "Quantity"]
        if len(full) and len(some):
            diffs.append(some.mean() - full.mean())
            full_in_mixed.extend(full)
            by_owner.setdefault(order["CustomerID"].iloc[0], []).append(
                diffs[-1]
            )
        elif len(full):
            plain.extend(full)
    diffs = np.array(diffs)
    within_low, within_high = _customer_interval(
        [np.array(by_owner[key]) for key in sorted(by_owner)],
        lambda sample: np.concatenate(sample).mean(),
    )
    higher, lower = int((diffs > 0).sum()), int((diffs < 0).sum())
    sign = stats.binomtest(higher, higher + lower, 0.5)
    pairs = {
        cid: (
            grp.loc[grp["Discount"] == BASE_DISCOUNT, "Quantity"],
            grp.loc[grp["Discount"] == TIERS[-1], "Quantity"],
        )
        for cid, grp in used.groupby("CustomerID")
    }
    base_mean = float(
        used.loc[used["Discount"] == BASE_DISCOUNT, "Quantity"].mean()
    )
    top_mean = float(
        used.loc[used["Discount"] == TIERS[-1], "Quantity"].mean()
    )

    def depth(sample):
        """Compute the 25%-minus-5% difference in mean units.

        Args:
            sample (list[tuple[numpy.ndarray, numpy.ndarray]]):
                Resampled customers, each holding 5% and 25% line
                quantities.

        Returns:
            float: Difference in mean units per line, or NaN when
            the sample has no line at one of the two levels.
        """
        five = np.concatenate([item[0] for item in sample])
        top = np.concatenate([item[1] for item in sample])
        if len(five) == 0 or len(top) == 0:
            return np.nan
        return top.mean() - five.mean()

    depth_low, depth_high = _customer_interval(
        [(a.to_numpy(), b.to_numpy()) for a, b in pairs.values()], depth
    )
    full_mean = float(np.mean(full_in_mixed))
    return {
        "lift_ci_low": lift_low,
        "lift_ci_high": lift_high,
        "orders_with_both": int(len(diffs)),
        "full_in_mixed_orders": full_mean,
        "full_in_plain_orders": float(np.mean(plain)),
        "within_order_diff": float(diffs.mean()),
        "within_order_lift": float(diffs.mean() / full_mean),
        "within_order_ci_low": within_low,
        "within_order_ci_high": within_high,
        "within_order_higher": higher,
        "within_order_lower": lower,
        "within_order_sign_p": float(sign.pvalue),
        "depth_diff_units": top_mean - base_mean,
        "depth_diff_pct": (top_mean - base_mean) / base_mean,
        "depth_ci_low": depth_low,
        "depth_ci_high": depth_high,
        "depth_ci_low_pct": depth_low / base_mean,
        "depth_ci_high_pct": depth_high / base_mean,
        "breakeven_lift_25_vs_5": (1 - BASE_DISCOUNT)
        / (1 - TIERS[-1])
        - 1,
    }


def plot_lift_estimates(summary, path):
    """Draw how much extra volume each comparison attributes to discounts.

    Three estimates of the change in units per order line, each with
    its 95% interval, are shown against zero and against the lift a
    25% discount needs to match a 5% discount on revenue.

    Args:
        summary (dict[str, Any]): Combined output of
            ``discount_tests`` and ``robustness``.
        path (str | pathlib.Path): Output PNG path.

    Returns:
        pathlib.Path: The path that was written.
    """
    plotting.apply_style()
    colors = plotting.COLORS
    full = summary["full_in_mixed_orders"]
    rows = [
        (
            "All discounted lines vs full-price lines\n"
            "(mixes buyers and order sizes)",
            summary["qty_lift"],
            summary["lift_ci_low"],
            summary["lift_ci_high"],
            colors["grey"],
        ),
        (
            "Same order: discounted vs full-price line\n"
            f"({summary['orders_with_both']} orders with both)",
            summary["within_order_lift"],
            summary["within_order_ci_low"] / full,
            summary["within_order_ci_high"] / full,
            colors["blue"],
        ),
        (
            "25% discount vs 5% discount\n(does deeper sell more?)",
            summary["depth_diff_pct"],
            summary["depth_ci_low_pct"],
            summary["depth_ci_high_pct"],
            colors["blue"],
        ),
    ]
    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    ypos = np.arange(len(rows))[::-1]
    for y, (label, point, low, high, color) in zip(ypos, rows):
        ax.plot([low, high], [y, y], color=color, linewidth=3,
                solid_capstyle="round")
        ax.scatter([point], [y], color=colors["dark"], zorder=3, s=55)
        ax.text(
            point,
            y + 0.2,
            f"{point:+.0%}  ({low:+.0%} to {high:+.0%})",
            ha="center",
            va="bottom",
            fontsize=10,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.5},
            zorder=4,
        )
    ax.axvline(0, color=colors["dark"], linewidth=1, zorder=1)
    breakeven = summary["breakeven_lift_25_vs_5"]
    last = ypos[-1]
    ax.plot([breakeven, breakeven], [last - 0.3, last + 0.3],
            color=colors["orange"], linestyle="--", linewidth=2)
    ax.text(
        breakeven + 0.012,
        last - 0.12,
        f"Break-even for 25% vs 5%:\n{breakeven:+.0%} more units",
        color=colors["orange"],
        fontsize=10,
        va="center",
    )
    ax.set_yticks(ypos, [row[0] for row in rows])
    ax.set_ylim(-0.6, len(rows) - 0.3)
    ax.set_xlim(
        min(row[2] for row in rows) - 0.05,
        max(max(row[3] for row in rows), breakeven) + 0.22,
    )
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:+.0%}"))
    ax.set_xlabel(
        "Change in units per order line (dot = estimate, bar = 95% "
        "interval)"
    )
    ax.set_title(
        "How much extra volume do discounts buy?", loc="left", pad=12
    )
    return plotting.save_figure(fig, path)


def plot_discounts(table, path):
    """Draw units per line and discount dollars by discount level.

    Args:
        table (pandas.DataFrame): Output of ``tier_table``.
        path (str | pathlib.Path): Output PNG path.

    Returns:
        pathlib.Path: The path that was written.
    """
    plotting.apply_style()
    colors = plotting.COLORS
    fig, (left, right) = plt.subplots(1, 2, figsize=(12, 5))
    x = np.arange(len(table))
    labels = [f"{t * 100:.0f}%" for t in table["Discount"]]
    shades = [colors["grey"]] + [colors["blue"]] * (len(table) - 1)
    err = [
        table["MeanQty"] - table["CILow"],
        table["CIHigh"] - table["MeanQty"],
    ]
    left.bar(x, table["MeanQty"], color=shades, yerr=err, capsize=4)
    for pos, row in zip(x, table.itertuples()):
        left.text(
            pos,
            row.CIHigh + 0.015 * table["CIHigh"].max(),
            f"{row.MeanQty:.1f}",
            ha="center",
            fontsize=10,
        )
    left.set_xticks(x, labels)
    left.set_ylim(0, table["CIHigh"].max() * 1.18)
    left.set_xlabel("Discount on the order line")
    left.set_ylabel("Mean units per order line")
    left.set_title(
        "Discounted lines are larger; deeper is not", loc="left"
    )
    right.bar(
        x[1:], table["DiscountDollars"].iloc[1:], color=colors["orange"]
    )
    for pos, row in zip(x[1:], table.iloc[1:].itertuples()):
        right.text(
            pos,
            row.DiscountDollars + 0.015 * table["DiscountDollars"].max(),
            f"{plotting.money(row.DiscountDollars)}\n"
            f"({row.ShareOfDiscountDollars:.0%})",
            ha="center",
            fontsize=10,
        )
    right.set_xticks(x[1:], labels[1:])
    right.set_ylim(0, table["DiscountDollars"].max() * 1.25)
    right.yaxis.set_major_formatter(FuncFormatter(plotting.money))
    right.set_xlabel("Discount on the order line")
    right.set_ylabel("Revenue given away (USD)")
    right.set_title("Deeper discounts cost far more", loc="left")
    fig.text(
        0.01,
        -0.03,
        "Left: bars show the mean; whiskers are 95% confidence "
        "intervals. Right: share of all discount dollars in brackets.",
        fontsize=9,
        color=colors["grey"],
    )
    fig.tight_layout()
    return plotting.save_figure(fig, path)
