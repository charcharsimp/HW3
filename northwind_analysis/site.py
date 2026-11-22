"""Build the single-file webpage from the analysis results."""

import base64
import html
from pathlib import Path

import pandas as pd

CSS = """
:root {
  --bg: #f4f6f9;
  --surface: #ffffff;
  --fg: #1d2630;
  --muted: #566272;
  --accent: #2563a8;
  --accent-soft: #e3edf8;
  --warn: #a8500f;
  --warn-soft: #fbeee2;
  --line: #d9e0e8;
  --font-display: "Space Grotesk", "Inter", system-ui, sans-serif;
  --font-body: "Inter", system-ui, -apple-system, "Segoe UI", sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #0e141b;
    --surface: #161d26;
    --fg: #e5eaf0;
    --muted: #9ba7b6;
    --accent: #7db1ea;
    --accent-soft: #1b2a3c;
    --warn: #f0a266;
    --warn-soft: #33241a;
    --line: #2a3441;
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --bg: #0e141b;
  --surface: #161d26;
  --fg: #e5eaf0;
  --muted: #9ba7b6;
  --accent: #7db1ea;
  --accent-soft: #1b2a3c;
  --warn: #f0a266;
  --warn-soft: #33241a;
  --line: #2a3441;
  color-scheme: dark;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--fg);
  font-family: var(--font-body);
  font-size: 1rem;
  line-height: 1.6;
  padding-block: 2.5rem 4rem;
  padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px));
}
main { max-width: 56rem; margin: 0 auto; }
h1, h2, h3 {
  font-family: var(--font-display);
  line-height: 1.2;
  text-wrap: balance;
  margin: 0;
}
h1 { font-size: clamp(1.7rem, 4vw, 2.4rem); letter-spacing: -0.01em; }
h2 { font-size: clamp(1.3rem, 3vw, 1.65rem); }
h3 { font-size: 1.05rem; }
p { margin: 0 0 0.8rem; max-width: 68ch; }
a { color: var(--accent); }
a:focus-visible, summary:focus-visible {
  outline: 3px solid var(--accent);
  outline-offset: 2px;
}
.eyebrow {
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
  margin: 0 0 0.4rem;
}
.lede { color: var(--muted); font-size: 1.05rem; margin-top: 0.8rem; }
.facts {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem 1.6rem;
  margin: 1.2rem 0 0;
  padding: 0;
  list-style: none;
  font-size: 0.9rem;
  color: var(--muted);
}
.facts strong { color: var(--fg); font-variant-numeric: tabular-nums; }
.glance {
  margin-top: 2rem;
  padding: 1.2rem 1.4rem;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 10px;
}
.glance ul { margin: 0.6rem 0 0; padding-left: 1.1rem; }
.glance li { margin-bottom: 0.55rem; max-width: 70ch; }
section.q {
  margin-top: 3rem;
  padding-top: 2rem;
  border-top: 2px solid var(--line);
}
.row {
  display: grid;
  grid-template-columns: 8.5rem minmax(0, 1fr);
  gap: 0.4rem 1.5rem;
  margin-top: 1.4rem;
}
.row > h3 {
  font-size: 0.8rem;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--muted);
  padding-top: 0.25rem;
}
.row.finding > h3 { color: var(--accent); }
.row.action > h3 { color: var(--warn); }
.row > div { min-width: 0; }
figure { margin: 1.6rem 0 0; }
.chart {
  background: #ffffff;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 0.6rem;
}
.chart img { display: block; width: 100%; height: auto; }
figcaption { font-size: 0.85rem; color: var(--muted); margin-top: 0.5rem; }
.scroll { overflow-x: auto; margin-top: 1.2rem; }
table {
  border-collapse: collapse;
  width: 100%;
  font-size: 0.88rem;
  font-variant-numeric: tabular-nums;
}
caption {
  text-align: left;
  font-weight: 600;
  padding-bottom: 0.4rem;
  font-size: 0.9rem;
}
th, td {
  padding: 0.45rem 0.7rem;
  border-bottom: 1px solid var(--line);
  text-align: right;
  white-space: nowrap;
}
th:first-child, td:first-child { text-align: left; }
thead th {
  color: var(--muted);
  font-weight: 600;
  font-size: 0.78rem;
  letter-spacing: 0.03em;
}
.limits {
  font-size: 0.88rem;
  color: var(--muted);
  border-left: 3px solid var(--line);
  padding-left: 0.9rem;
}
.limits p { margin-bottom: 0.4rem; }
.note {
  margin-top: 3rem;
  padding: 1.2rem 1.4rem;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 10px;
}
.note ul { padding-left: 1.1rem; margin: 0.6rem 0 0; }
.note li { margin-bottom: 0.45rem; max-width: 72ch; }
code {
  font-family: ui-monospace, "SFMono-Regular", Menlo, monospace;
  font-size: 0.88em;
  background: var(--accent-soft);
  padding: 0.1em 0.35em;
  border-radius: 4px;
}
pre {
  background: var(--accent-soft);
  padding: 0.8rem 1rem;
  border-radius: 8px;
  overflow-x: auto;
  font-size: 0.85rem;
}
pre code { background: none; padding: 0; }
footer { margin-top: 2.5rem; color: var(--muted); font-size: 0.85rem; }
@media (max-width: 40rem) {
  .chart { overflow-x: auto; }
  .chart img { min-width: 620px; }
  .row { grid-template-columns: minmax(0, 1fr); gap: 0.2rem; }
  .row > h3 { padding-top: 0; }
  .glance, .note { padding: 1rem; }
}
"""


def _usd(value):
    """Format dollars with thousands separators.

    Args:
        value (float): Amount in US dollars.

    Returns:
        str: For example ``$1,234``.
    """
    return f"${value:,.0f}"


def _usdk(value):
    """Format dollars in thousands.

    Args:
        value (float): Amount in US dollars.

    Returns:
        str: For example ``$12.3k``.
    """
    return f"${value / 1000:,.1f}k"


def _pct(value, digits=0):
    """Format a fraction as a percentage.

    Args:
        value (float): Fraction, where 0.25 means 25%.
        digits (int): Decimal places to show.

    Returns:
        str: For example ``25%``.
    """
    return f"{value * 100:.{digits}f}%"


def _date(value):
    """Format a date without a leading zero on the day.

    Args:
        value (Any): Anything ``pandas.Timestamp`` can parse.

    Returns:
        str: For example ``4 Jul 1996``.
    """
    stamp = pd.Timestamp(value)
    return f"{stamp.day} {stamp:%b %Y}"


def _listing(items):
    """Join names into a readable list.

    Args:
        items (Iterable[Any]): Names to join; each is HTML-escaped.

    Returns:
        str: ``A``, ``A and B`` or ``A, B and C``.
    """
    names = [_esc(item) for item in items]
    if len(names) <= 1:
        return "".join(names)
    return f"{', '.join(names[:-1])} and {names[-1]}"


def _esc(text):
    """Escape text for safe use inside HTML.

    Args:
        text (Any): Value to convert and escape.

    Returns:
        str: HTML-escaped string.
    """
    return html.escape(str(text))


def _table(caption, headers, rows):
    """Render a table inside a horizontally scrollable box.

    Args:
        caption (str): Table caption.
        headers (list[str]): Column headings.
        rows (list[list[str]]): Cell text for each row; cells are
            escaped here.

    Returns:
        str: HTML for the table.
    """
    head = "".join(f"<th scope='col'>{_esc(h)}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{_esc(c)}</td>" for c in row) + "</tr>"
        for row in rows
    )
    return (
        "<div class='scroll'><table>"
        f"<caption>{_esc(caption)}</caption>"
        f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody>"
        "</table></div>"
    )


def _figure(figures, name, alt, caption):
    """Embed a figure PNG as a base64 image with a caption.

    Args:
        figures (pathlib.Path): Folder containing the PNG files.
        name (str): PNG file name inside ``figures``.
        alt (str): Text alternative describing the chart.
        caption (str): Visible caption under the chart.

    Returns:
        str: HTML for the figure.
    """
    data = base64.b64encode((figures / name).read_bytes()).decode()
    return (
        "<figure><div class='chart'>"
        f"<img alt='{_esc(alt)}' src='data:image/png;base64,{data}'>"
        f"</div><figcaption>{_esc(caption)}</figcaption></figure>"
    )


def _row(label, body, kind=""):
    """Render one labelled block of a question section.

    Args:
        label (str): Short heading, such as ``Why it matters``.
        body (str): HTML content of the block.
        kind (str): Extra CSS class (``finding`` or ``action``).

    Returns:
        str: HTML for the block.
    """
    return (
        f"<div class='row {kind}'><h3>{_esc(label)}</h3>"
        f"<div>{body}</div></div>"
    )


def _question_one(results, tables, figures):
    """Write the section on market growth.

    Args:
        results (dict[str, Any]): All reported numbers.
        tables (dict[str, pandas.DataFrame]): Supporting tables.
        figures (pathlib.Path): Folder containing the figure PNGs.

    Returns:
        str: HTML for question 1.
    """
    q = results["q1"]
    g = tables["q1"]
    win, prev, cur = q["window"], q["prev_year"], q["cur_year"]
    shown = g[g["DriverShareOfChange"].notna()]
    dependent = shown[shown["DriverShareOfChange"] >= 0.7]
    broad = shown[shown["DriverShareOfChange"] < 0.5]
    falling = g[g["Change"] < 0]
    two = g[g["Country"].isin(["USA", "Germany"])]
    rows = [
        [
            r.Country,
            _usd(r.RevenuePrev),
            _usd(r.RevenueCur),
            _usd(r.Change),
            _pct(r.ShareOfGrowth),
            f"{r.DriverAccount} ({_pct(r.DriverShareOfChange)})",
        ]
        for r in g.head(5).itertuples()
    ]
    finding = (
        f"<p>Net revenue in {win} {cur} was "
        f"<strong>{_usdk(q['revenue_cur'])}</strong>, "
        f"<strong>{q['growth_multiple']:.1f}×</strong> the same "
        f"months of {prev} ({_usdk(q['revenue_prev'])}). The increase "
        f"came from <strong>more orders</strong> "
        f"({q['orders_cur']} vs {q['orders_prev']}, "
        f"{q['orders_growth']:+.0%}), not larger ones: the average "
        f"order moved from {_usd(q['aov_prev'])} to "
        f"{_usd(q['aov_cur'])} ({q['aov_growth']:+.0%}). Active "
        f"customers rose from {q['customers_prev']} to "
        f"{q['customers_cur']}.</p>"
        f"<p>{q['markets_up']} of {q['markets_total']} markets grew. "
        f"{_listing(q['top_markets'])} supplied "
        f"{_pct(q['top_markets_share_of_growth'])} of the growth. "
        f"{_listing(broad['Country'])} grew across several "
        f"accounts (the largest account supplied under half of each "
        f"market's gain). In contrast, {len(dependent)} of the "
        f"{len(shown)} markets that grew by "
        f"$5,000 or more got at least 70% of that growth from one "
        f"account: {_listing(dependent['Country'])}. "
        f"{len(falling)} markets shrank "
        f"({_listing(falling['Country'])}), by "
        f"{_usd(-falling['Change'].sum())} in total.</p>"
    )
    action = (
        f"<p>Give sales capacity first to the markets where growth is "
        f"large and spread across customers: "
        f"{_listing(two['Country'])} together delivered "
        f"{_pct(two['ShareOfGrowth'].sum())} of all growth. For the "
        f"single-account markets, the priority is protection: assign "
        f"an owner to each lead account and recruit a second buyer, "
        f"because losing one customer would erase most of that "
        f"market's gain. Review the shrinking markets before they "
        f"turn into lost ones; Denmark's drop is the largest.</p>"
    )
    limits = (
        "<p>Percent changes on small bases (for example Sweden and "
        "Spain) are unreliable, so the chart ranks dollar change. "
        "Four months of overlap cannot show seasonality, and a market "
        "with one or two customers can move on a single order.</p>"
    )
    return (
        "<section class='q' id='q1'><p class='eyebrow'>Question 1</p>"
        "<h2>Which customer markets are growing or declining, and "
        "where should sales attention go?</h2>"
        + _row(
            "Why it matters",
            "<p>Sales time is limited and revenue has more than "
            "doubled. The manager needs to know which markets deserve "
            "more attention, and which gains are fragile.</p>",
        )
        + _row(
            "Approach",
            f"<p>Compare net revenue by customer country for the same "
            f"months ({win}) of {cur} and {prev}. The data end on "
            f"6 May {cur} and start in July 1996, so full-year totals "
            f"would not compare fairly. For each country, split the "
            f"change by account to see whether growth is broad or "
            f"rests on one buyer.</p>",
        )
        + _figure(
            figures,
            "q1_markets.png",
            "Bar chart of revenue change by customer country, January "
            "to April 1998 versus 1997. The USA, Germany and Brazil "
            "grew most; Denmark, Canada, Mexico and Finland declined.",
            f"Revenue change by customer country, {win} {cur} vs "
            f"{prev}. The right-hand column shows how much of a "
            f"growing market's gain came from its largest account.",
        )
        + _table(
            f"Five largest growth markets, {win} {cur} vs {prev}",
            [
                "Market",
                f"{win} {prev}",
                f"{win} {cur}",
                "Change",
                "Share of total growth",
                "Largest account (share of market growth)",
            ],
            rows,
        )
        + _row("Main finding", finding, "finding")
        + _row("Business implication", action, "action")
        + _row("Limits", f"<div class='limits'>{limits}</div>")
        + "</section>"
    )


def _question_two(results, tables, figures):
    """Write the section on customer concentration and lapses.

    Args:
        results (dict[str, Any]): All reported numbers.
        tables (dict[str, pandas.DataFrame]): Supporting tables.
        figures (pathlib.Path): Folder containing the figure PNGs.

    Returns:
        str: HTML for question 2.
    """
    q = results["q2"]
    q1 = results["q1"]
    ranked = tables["q2_ranked"]
    lapsed = tables["q2_lapsed"]
    flagged = lapsed[lapsed["Lapsed"]]
    top = flagged.iloc[0]
    rank = int(
        ranked.loc[ranked["CompanyName"] == top["CompanyName"], "Rank"]
        .iloc[0]
    )
    established = flagged.iloc[1:][
        (flagged.iloc[1:]["Orders"] >= 5)
        & (flagged.iloc[1:]["TrailingYearRevenue"] >= 5000)
    ]
    one_off = flagged[flagged["Orders"] <= 2]
    trailing_total = lapsed["TrailingYearRevenue"].sum()
    rows = [
        [
            r.CompanyName,
            r.Country,
            str(r.Orders),
            _date(r.LastOrder),
            str(r.IdleDays),
            (
                f"{r.TypicalGapDays:.0f}"
                if pd.notna(r.TypicalGapDays)
                else "too few orders"
            ),
            _usd(r.TrailingYearRevenue),
        ]
        for r in flagged.itertuples()
    ]
    names = " and ".join(
        f"{_esc(r.CompanyName)} ({_esc(r.Country)}, {r.IdleDays} days)"
        for r in established.itertuples()
    )
    finding = (
        f"<p>The three largest customers, "
        f"{_listing(q['top3_names'])}, produce "
        f"<strong>{_pct(q['top3_share'])}</strong> of lifetime "
        f"revenue (the largest alone, {_pct(q['top1_share'], 1)}). "
        f"The top 10 produce {_pct(q['top10_share'])}, and "
        f"{q['customers_for_80pct']} of {q['customers']} customers "
        f"produce 80%. Dependence is not rising: in "
        f"{q1['window']}, the top 10 accounted for "
        f"{_pct(q['top10_share_prev'], 1)} of revenue in "
        f"{q1['prev_year']} and {_pct(q['top10_share_cur'], 1)} in "
        f"{q1['cur_year']}, even though active customers grew from "
        f"{q1['customers_prev']} to {q1['customers_cur']}.</p>"
        f"<p>{q['lapsed_accounts']} accounts have been silent far "
        f"longer than their own ordering pattern, but together they "
        f"are only {_pct(q['lapsed_trailing_share'], 1)} of "
        f"last-12-month revenue ({_usd(q['lapsed_trailing_revenue'])})."
        f" The one that matters is "
        f"<strong>{_esc(top['CompanyName'])} ({_esc(top['Country'])})"
        f"</strong>, the number {rank} customer by lifetime revenue "
        f"({_usd(top['LifetimeRevenue'])}). It normally orders about "
        f"every {top['TypicalGapDays']:.0f} days and has been silent "
        f"for {top['IdleDays']} days. "
        + (
            f"{names} are only just past their threshold."
            if len(established)
            else ""
        )
        + f" The {len(one_off)} accounts with one or two orders are "
        f"more likely one-off buyers than lapses.</p>"
    )
    action = (
        f"<p>Concentration is moderate and stable, so it does not "
        f"need an emergency response. Give each of the top three "
        f"accounts a named owner and check their service levels "
        f"regularly. Have someone call {_esc(top['CompanyName'])} "
        f"this week: it represents "
        f"{_pct(top['TrailingYearRevenue'] / trailing_total, 1)} of "
        f"last-12-month revenue ({_usd(top['TrailingYearRevenue'])}), "
        f"and winning back a regular buyer is cheaper than finding a "
        f"new one. Re-run the lapse check monthly; "
        f"<code>customers.lapsed_accounts</code> produces the list.</p>"
    )
    limits = (
        "<p>“Today” is the date of the last order (6 May "
        "1998). The lapse rule (silent longer than the larger of 90 "
        "days and three times the customer's own median gap) is a "
        "judgement call; other thresholds would change the list. "
        "Customers with fewer than three orders have no reliable "
        "usual gap.</p>"
    )
    return (
        "<section class='q' id='q2'><p class='eyebrow'>Question 2</p>"
        "<h2>How dependent is revenue on a few customers, and which "
        "important accounts have gone quiet?</h2>"
        + _row(
            "Why it matters",
            "<p>Losing a top account hits revenue hard, and a regular "
            "buyer who stops ordering is easiest to win back early. "
            "Both are risks the manager can act on.</p>",
        )
        + _row(
            "Approach",
            "<p>Rank customers by lifetime net revenue and plot the "
            "cumulative share. Check whether the top-10 share is "
            "rising by comparing the same months of the two years. "
            "Flag lapsed accounts by comparing days since each "
            "customer's last order with that customer's own usual "
            "gap between orders.</p>",
        )
        + _figure(
            figures,
            "q2_customers.png",
            "Left: curve of cumulative revenue share by customer rank, "
            "reaching 25 percent at the top 3 and 80 percent at the "
            "top 34. Right: bars for the ten largest customers, with "
            "Mere Paillarde highlighted as silent for longer than "
            "usual.",
            "Revenue concentration across 89 customers and the ten "
            "largest accounts. Orange marks an account that has been "
            "silent much longer than its usual pattern.",
        )
        + _table(
            "Accounts silent much longer than usual (as of "
            "6 May 1998)",
            [
                "Account",
                "Country",
                "Orders",
                "Last order",
                "Days silent",
                "Usual gap (days)",
                "Last 12 months revenue",
            ],
            rows,
        )
        + _row("Main finding", finding, "finding")
        + _row("Business implication", action, "action")
        + _row("Limits", f"<div class='limits'>{limits}</div>")
        + "</section>"
    )


def _question_three(results, tables, figures):
    """Write the section on discounting.

    Args:
        results (dict[str, Any]): All reported numbers.
        tables (dict[str, pandas.DataFrame]): Supporting tables.
        figures (pathlib.Path): Folder containing the figure PNGs.

    Returns:
        str: HTML for question 3.
    """
    q = results["q3"]
    t = tables["q3"]
    low = t[t["Discount"] == 0.05].iloc[0]
    high = t[t["Discount"] == 0.25].iloc[0]
    rows = [
        [
            f"{r.Discount * 100:.0f}%",
            f"{r.Lines:,}",
            f"{r.MeanQty:.1f}",
            f"{r.CILow:.1f} to {r.CIHigh:.1f}",
            _usd(r.DiscountDollars),
            _pct(r.ShareOfDiscountDollars),
        ]
        for r in t.itertuples()
    ]
    caps_out = q["depth_ci_high_pct"] < q["breakeven_lift_25_vs_5"]
    finding = (
        f"<p>Order lines with a discount average "
        f"<strong>{q['mean_qty_discounted']:.1f} units</strong> "
        f"against {q['mean_qty_none']:.1f} at full price "
        f"({q['qty_lift']:+.0%}; 95% interval "
        f"{q['lift_ci_low']:+.0%} to {q['lift_ci_high']:+.0%}, "
        f"resampling whole customers). Most of that gap reflects "
        f"<strong>which orders get discounts</strong>, not what the "
        f"discount does. Full-price lines in orders that also contain "
        f"a discounted line already average "
        f"{q['full_in_mixed_orders']:.1f} units, against "
        f"{q['full_in_plain_orders']:.1f} in orders with no discount. "
        f"Inside the same order ({q['orders_with_both']} orders "
        f"contain both kinds of line), discounted lines are larger by "
        f"only {q['within_order_diff']:.1f} units "
        f"({q['within_order_lift']:+.0%}), and the 95% interval, "
        f"{q['within_order_ci_low']:+.1f} to "
        f"{q['within_order_ci_high']:+.1f} units, includes zero. "
        f"Product mix does not explain the gap "
        f"({_pct(q['paired_share_higher'])} of the "
        f"{q['paired_products']} products sell more per line when "
        f"discounted); buyer and order size do.</p>"
        f"<p>Depth made no detectable difference. A 5% discount "
        f"averages {low['MeanQty']:.1f} units and a 25% discount "
        f"{high['MeanQty']:.1f}; the five tiers from 5% to 25% are "
        f"statistically indistinguishable (Kruskal-Wallis "
        f"p = {q['kruskal_p_5_to_25']:.2f}). The 25%-minus-5% "
        f"difference is {q['depth_diff_units']:+.1f} units, with a "
        f"95% interval of {q['depth_ci_low']:+.1f} to "
        f"{q['depth_ci_high']:+.1f} ({q['depth_ci_low_pct']:+.0%} to "
        f"{q['depth_ci_high_pct']:+.0%}). A 25% discount cuts the "
        f"price by about a fifth compared with a 5% one, so it needs "
        f"roughly {q['breakeven_lift_25_vs_5']:.0%} more units per "
        f"line to bring in the same revenue. "
        + (
            "Even the top of that interval falls short of this. "
            if caps_out
            else "The top of that interval reaches it, so a payoff "
            "cannot be ruled out. "
        )
        + f"Cost climbs with depth: the 25% tier gave away "
        f"{_usd(high['DiscountDollars'])} "
        f"({_pct(high['ShareOfDiscountDollars'])} of all discount "
        f"dollars) against {_usd(low['DiscountDollars'])} "
        f"({_pct(low['ShareOfDiscountDollars'])}) at 5%. About "
        f"<strong>{_usd(q['excess_over_5pct_dollars'])}</strong> "
        f"({_pct(q['excess_share_of_discount'])} of discount "
        f"dollars, {_pct(q['excess_pct_of_net_revenue'], 1)} of net "
        f"revenue) went to discounts above the 5% level.</p>"
    )
    action = (
        f"<p>Set 5% as the standard discount and require approval "
        f"above it: the extra depth shows no volume return, so most "
        f"of the {_usd(q['excess_over_5pct_dollars'])} should stay in "
        f"revenue. Treat that figure as an upper bound. The data also "
        f"do not show that a 5% discount itself raises order size "
        f"once the same order is compared. Run a one-quarter test: "
        f"randomly hold a share of discounted customers or reps at "
        f"5%, and another share at no discount, then compare order "
        f"sizes before making any policy permanent.</p>"
    )
    limits = (
        "<p>This is observational. Discounts are not assigned at "
        "random, and larger orders are the ones that get them, which "
        "is why the same-order comparison matters. That comparison "
        f"uses only the {q['orders_with_both']} orders that mix both "
        "kinds of line, so its interval is wide and cannot rule out "
        "an effect of a few units. Intervals come from resampling "
        "customers with a fixed seed. There are no cost figures, so "
        "the savings are revenue, not profit. "
        f"{q['lines_excluded']} lines with other discounts (1-4% and "
        "6%) on one to three units are left out of the tier "
        "analysis.</p>"
    )
    return (
        "<section class='q' id='q3'><p class='eyebrow'>Question 3</p>"
        "<h2>Do bigger discounts sell more, or do they just give "
        "revenue away?</h2>"
        + _row(
            "Why it matters",
            f"<p>Discounts are the lever sales staff control most "
            f"directly. They cost {_usd(q['total_discount_dollars'])} "
            f"over the period, {_pct(q['discount_pct_of_gross'], 1)} "
            f"of gross sales, and "
            f"{_pct(q['share_lines_discounted'])} of order lines "
            f"carry one.</p>",
        )
        + _row(
            "Approach",
            "<p>At order-line level, compare units per line at each "
            "discount level (0, 5, 10, 15, 20, 25%) with 95% "
            "confidence intervals, and test whether depth matters "
            "among discounted lines (Kruskal-Wallis). Because buyers "
            "who order more may also get more discounts, separate the "
            "discount from the buyer: compare discounted and "
            "full-price lines inside the same order, compare within "
            "each product, and resample whole customers to get "
            "intervals. Add up the discount dollars given at each "
            "level.</p>",
        )
        + _figure(
            figures,
            "q3_discounts.png",
            "Left: bars of mean units per order line at each discount "
            "level, about 22 at no discount and 25 to 28 at every "
            "discount level, with overlapping intervals. Right: bars "
            "of discount dollars given, "
            "rising from 7.8 thousand at 5 percent to 33 thousand at "
            "25 percent.",
            "Units per order line and revenue given away, by discount "
            "level.",
        )
        + _table(
            "Discount levels compared",
            [
                "Discount",
                "Order lines",
                "Mean units per line",
                "95% interval",
                "Discount dollars",
                "Share of discount dollars",
            ],
            rows,
        )
        + _row("Main finding", finding, "finding")
        + _row("Business implication", action, "action")
        + _row("Limits", f"<div class='limits'>{limits}</div>")
        + "</section>"
    )


def _question_four(results, tables, figures):
    """Write the section on stock-out risk.

    Args:
        results (dict[str, Any]): All reported numbers.
        tables (dict[str, pandas.DataFrame]): Supporting tables.
        figures (pathlib.Path): Folder containing the figure PNGs.

    Returns:
        str: HTML for question 4.
    """
    q = results["q4"]
    cover = tables["q4"]
    gone = cover[cover["Status"] == "Discontinued, still selling"]
    gone = gone.sort_values("WeeklyRevenue", ascending=False)
    none_ordered = cover[
        cover["Status"] == "Low stock, nothing on order"
    ].nlargest(5, "WeeklyRevenue")
    empty = gone[gone["UnitsInStock"] == 0]
    biggest = none_ordered.iloc[0]
    rows = [
        [
            r.ProductName,
            f"{r.UnitsInStock:,}",
            f"{r.WeeklyUnits:.1f}",
            _usd(r.WeeklyRevenue),
            f"{r.WeeksCover:.1f}",
        ]
        for r in gone.itertuples()
    ]
    finding = (
        f"<p><strong>{q['low_cover']} of {q['active_selling']}</strong>"
        f" active products with recent sales "
        f"({_pct(q['low_cover_share'])}) have under "
        f"{q['alert_weeks']:.0f} weeks of stock. They account for "
        f"{_pct(q['low_cover_revenue_share'])} of the weekly revenue "
        f"of active products ({_usd(q['low_cover_weekly_revenue'])} "
        f"a week). For {q['nothing_on_order']} of them, worth "
        f"{_usd(q['nothing_on_order_weekly_revenue'])} a week, "
        f"nothing is on order. {_esc(biggest['ProductName'])} is the "
        f"largest: {_usd(biggest['WeeklyRevenue'])} a week with "
        f"{biggest['WeeksCover']:.1f} weeks of stock and no order "
        f"placed.</p>"
        f"<p>Separately, {q['discontinued_selling']} discontinued "
        f"products still sell, {_pct(q['discontinued_revenue_share'])}"
        f" of weekly revenue ({_usd(q['discontinued_weekly_revenue'])}"
        f"). {q['discontinued_out_of_stock']} of them have no stock "
        f"left ({_listing(empty['ProductName'])}), which is "
        f"{_usd(q['discontinued_out_of_stock_weekly_revenue'])} a "
        f"week of demand with nothing to sell.</p>"
    )
    action = (
        f"<p>Place orders first for the best-selling products with "
        f"nothing on order: "
        f"{_listing(none_ordered['ProductName'])}. Then "
        f"compare reorder levels with current sales rates, since "
        f"order volume has roughly doubled year over year. Decide "
        f"deliberately about the discontinued products customers "
        f"still buy: either reinstate the ones with steady sales "
        f"(for example "
        f"{_esc(gone.iloc[0]['ProductName'])}, "
        f"{_usd(gone.iloc[0]['WeeklyRevenue'])} a week) or tell "
        f"customers what replaces them.</p>"
    )
    limits = (
        "<p>The Product sheet has no date, so stock levels are "
        "assumed current as of the last order. If stock has been "
        "replenished since, the risk is overstated. Weeks of cover "
        f"use the last {q['window_days']} days of sales, a period of "
        "fast growth; cover based on the full history would look "
        "healthier. Units on order have no arrival dates, so the "
        "light bars show the best case.</p>"
    )
    return (
        "<section class='q' id='q4'><p class='eyebrow'>Question 4</p>"
        "<h2>Which fast-selling products are about to run out, and "
        "are we discontinuing products customers still buy?</h2>"
        + _row(
            "Why it matters",
            "<p>A stock-out loses the sale and can lose the customer. "
            "With orders doubling, stock levels set for slower months "
            "may no longer fit.</p>",
        )
        + _row(
            "Approach",
            f"<p>Estimate each product's weekly demand from the last "
            f"{q['window_days']} days of orders. Divide units in "
            f"stock by weekly demand to get weeks of cover, with and "
            f"without units already on order. Flag active products "
            f"under {q['alert_weeks']:.0f} weeks, and list "
            f"discontinued products that still have recent "
            f"sales.</p>",
        )
        + _figure(
            figures,
            "q4_inventory.png",
            "Horizontal bars of weeks of stock cover for the twelve "
            "best-selling products with under two weeks of stock. "
            "Most have no units on order; three have an inbound order "
            "shown as a lighter bar.",
            "Weeks of cover for the best-selling low-stock products. "
            "Light hatched bars show cover if the units already on "
            "order arrive.",
        )
        + _table(
            "Discontinued products that still sell",
            [
                "Product",
                "Units in stock",
                "Units sold per week",
                "Weekly sales",
                "Weeks of cover",
            ],
            rows,
        )
        + _row("Main finding", finding, "finding")
        + _row("Business implication", action, "action")
        + _row("Limits", f"<div class='limits'>{limits}</div>")
        + "</section>"
    )


def build_site(results, tables, figures, path, repo_url=""):
    """Write the complete webpage as one self-contained HTML file.

    Args:
        results (dict[str, Any]): All reported numbers.
        tables (dict[str, pandas.DataFrame]): Supporting tables with
            keys ``q1``, ``q2_ranked``, ``q2_lapsed``, ``q3``,
            ``q4`` and ``shippers``.
        figures (pathlib.Path): Folder containing the figure PNGs.
        path (pathlib.Path): Output HTML path; parent folders are
            created.
        repo_url (str): Public GitHub URL for the footer; leave
            empty to omit the link.

    Returns:
        None. Writes the HTML file to ``path``.
    """
    meta = results["meta"]
    q1, q2, q3, q4 = (results[k] for k in ("q1", "q2", "q3", "q4"))
    side = results["side_check"]
    start = _date(meta["first_order"])
    end = _date(meta["last_order"])
    shippers = tables["shippers"]
    top = tables["q2_lapsed"].query("Lapsed").iloc[0]
    glance = [
        f"<strong>Growth.</strong> {q1['window']} {q1['cur_year']} "
        f"revenue was {q1['growth_multiple']:.1f}× the same "
        f"months of {q1['prev_year']}, driven by order count. The USA "
        f"and Germany grew across many accounts; several other "
        f"markets depend on one account each.",
        f"<strong>Customers.</strong> The top 3 customers are "
        f"{_pct(q2['top3_share'])} of revenue and that share is "
        f"stable. {_esc(top['CompanyName'])} ({_esc(top['Country'])}), "
        f"a top-10 account, has been silent {top['IdleDays']} days "
        f"against a usual {top['TypicalGapDays']:.0f}.",
        f"<strong>Discounts.</strong> Discounted lines are "
        f"{q3['qty_lift']:.0%} larger, but mostly because larger "
        f"orders get the discounts: inside one order the gap is "
        f"{q3['within_order_lift']:+.0%} and not distinguishable from "
        f"zero. Deeper discounts bring no detectable extra volume. "
        f"About {_usd(q3['excess_over_5pct_dollars'])} was given "
        f"beyond a 5% level.",
        f"<strong>Stock.</strong> {q4['low_cover']} of "
        f"{q4['active_selling']} active products have under "
        f"{q4['alert_weeks']:.0f} weeks of stock, and "
        f"{q4['nothing_on_order']} have nothing on order. "
        f"{q4['discontinued_selling']} discontinued products still "
        f"make {_pct(q4['discontinued_revenue_share'])} of weekly "
        f"revenue.",
    ]
    repo = (
        f"<p>Code and README: <a href='{_esc(repo_url)}'>"
        f"{_esc(repo_url)}</a></p>"
        if repo_url
        else ""
    )
    late = shippers.sort_values("LateRate", ascending=False)
    notes = [
        "<strong>Revenue</strong> is unit price × quantity "
        "× (1 − discount) from the order lines. Freight is "
        "excluded. The price charged on the order line is used "
        f"because <code>Product.Price</code> differs on "
        f"{_pct(meta['price_mismatch_share'])} of lines.",
        f"<strong>Coverage.</strong> {meta['orders']} orders and "
        f"{meta['order_lines']:,} order lines from {start} to {end}; "
        f"{meta['customers_with_orders']} of "
        f"{meta['customers_total']} customers have ordered. 1996 "
        f"starts in July and 1998 ends in early May, so growth uses "
        f"matching months.",
        f"<strong>Country</strong> is the customer's country. "
        f"{_pct(meta['ship_country_match_share'], 1)} of orders ship "
        f"to the same country.",
        "<strong>No cost data.</strong> Every figure is revenue, not "
        "profit.",
        f"<strong>Also checked: delivery.</strong> "
        f"{_pct(side['on_time_rate'], 1)} of "
        f"{side['orders_shipped']} shipped orders met their required "
        f"date ({side['late_orders']} late). Late rates run from "
        f"{_pct(late['LateRate'].min(), 1)} to "
        f"{_pct(late['LateRate'].max(), 1)} across the three "
        f"shippers, a difference that could easily be chance "
        f"(chi-square p = {side['shipper_chi2_p']:.2f}). Freight is "
        f"{_pct(side['freight_share_of_revenue'], 1)} of net "
        f"revenue, and {side['open_orders']} orders were still open. "
        f"Fulfillment is not where to spend attention.",
        "<strong>Verification.</strong> "
        "<code>verify_with_sql.py</code> recomputes the headline "
        "numbers with SQL in a separate in-memory database and "
        "compares them with the pandas results.",
    ]
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Northwind Business Review</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Space+Grotesk:wght@500;700&display=swap">
<style>{CSS}</style>
</head>
<body>
<main>
<header>
<p class="eyebrow">Northwind Traders, order history analysis</p>
<h1>Where Northwind is growing, who it depends on, what discounts
cost, and what may run out</h1>
<p class="lede">Four questions for a manager who wants to understand
the business, answered from the Northwind order data.</p>
<ul class="facts">
<li><strong>{meta['orders']}</strong> orders</li>
<li><strong>{meta['customers_with_orders']}</strong> customers</li>
<li><strong>{_usd(meta['net_revenue'])}</strong> net revenue</li>
<li>{start} to {end}</li>
</ul>
</header>
<div class="glance">
<h2>At a glance</h2>
<ul>
{''.join(f'<li>{item}</li>' for item in glance)}
</ul>
</div>
{_question_one(results, tables, figures)}
{_question_two(results, tables, figures)}
{_question_three(results, tables, figures)}
{_question_four(results, tables, figures)}
<div class="note" id="notes">
<h2>Data and method notes</h2>
<ul>
{''.join(f'<li>{item}</li>' for item in notes)}
</ul>
</div>
<footer>
{repo}
<p>To rebuild every number, figure and table, run
<code>python run_all.py</code> from the repository root.</p>
</footer>
</main>
</body>
</html>
"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page, encoding="utf-8")
