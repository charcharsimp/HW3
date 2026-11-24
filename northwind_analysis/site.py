"""Build the single-file webpage from the analysis results."""

import base64
import html
import shutil
from pathlib import Path

import pandas as pd

from northwind_analysis import customers, discounts, markets

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
.plain {
  background: var(--accent-soft);
  border-left: 4px solid var(--accent);
  border-radius: 6px;
  padding: 0.7rem 1rem;
  margin: 1.1rem 0 0;
  max-width: 70ch;
}
.tight { margin: 0; padding-left: 1.1rem; }
.tight li { margin-bottom: 0.55rem; max-width: 68ch; }
details.work {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 0.1rem 1rem;
}
details.work summary {
  cursor: pointer;
  font-weight: 600;
  color: var(--accent);
  padding: 0.6rem 0;
}
details.work ol { padding-left: 1.2rem; margin: 0.3rem 0 0.6rem; }
details.work li { margin-bottom: 0.55rem; max-width: 68ch; }
.files { font-size: 0.88rem; color: var(--muted); }
nav.jump {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem 1.2rem;
  margin: 1.2rem 0 0;
  font-size: 0.92rem;
}
dl.terms { margin: 0.6rem 0 0; }
dl.terms dt { font-weight: 600; margin-top: 0.8rem; }
dl.terms dd { margin: 0.1rem 0 0; max-width: 68ch; color: var(--muted); }
@media (max-width: 40rem) {
  .chart { overflow-x: auto; }
  .chart img { min-width: 620px; }
  .row { grid-template-columns: minmax(0, 1fr); gap: 0.2rem; }
  .row > h3 { padding-top: 0; }
  .glance, .note { padding: 1rem; }
}
"""


DATA_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1mD4Hn4NZdJlXMC4EJcSp27vg-_jbxUYJ95vQvMbSpVM/edit?usp=sharing"
)
DOWNLOAD_TABLES = (
    "q1_market_growth.csv",
    "q2_revenue_by_customer.csv",
    "q2_lapsed_accounts.csv",
    "q3_discount_tiers.csv",
    "q4_product_cover.csv",
    "side_check_shippers.csv",
)


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


def _code_link(path, repo_url, label=None):
    """Link to a file in the GitHub repository.

    Args:
        path (str): File path inside the repository.
        repo_url (str): Public repository URL; when empty the link is
            filled in by the page script from the page address.
        label (str | None): Link text; defaults to ``path``.

    Returns:
        str: HTML anchor carrying a ``data-repo-path`` attribute.
    """
    href = (
        f"{repo_url.rstrip('/')}/blob/main/{path}"
        if repo_url
        else "#how-to-check"
    )
    return (
        f"<a href='{_esc(href)}' data-repo-path='{_esc(path)}'>"
        f"{_esc(label or path)}</a>"
    )


def _data_link(name):
    """Link to a downloadable results file next to the page.

    Args:
        name (str): File name inside the ``downloads`` folder.

    Returns:
        str: HTML anchor to ``downloads/<name>``.
    """
    return f"<a href='downloads/{_esc(name)}'>{_esc(name)}</a>"


def _work(steps, data_files, code_files, repo_url):
    """Render a collapsible step-by-step calculation.

    Args:
        steps (list[str]): HTML for each numbered step.
        data_files (list[str]): Names in the ``downloads`` folder.
        code_files (list[str]): Repository paths of the code used.
        repo_url (str): Public repository URL for the code links.

    Returns:
        str: HTML for the collapsible block.
    """
    items = "".join(f"<li>{step}</li>" for step in steps)
    data = ", ".join(_data_link(name) for name in data_files)
    code = ", ".join(_code_link(p, repo_url) for p in code_files)
    return (
        "<details class='work'><summary>Show the calculation, step by "
        f"step</summary><ol>{items}</ol><p class='files'>"
        f"<strong>Numbers and tables:</strong> {data}.<br>"
        f"<strong>Code:</strong> {code}.</p></details>"
    )


def _plain(text):
    """Render the one-sentence answer shown under a question.

    Args:
        text (str): HTML of the short answer.

    Returns:
        str: HTML callout.
    """
    return f"<p class='plain'><strong>Short answer.</strong> {text}</p>"


def _bullets(items):
    """Render a compact bulleted list.

    Args:
        items (list[str]): HTML for each bullet.

    Returns:
        str: HTML unordered list.
    """
    body = "".join(f"<li>{item}</li>" for item in items)
    return f"<ul class='tight'>{body}</ul>"


def copy_downloads(out_dir, site_path):
    """Copy the results files next to the page so it can link to them.

    Args:
        out_dir (pathlib.Path): Folder holding ``results.json`` and the
            ``tables`` folder written by the analysis.
        site_path (pathlib.Path): Path of the HTML page; files go in a
            ``downloads`` folder beside it.

    Returns:
        None. Creates ``downloads/`` with the CSV tables and
        ``results.json``.
    """
    target = Path(site_path).parent / "downloads"
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out_dir / "results.json", target / "results.json")
    for name in DOWNLOAD_TABLES:
        shutil.copy2(out_dir / "tables" / name, target / name)


def _question_one(results, tables, figures, repo_url=""):
    """Write the section on market growth.

    Args:
        results (dict[str, Any]): All reported numbers.
        tables (dict[str, pandas.DataFrame]): Supporting tables.
        figures (pathlib.Path): Folder containing the figure PNGs.
        repo_url (str): Public repository URL for code links.

    Returns:
        str: HTML for question 1.
    """
    q = results["q1"]
    meta = results["meta"]
    g = tables["q1"]
    win, prev, cur = q["window"], q["prev_year"], q["cur_year"]
    floor = _usd(markets.DRIVER_MIN_GROWTH)
    shown = g[g["DriverShareOfChange"].notna()]
    dependent = shown[shown["DriverShareOfChange"] >= 0.7]
    broad = shown[shown["DriverShareOfChange"] < 0.5]
    falling = g[g["Change"] < 0]
    two = g[g["Country"].isin(["USA", "Germany"])]
    biggest_drop = falling.nsmallest(1, "Change").iloc[0]["Country"]
    usa = g[g["Country"] == "USA"].iloc[0]
    growth = q["revenue_cur"] - q["revenue_prev"]
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
    short = (
        f"Yes, in most places. Revenue in {win} {cur} was "
        f"{q['growth_multiple']:.1f}× the same months of {prev}, and "
        f"{q['markets_up']} of {q['markets_total']} markets grew. The "
        f"USA and Germany grew across many customers; several other "
        f"markets rest on a single customer."
    )
    finding = _bullets(
        [
            f"<strong>Revenue more than doubled, because of more "
            f"orders.</strong> Net revenue was "
            f"{_usdk(q['revenue_cur'])} against "
            f"{_usdk(q['revenue_prev'])} ({q['growth_multiple']:.1f}×). "
            f"Orders rose from {q['orders_prev']} to {q['orders_cur']} "
            f"({q['orders_growth']:+.0%}); the average order only moved "
            f"from {_usd(q['aov_prev'])} to {_usd(q['aov_cur'])} "
            f"({q['aov_growth']:+.0%}). Active customers rose from "
            f"{q['customers_prev']} to {q['customers_cur']}.",
            f"<strong>Growth is widespread.</strong> "
            f"{q['markets_up']} of {q['markets_total']} markets grew. "
            f"{_listing(q['top_markets'])} supplied "
            f"{_pct(q['top_markets_share_of_growth'])} of the growth.",
            f"<strong>Some growth is solid.</strong> "
            f"{_listing(broad['Country'])} grew across several "
            f"accounts; in each, the largest account supplied under "
            f"half of the gain.",
            f"<strong>Some growth is fragile.</strong> "
            f"{len(dependent)} of the {len(shown)} markets that grew by "
            f"{floor} or more got at least 70% of that growth from one "
            f"account: {_listing(dependent['Country'])}.",
            f"<strong>{len(falling)} markets shrank</strong> "
            f"({_listing(falling['Country'])}), by "
            f"{_usd(-falling['Change'].sum())} in total.",
        ]
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
        f"turn into lost ones; {_esc(biggest_drop)}'s drop is the "
        f"largest.</p>"
    )
    limits = (
        f"<p>Percent changes on small bases (for example Sweden and "
        f"Spain) are unreliable, so the chart ranks dollar change. "
        f"Four months of overlap cannot show seasonality, and a market "
        f"with one or two customers can move on a single order.</p>"
    )
    steps = [
        f"Revenue of one order line = unit price × quantity × "
        f"(1 − discount). All {meta['order_lines']:,} lines add up to "
        f"{_usd(meta['net_revenue'])}.",
        f"Keep only orders dated {win} of each year and group them by "
        f"the customer's country. {win} {prev} adds up to "
        f"{_usd(q['revenue_prev'])} and {win} {cur} to "
        f"{_usd(q['revenue_cur'])}. {_usd(q['revenue_cur'])} ÷ "
        f"{_usd(q['revenue_prev'])} = {q['growth_multiple']:.2f}×, a "
        f"gain of {_usd(growth)}.",
        f"Example, USA: {_usd(usa.RevenueCur)} − "
        f"{_usd(usa.RevenuePrev)} = {_usd(usa.Change)}. That is "
        f"{_usd(usa.Change)} ÷ {_usd(growth)} = "
        f"{_pct(usa.ShareOfGrowth)} of all growth.",
        f"Largest account in the USA: {_esc(usa.DriverAccount)} "
        f"supplied {_pct(usa.DriverShareOfChange)} of the USA's gain, "
        f"about {_usd(usa.DriverShareOfChange * usa.Change)}. The share "
        f"is only shown for markets that grew by at least {floor}, "
        f"because a share of a tiny change means little.",
        f"A market counts as resting on one account when it grew by "
        f"{floor} or more and its largest account supplied at least "
        f"70% of that gain.",
        f"Percent change is left blank when the {prev} revenue was "
        f"under {_usd(markets.MIN_BASE)}, because a tiny starting "
        f"point makes the percentage swing wildly. The chart ranks "
        f"dollar change instead.",
    ]
    return (
        "<section class='q' id='q1'><p class='eyebrow'>Question 1</p>"
        "<h2>Which customer markets are growing or declining, and "
        "where should sales attention go?</h2>"
        + _plain(short)
        + _row(
            "Why it matters",
            "<p>Sales time is limited and revenue has more than "
            "doubled. The manager needs to know which markets deserve "
            "more attention, and which gains are fragile.</p>",
        )
        + _row(
            "Approach",
            f"<p>Add up net revenue by the customer's country for "
            f"{win} {cur} and for {win} {prev}. Only these months can "
            f"be compared fairly: the data start in July 1996 and end "
            f"on 6 May {cur}. Then, for each country, check how much "
            f"of the gain came from its single largest customer.</p>",
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
        + _row(
            "How we got this",
            _work(
                steps,
                ["q1_market_growth.csv", "results.json"],
                [
                    "northwind_analysis/markets.py",
                    "northwind_analysis/data.py",
                ],
                repo_url,
            ),
        )
        + "</section>"
    )


def _question_two(results, tables, figures, repo_url=""):
    """Write the section on customer concentration and lapses.

    Args:
        results (dict[str, Any]): All reported numbers.
        tables (dict[str, pandas.DataFrame]): Supporting tables.
        figures (pathlib.Path): Folder containing the figure PNGs.
        repo_url (str): Public repository URL for code links.

    Returns:
        str: HTML for question 2.
    """
    q = results["q2"]
    q1 = results["q1"]
    meta = results["meta"]
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
    end = _date(meta["last_order"])
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
    short = (
        f"Moderately, and not getting worse. The top 3 customers are "
        f"{_pct(q['top3_share'])} of revenue and that share is not "
        f"rising. One top-10 customer, {_esc(top['CompanyName'])}, "
        f"has gone quiet and is worth a call."
    )
    finding = _bullets(
        [
            f"<strong>Concentration is moderate.</strong> The three "
            f"largest customers, {_listing(q['top3_names'])}, produce "
            f"{_pct(q['top3_share'])} of lifetime revenue (the largest "
            f"alone, {_pct(q['top1_share'], 1)}). The top 10 produce "
            f"{_pct(q['top10_share'])}, and {q['customers_for_80pct']} "
            f"of {q['customers']} customers produce 80%.",
            f"<strong>Dependence is not rising.</strong> In "
            f"{q1['window']}, the top 10 accounted for "
            f"{_pct(q['top10_share_prev'], 1)} of revenue in "
            f"{q1['prev_year']} and {_pct(q['top10_share_cur'], 1)} in "
            f"{q1['cur_year']}, even though active customers grew from "
            f"{q1['customers_prev']} to {q1['customers_cur']}.",
            f"<strong>One quiet account matters.</strong> "
            f"{_esc(top['CompanyName'])} ({_esc(top['Country'])}) is "
            f"the number {rank} customer by lifetime revenue "
            f"({_usd(top['LifetimeRevenue'])}). It normally orders "
            f"about every {top['TypicalGapDays']:.0f} days and has been "
            f"silent for {top['IdleDays']} days.",
            f"<strong>The other flagged accounts are small.</strong> "
            f"All {q['lapsed_accounts']} flagged accounts together are "
            f"{_pct(q['lapsed_trailing_share'], 1)} of last-12-month "
            f"revenue ({_usd(q['lapsed_trailing_revenue'])}). "
            + (
                f"{names} are only just past their threshold. "
                if len(established)
                else ""
            )
            + f"The {len(one_off)} accounts with one or two orders are "
            f"more likely one-off buyers than lapses.",
        ]
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
        f"<p>“Today” is the date of the last order ({end}). The lapse "
        f"rule is a judgement call; other thresholds would change the "
        f"list. Customers with fewer than three orders have no "
        f"reliable usual gap.</p>"
    )
    floor = customers.IDLE_FLOOR_DAYS
    mult = customers.IDLE_GAP_MULTIPLE
    gap = top["TypicalGapDays"]
    est = flagged[flagged["TypicalGapDays"].notna()]
    close = est.loc[(est["IdleDays"] - est["ThresholdDays"]).idxmin()]
    first = ranked.iloc[0]
    third = ranked.iloc[2]
    steps = [
        f"Add each customer's net revenue over the whole period and "
        f"rank them. Number 1 is {_esc(first['CompanyName'])} with "
        f"{_usd(first['Revenue'])}: {_usd(first['Revenue'])} ÷ "
        f"{_usd(meta['net_revenue'])} = {_pct(first['Share'], 1)} of "
        f"all revenue.",
        f"Keep a running total down the ranking. The top 3 reach "
        f"{_pct(third['CumShare'], 1)}, the top 10 reach "
        f"{_pct(q['top10_share'], 1)}, and it takes "
        f"{q['customers_for_80pct']} customers to reach 80%.",
        f"Trend check: repeat the top-10 share using only "
        f"{q1['window']} orders of each year: "
        f"{_pct(q['top10_share_prev'], 1)} in {q1['prev_year']} and "
        f"{_pct(q['top10_share_cur'], 1)} in {q1['cur_year']}.",
        f"Lapse rule: list each customer's order dates and take the "
        f"gaps between them. The usual gap is the median gap, used "
        f"only for customers with 3 or more orders. The threshold is "
        f"the larger of {floor} days and {mult} × the usual gap. A "
        f"customer is flagged when the days since their last order, "
        f"counted up to {end}, exceed the threshold. With fewer than "
        f"3 orders there is no usual gap, so only the {floor}-day "
        f"floor applies.",
        f"Example, {_esc(top['CompanyName'])}: usual gap {gap:.1f} "
        f"days, so {mult} × {gap:.1f} = {mult * gap:.1f}. The "
        f"threshold is the larger of {floor} and {mult * gap:.1f}, "
        f"which is {top['ThresholdDays']:.0f}. It has been silent "
        f"{top['IdleDays']} days, more than {top['ThresholdDays']:.0f}"
        f", so it is flagged.",
        f"Closest call, {_esc(close['CompanyName'])}: usual gap "
        f"{close['TypicalGapDays']:.1f} days, threshold "
        f"{close['ThresholdDays']:.0f}, silent {close['IdleDays']} "
        f"days. It is over the line by "
        f"{close['IdleDays'] - close['ThresholdDays']:.0f} "
        f"day(s), so it is a weak flag.",
        f"Last-12-month revenue is net revenue from orders in the "
        f"{customers.TRAILING_DAYS} days up to the last order date.",
    ]
    return (
        "<section class='q' id='q2'><p class='eyebrow'>Question 2</p>"
        "<h2>How dependent is revenue on a few customers, and which "
        "important accounts have gone quiet?</h2>"
        + _plain(short)
        + _row(
            "Why it matters",
            "<p>Losing a top account hits revenue hard, and a regular "
            "buyer who stops ordering is easiest to win back early. "
            "Both are risks the manager can act on.</p>",
        )
        + _row(
            "Approach",
            "<p>Rank customers by their total net revenue and see how "
            "much the top few contribute. Check whether that share is "
            "rising by comparing the same months of the two years. "
            "Then flag customers whose time since their last order is "
            "much longer than their own usual time between orders.</p>",
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
            f"Accounts silent much longer than usual (as of {end})",
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
        + _row(
            "How we got this",
            _work(
                steps,
                [
                    "q2_revenue_by_customer.csv",
                    "q2_lapsed_accounts.csv",
                    "results.json",
                ],
                ["northwind_analysis/customers.py"],
                repo_url,
            ),
        )
        + "</section>"
    )


def _question_three(results, tables, figures, repo_url=""):
    """Write the section on discounting.

    Args:
        results (dict[str, Any]): All reported numbers.
        tables (dict[str, pandas.DataFrame]): Supporting tables.
        figures (pathlib.Path): Folder containing the figure PNGs.
        repo_url (str): Public repository URL for code links.

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
    short = (
        f"Discounted lines are bigger, but that is mostly because "
        f"bigger orders get the discounts, and deeper discounts do "
        f"not sell more. About {_usd(q['excess_over_5pct_dollars'])} "
        f"was given away beyond a 5% discount."
    )
    finding = _bullets(
        [
            f"<strong>Discounted lines are bigger.</strong> They "
            f"average {q['mean_qty_discounted']:.1f} units against "
            f"{q['mean_qty_none']:.1f} at full price "
            f"({q['qty_lift']:+.0%}; likely range "
            f"{q['lift_ci_low']:+.0%} to {q['lift_ci_high']:+.0%}).",
            f"<strong>But the discount may not be the reason.</strong> "
            f"Full-price lines in orders that also contain a "
            f"discounted line already average "
            f"{q['full_in_mixed_orders']:.1f} units, against "
            f"{q['full_in_plain_orders']:.1f} in orders with no "
            f"discount. Bigger orders are the ones that get discounts.",
            f"<strong>Inside the same order the gap is small.</strong> "
            f"In the {q['orders_with_both']} orders with both kinds of "
            f"line, the discounted line is larger by "
            f"{q['within_order_diff']:.1f} units "
            f"({q['within_order_lift']:+.0%}). The likely range, "
            f"{q['within_order_ci_low']:+.1f} to "
            f"{q['within_order_ci_high']:+.1f} units, includes zero, "
            f"so “no effect” cannot be ruled out. Product mix does "
            f"not explain the gap either: "
            f"{_pct(q['paired_share_higher'])} of the "
            f"{q['paired_products']} products sell more per line when "
            f"discounted, so buyer and order size matter more.",
            f"<strong>Deeper discounts do not sell more.</strong> A 5% "
            f"discount averages {low['MeanQty']:.1f} units and a 25% "
            f"discount {high['MeanQty']:.1f}. The difference, "
            f"{q['depth_diff_units']:+.1f} units, has a likely range "
            f"of {q['depth_ci_low']:+.1f} to {q['depth_ci_high']:+.1f} "
            f"({q['depth_ci_low_pct']:+.0%} to "
            f"{q['depth_ci_high_pct']:+.0%}). A statistical test finds "
            f"no difference between the five levels (p = "
            f"{q['kruskal_p_5_to_25']:.2f}).",
            f"<strong>A 25% discount needs "
            f"{q['breakeven_lift_25_vs_5']:.0%} more units per line "
            f"than a 5% discount</strong> just to bring in the same "
            f"revenue. "
            + (
                "Even the top of the likely range falls short of this."
                if caps_out
                else "The top of the likely range reaches it, so a "
                "payoff cannot be ruled out."
            ),
            f"<strong>Cost climbs with depth.</strong> The 25% level "
            f"gave away {_usd(high['DiscountDollars'])} "
            f"({_pct(high['ShareOfDiscountDollars'])} of all discount "
            f"dollars) against {_usd(low['DiscountDollars'])} "
            f"({_pct(low['ShareOfDiscountDollars'])}) at 5%. In total, "
            f"<strong>{_usd(q['excess_over_5pct_dollars'])}</strong> "
            f"({_pct(q['excess_share_of_discount'])} of discount "
            f"dollars, {_pct(q['excess_pct_of_net_revenue'], 1)} of "
            f"net revenue) went to the part of discounts above 5%.",
        ]
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
        f"<p>This is observational. Discounts are not assigned at "
        f"random, and larger orders are the ones that get them, which "
        f"is why the same-order comparison matters. That comparison "
        f"uses only the {q['orders_with_both']} orders that mix both "
        f"kinds of line, so its range is wide and cannot rule out "
        f"an effect of a few units. The ranges come from resampling "
        f"customers with a fixed seed. There are no cost figures, so "
        f"the savings are revenue, not profit. "
        f"{q['lines_excluded']} lines with other discounts (1-4% and "
        f"6%) on one to three units are left out of the level "
        f"analysis.</p>"
    )
    base = discounts.BASE_DISCOUNT
    steps = [
        f"Round each discount to two decimals (the sheet stores 5% as "
        f"0.0500000007) and keep the six standard levels: 0, 5, 10, "
        f"15, 20 and 25%. {q['lines_excluded']} lines with other "
        f"discounts are set aside, leaving {q['lines_used']:,} lines.",
        f"Average the units per order line at each level (the table "
        f"above). The range in the table is a standard 95% interval "
        f"that treats each line as independent. The headline ranges "
        f"in the findings are stricter: they resample whole customers "
        f"{discounts.BOOTSTRAP_DRAWS:,} times with a fixed seed, "
        f"because one customer's lines resemble each other.",
        f"Discounted against full price: "
        f"{q['mean_qty_discounted']:.1f} ÷ {q['mean_qty_none']:.1f} − "
        f"1 = {q['qty_lift']:+.0%}.",
        f"Same-order comparison: in each of the "
        f"{q['orders_with_both']} orders that have both kinds of "
        f"line, take the average units of the discounted lines minus "
        f"the average units of the full-price lines, then average "
        f"those {q['orders_with_both']} differences: "
        f"{q['within_order_diff']:+.1f} units. The discounted line was "
        f"larger in {q['within_order_higher']} orders and smaller in "
        f"{q['within_order_lower']}; the rest were equal. A sign test "
        f"gives p = {q['within_order_sign_p']:.2f}.",
        f"Depth: 25% lines against 5% lines is "
        f"{high['MeanQty']:.1f} − {low['MeanQty']:.1f} = "
        f"{q['depth_diff_units']:+.1f} units. Across all five "
        f"discount levels, the Kruskal-Wallis test gives p = "
        f"{q['kruskal_p_5_to_25']:.2f}. A p-value above 0.05 means "
        f"the differences could easily be chance.",
        f"Break-even: at 5% off, a unit brings in {1 - base:.2f} of "
        f"its price; at 25% off, 0.75. To bring in the same revenue "
        f"per line, units must rise by {1 - base:.2f} ÷ 0.75 − 1 = "
        f"{q['breakeven_lift_25_vs_5']:.1%}.",
        f"Discount dollars = unit price × quantity × discount, added "
        f"up for each level (last two table columns). The total is "
        f"{_usd(q['total_discount_dollars'])}, "
        f"{_pct(q['discount_pct_of_gross'], 1)} of gross sales. "
        f"Dollars “above 5%” count only the part of each discount "
        f"over 5 points: unit price × quantity × (discount − 5%), "
        f"which adds up to {_usd(q['excess_over_5pct_dollars'])}.",
    ]
    return (
        "<section class='q' id='q3'><p class='eyebrow'>Question 3</p>"
        "<h2>Do bigger discounts sell more, or do they just give "
        "revenue away?</h2>"
        + _plain(short)
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
            "<p>Compare the units on order lines at each discount "
            "level (0, 5, 10, 15, 20 and 25%). Because buyers who "
            "order more may also get more discounts, the discount has "
            "to be separated from the buyer. So the analysis also "
            "compares discounted and full-price lines inside the same "
            "order, and checks product by product. Finally it adds up "
            "the discount dollars given at each level.</p>",
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
        + _row(
            "How we got this",
            _work(
                steps,
                ["q3_discount_tiers.csv", "results.json"],
                ["northwind_analysis/discounts.py"],
                repo_url,
            ),
        )
        + "</section>"
    )


def _question_four(results, tables, figures, repo_url=""):
    """Write the section on stock-out risk.

    Args:
        results (dict[str, Any]): All reported numbers.
        tables (dict[str, pandas.DataFrame]): Supporting tables.
        figures (pathlib.Path): Folder containing the figure PNGs.
        repo_url (str): Public repository URL for code links.

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
    last = pd.Timestamp(results["meta"]["last_order"])
    window = q["window_days"]
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
    short = (
        f"{q['low_cover']} of {q['active_selling']} active products "
        f"would run out within {q['alert_weeks']:.0f} weeks at their "
        f"current sales rate, and {q['discontinued_out_of_stock']} "
        f"discontinued products that customers still buy are already "
        f"out of stock."
    )
    finding = _bullets(
        [
            f"<strong>{q['low_cover']} of {q['active_selling']}</strong>"
            f" active products with recent sales "
            f"({_pct(q['low_cover_share'])}) have under "
            f"{q['alert_weeks']:.0f} weeks of stock. They account for "
            f"{_pct(q['low_cover_revenue_share'])} of the weekly "
            f"revenue of active products "
            f"({_usd(q['low_cover_weekly_revenue'])} a week).",
            f"<strong>{q['nothing_on_order']} of them have nothing on "
            f"order</strong>, worth "
            f"{_usd(q['nothing_on_order_weekly_revenue'])} a week. "
            f"{_esc(biggest['ProductName'])} is the largest: "
            f"{_usd(biggest['WeeklyRevenue'])} a week with "
            f"{biggest['WeeksCover']:.1f} weeks of stock and no order "
            f"placed.",
            f"<strong>{q['discontinued_selling']} discontinued "
            f"products still sell</strong>, "
            f"{_pct(q['discontinued_revenue_share'])} of weekly "
            f"revenue ({_usd(q['discontinued_weekly_revenue'])}). "
            f"{q['discontinued_out_of_stock']} of them have no stock "
            f"left ({_listing(empty['ProductName'])}), which is "
            f"{_usd(q['discontinued_out_of_stock_weekly_revenue'])} a "
            f"week of demand with nothing to sell.",
        ]
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
        f"<p>The Product sheet has no date, so stock levels are "
        f"assumed current as of the last order. If stock has been "
        f"replenished since, the risk is overstated. Weeks of cover "
        f"use the last {window} days of sales, a period of "
        f"fast growth; cover based on the full history would look "
        f"healthier. Units on order have no arrival dates, so the "
        f"light bars show the best case.</p>"
    )
    steps = [
        f"Take the orders from the last {window} days of the data "
        f"({_date(last - pd.Timedelta(days=window - 1))} to "
        f"{_date(last)}).",
        f"Weekly units for a product = units sold in those {window} "
        f"days ÷ {window / 7:.1f} weeks. Weekly revenue is worked out "
        f"the same way from net revenue.",
        f"Weeks of cover = units in stock ÷ weekly units. Example, "
        f"{_esc(biggest['ProductName'])}: "
        f"{biggest['UnitsInStock']:,.0f} in stock ÷ "
        f"{biggest['WeeklyUnits']:.1f} a week = "
        f"{biggest['WeeksCover']:.1f} weeks, with "
        f"{biggest['UnitsOnOrder']:,.0f} units on order.",
        f"A product is flagged when it is active, has sold in the "
        f"window and has under {q['alert_weeks']:.0f} weeks of cover. "
        f"“Nothing on order” means the Product sheet shows 0 units on "
        f"order. The {q['low_cover']} flagged products add up to "
        f"{_usd(q['low_cover_weekly_revenue'])} a week, "
        f"{_pct(q['low_cover_revenue_share'])} of the weekly revenue "
        f"of active products.",
        "A product counts as discontinued and still selling when its "
        "Discontinued flag is on and it sold at least one unit in the "
        "window.",
    ]
    return (
        "<section class='q' id='q4'><p class='eyebrow'>Question 4</p>"
        "<h2>Which fast-selling products are about to run out, and "
        "are we discontinuing products customers still buy?</h2>"
        + _plain(short)
        + _row(
            "Why it matters",
            "<p>A stock-out loses the sale and can lose the customer. "
            "With orders doubling, stock levels set for slower months "
            "may no longer fit.</p>",
        )
        + _row(
            "Approach",
            f"<p>Estimate how many units of each product sell per "
            f"week, using the last {window} days of orders. Divide the "
            f"units in stock by that weekly rate to get “weeks of "
            f"cover”, with and without units already on order. Flag "
            f"active products under {q['alert_weeks']:.0f} weeks, and "
            f"list discontinued products that still sell.</p>",
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
        + _row(
            "How we got this",
            _work(
                steps,
                ["q4_product_cover.csv", "results.json"],
                ["northwind_analysis/inventory.py"],
                repo_url,
            ),
        )
        + "</section>"
    )


def _terms():
    """Write the plain-English guide to the terms used on the page.

    Args:
        None.

    Returns:
        str: HTML for the glossary block.
    """
    items = [
        (
            "Net revenue",
            "What customers paid: unit price × quantity × (1 − "
            "discount). Freight is not included.",
        ),
        (
            "Same months of both years",
            "The data start in July 1996 and end in early May 1998, so "
            "full years cannot be compared. Growth compares January "
            "to April of 1998 with January to April of 1997.",
        ),
        (
            "Likely range (95% interval)",
            "A range that should contain the true value about 95 times "
            "in 100. If the range includes zero, the data cannot rule "
            "out “no effect”.",
        ),
        (
            "p-value",
            "How easily the result could come from chance alone. Above "
            "0.05 means the difference could easily be chance.",
        ),
        (
            "Weeks of cover",
            "Units in stock divided by units sold per week: how long "
            "the stock lasts at the current sales rate.",
        ),
        (
            "Silent or lapsed account",
            "A customer whose time since their last order is far "
            "longer than their own usual time between orders.",
        ),
    ]
    body = "".join(
        f"<dt>{_esc(term)}</dt><dd>{_esc(text)}</dd>"
        for term, text in items
    )
    return (
        "<div class='note' id='terms'><h2>Plain-English guide</h2>"
        f"<dl class='terms'>{body}</dl></div>"
    )


def _how_to_check(results, repo_url):
    """Write the section that shows how to verify the numbers.

    Args:
        results (dict[str, Any]): All reported numbers.
        repo_url (str): Public repository URL for code links.

    Returns:
        str: HTML for the check-our-work block.
    """
    meta = results["meta"]
    lines = meta["order_lines"]
    orders = meta["orders"]
    last = lines + 1
    formula = (
        "=SUMPRODUCT('Orders Details'!C2:C"
        f"{last}, 'Orders Details'!D2:D{last}, "
        f"1-ROUND('Orders Details'!E2:E{last}, 2))"
    )
    steps = [
        f"<strong>See the data.</strong> The numbers come from the "
        f"Northwind workbook: "
        f"<a href='{_esc(DATA_SHEET_URL)}'>Google Sheet</a>, or the "
        f"Excel copy in the repository "
        f"({_code_link('data/Northwind_Database.xlsx', repo_url)}).",
        f"<strong>Check the total in a spreadsheet.</strong> In the "
        f"<em>Orders Details</em> tab, type this into any empty cell: "
        f"<code>{_esc(formula)}</code>. It should show "
        f"{_usd(meta['net_revenue'])}. Counting the rows in the "
        f"<em>Orders</em> tab should give {orders} orders.",
        "<strong>Open every number.</strong> Each “How we got this” "
        "block above lists the exact table and code file, and "
        f"{_data_link('results.json')} holds every figure quoted on "
        "this page.",
        f"<strong>Read the code.</strong> "
        f"{_code_link('run_all.py', repo_url)} runs the analysis; each "
        f"question has its own module. "
        f"{_code_link('README.md', repo_url)} explains how to rebuild "
        f"everything, and "
        f"{_code_link('DOCSTRING_REPORT.md', repo_url)} documents "
        f"every function.",
        f"<strong>See the independent checks.</strong> "
        f"{_code_link('verify_with_sql.py', repo_url)} recomputes the "
        f"headline numbers with SQL in a separate database, and "
        f"{_code_link('tests/test_analysis.py', repo_url)} tests the "
        f"logic.",
    ]
    return (
        "<div class='note' id='how-to-check'><h2>Check our work</h2>"
        "<p>Every number on this page can be traced back to the "
        "data.</p><ol class='tight'>"
        + "".join(f"<li>{step}</li>" for step in steps)
        + "</ol></div>"
    )


def _repo_script():
    """Return the script that points code links at the GitHub repo.

    Args:
        None.

    Returns:
        str: HTML ``script`` element. On a ``github.io`` address it
        rewrites links that have no repository address yet.
    """
    return (
        "<script>(function(){var h=location.hostname;"
        "if(!/\\.github\\.io$/.test(h)){return;}"
        "var u=h.split('.')[0];"
        "var p=location.pathname.split('/').filter(Boolean);"
        "var r=(p.length&&p[0]!=='index.html')?p[0]:h;"
        "var b='https://github.com/'+u+'/'+r+'/blob/main/';"
        "var a=document.querySelectorAll('a[data-repo-path]');"
        "for(var i=0;i<a.length;i++){"
        "if(a[i].getAttribute('href').charAt(0)==='#'){"
        "a[i].href=b+a[i].getAttribute('data-repo-path');}}"
        "})();</script>"
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
        repo_url (str): Public GitHub URL for the footer and code
            links; when empty, code links are set from the page
            address if it is a ``github.io`` address.

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
        f"Fulfillment is not where to spend attention. "
        f"Table: {_data_link('side_check_shippers.csv')}.",
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
the business, answered from the Northwind order data. Each answer
shows its reasoning and links to the calculation behind it.</p>
<ul class="facts">
<li><strong>{meta['orders']}</strong> orders</li>
<li><strong>{meta['customers_with_orders']}</strong> customers</li>
<li><strong>{_usd(meta['net_revenue'])}</strong> net revenue</li>
<li>{start} to {end}</li>
</ul>
<nav class="jump" aria-label="Sections">
<a href="#q1">1. Markets</a>
<a href="#q2">2. Customers</a>
<a href="#q3">3. Discounts</a>
<a href="#q4">4. Stock</a>
<a href="#terms">Plain-English guide</a>
<a href="#how-to-check">Check our work</a>
</nav>
</header>
<div class="glance">
<h2>At a glance</h2>
<ul>
{''.join(f'<li>{item}</li>' for item in glance)}
</ul>
</div>
{_question_one(results, tables, figures, repo_url)}
{_question_two(results, tables, figures, repo_url)}
{_question_three(results, tables, figures, repo_url)}
{_question_four(results, tables, figures, repo_url)}
{_terms()}
{_how_to_check(results, repo_url)}
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
{_repo_script()}
</body>
</html>
"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page, encoding="utf-8")
