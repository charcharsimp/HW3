# Docstring report

Written with the `python-docstrings` skill (Google style, one line per parameter, an output line for every function, 72-character lines). Each entry gives the location and the docstring as written.

## Docstrings written

### `run_all.py`

Module docstring: *Run the full Northwind analysis and rebuild every output.*

#### `parse_args` — [run_all.py:23](run_all.py:23)

```python
"""Parse command-line options.

    Args:
        argv (list[str] | None): Arguments to parse; None reads
            ``sys.argv``.

    Returns:
        argparse.Namespace: Fields ``data``, ``out``, ``site`` and
        ``repo_url``.
    """
```

#### `_native` — [run_all.py:61](run_all.py:61)

```python
"""Convert numpy and pandas scalars to JSON-safe Python values.

    Args:
        value (Any): Object passed by ``json.dump`` for unknown types.

    Returns:
        Any: A plain int, float, bool, str or list.

    Raises:
        TypeError: If the type cannot be converted.
    """
```

#### `run` — [run_all.py:84](run_all.py:84)

```python
"""Run every analysis, save outputs, and build the webpage.

    Args:
        data_path (pathlib.Path): Path to the Northwind workbook.
        out_dir (pathlib.Path): Folder for figures, tables and
            ``results.json``.
        site_path (pathlib.Path): Path of the HTML file to write.
        repo_url (str): Public GitHub URL for the page footer.

    Returns:
        dict[str, Any]: All numbers reported on the webpage.
    """
```

#### `main` — [run_all.py:177](run_all.py:177)

```python
"""Run the analysis from the command line.

    Args:
        argv (list[str] | None): Arguments to parse; None reads
            ``sys.argv``.

    Returns:
        None. Writes figures, tables, results.json and the webpage.
    """
```

### `northwind_analysis/__init__.py`

Module docstring: *Reproducible Northwind business analysis (Python only).*

### `northwind_analysis/customers.py`

Module docstring: *Question 2: how concentrated is revenue, and who is lapsing.*

#### `revenue_by_customer` — [northwind_analysis/customers.py:16](northwind_analysis/customers.py:16)

```python
"""Rank customers by lifetime net revenue.

    Args:
        lines (pandas.DataFrame): Order lines from
            ``data.build_order_lines``.

    Returns:
        pandas.DataFrame: One row per customer, largest first, with
        revenue, share of total, cumulative share, and rank.
    """
```

#### `concentration_summary` — [northwind_analysis/customers.py:42](northwind_analysis/customers.py:42)

```python
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
```

#### `lapsed_accounts` — [northwind_analysis/customers.py:90](northwind_analysis/customers.py:90)

```python
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
```

#### `lapse_summary` — [northwind_analysis/customers.py:150](northwind_analysis/customers.py:150)

```python
"""Summarise the lapsed-account flags.

    Args:
        lapsed (pandas.DataFrame): Output of ``lapsed_accounts``.

    Returns:
        dict[str, Any]: Number of lapsed accounts, their share of
        trailing-year revenue, and the largest lapsed account.
    """
```

#### `plot_concentration` — [northwind_analysis/customers.py:180](northwind_analysis/customers.py:180)

```python
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
```

### `northwind_analysis/data.py`

Module docstring: *Load the Northwind workbook and build the order-line table.*

#### `load_tables` — [northwind_analysis/data.py:17](northwind_analysis/data.py:17)

```python
"""Read the needed Northwind sheets from the Excel workbook.

    Args:
        path (str | pathlib.Path): Path to Northwind_Database.xlsx.

    Returns:
        dict[str, pandas.DataFrame]: Sheet name mapped to its table.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
    """
```

#### `build_order_lines` — [northwind_analysis/data.py:36](northwind_analysis/data.py:36)

```python
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
```

#### `data_checks` — [northwind_analysis/data.py:92](northwind_analysis/data.py:92)

```python
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
```

#### `comparison_window` — [northwind_analysis/data.py:121](northwind_analysis/data.py:121)

```python
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
```

### `northwind_analysis/discounts.py`

Module docstring: *Question 3: what do discounts buy, and what do they cost.*

#### `tier_lines` — [northwind_analysis/discounts.py:17](northwind_analysis/discounts.py:17)

```python
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
```

#### `tier_table` — [northwind_analysis/discounts.py:34](northwind_analysis/discounts.py:34)

```python
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
```

#### `discount_tests` — [northwind_analysis/discounts.py:74](northwind_analysis/discounts.py:74)

```python
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
```

#### `_customer_interval` — [northwind_analysis/discounts.py:144](northwind_analysis/discounts.py:144)

```python
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
```

#### `robustness` — [northwind_analysis/discounts.py:170](northwind_analysis/discounts.py:170)

```python
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
```

#### `robustness.lift` — [northwind_analysis/discounts.py:200](northwind_analysis/discounts.py:200)

```python
"""Compute the discounted-over-full-price lift of a sample.

        Args:
            sample (list[tuple[numpy.ndarray, numpy.ndarray]]):
                Resampled customers, each holding full-price and
                discounted line quantities.

        Returns:
            float: Mean discounted units over mean full-price units,
            minus one.
        """
```

#### `robustness.depth` — [northwind_analysis/discounts.py:254](northwind_analysis/discounts.py:254)

```python
"""Compute the 25%-minus-5% difference in mean units.

        Args:
            sample (list[tuple[numpy.ndarray, numpy.ndarray]]):
                Resampled customers, each holding 5% and 25% line
                quantities.

        Returns:
            float: Difference in mean units per line, or NaN when
            the sample has no line at one of the two levels.
        """
```

#### `plot_discounts` — [northwind_analysis/discounts.py:300](northwind_analysis/discounts.py:300)

```python
"""Draw units per line and discount dollars by discount level.

    Args:
        table (pandas.DataFrame): Output of ``tier_table``.
        path (str | pathlib.Path): Output PNG path.

    Returns:
        pathlib.Path: The path that was written.
    """
```

### `northwind_analysis/fulfillment.py`

Module docstring: *Side check: delivery timeliness and freight cost by shipper.*

#### `fulfillment_summary` — [northwind_analysis/fulfillment.py:7](northwind_analysis/fulfillment.py:7)

```python
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
```

### `northwind_analysis/inventory.py`

Module docstring: *Question 4: which products risk running out of stock.*

#### `product_cover` — [northwind_analysis/inventory.py:14](northwind_analysis/inventory.py:14)

```python
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
```

#### `inventory_summary` — [northwind_analysis/inventory.py:92](northwind_analysis/inventory.py:92)

```python
"""Summarise stock-out exposure and discontinued-product sales.

    Args:
        table (pandas.DataFrame): Output of ``product_cover``.

    Returns:
        dict[str, Any]: Counts of active selling products and of
        those with low cover, weekly revenue exposed, and the sales
        and stock position of discontinued products still selling.
    """
```

#### `plot_inventory` — [northwind_analysis/inventory.py:135](northwind_analysis/inventory.py:135)

```python
"""Draw weeks of cover for the best-selling low-stock products.

    Args:
        table (pandas.DataFrame): Output of ``product_cover``.
        path (str | pathlib.Path): Output PNG path.
        top_n (int): Number of products shown, by weekly revenue.

    Returns:
        pathlib.Path: The path that was written.
    """
```

### `northwind_analysis/markets.py`

Module docstring: *Question 1: which customer markets are growing or declining.*

#### `market_growth` — [northwind_analysis/markets.py:18](northwind_analysis/markets.py:18)

```python
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
```

#### `growth_summary` — [northwind_analysis/markets.py:96](northwind_analysis/markets.py:96)

```python
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
```

#### `plot_market_growth` — [northwind_analysis/markets.py:139](northwind_analysis/markets.py:139)

```python
"""Draw revenue change by country as a ranked bar chart.

    Args:
        table (pandas.DataFrame): Output of ``market_growth``.
        summary (dict[str, Any]): Output of ``growth_summary``.
        path (str | pathlib.Path): Output PNG path.

    Returns:
        pathlib.Path: The path that was written.
    """
```

### `northwind_analysis/plotting.py`

Module docstring: *Shared matplotlib style and formatting helpers.*

#### `apply_style` — [northwind_analysis/plotting.py:19](northwind_analysis/plotting.py:19)

```python
"""Set the shared matplotlib style used by every figure.

    Args:
        None.

    Returns:
        None. Updates ``matplotlib.rcParams`` in place.
    """
```

#### `money` — [northwind_analysis/plotting.py:49](northwind_analysis/plotting.py:49)

```python
"""Format a dollar amount compactly.

    Args:
        value (float): Amount in US dollars.
        pos (int | None): Tick position; unused but required by
            matplotlib tick formatters.

    Returns:
        str: Text such as ``$12.3k``, ``-$850`` or ``$1.2M``.
    """
```

#### `save_figure` — [northwind_analysis/plotting.py:69](northwind_analysis/plotting.py:69)

```python
"""Save a figure as a PNG and close it.

    Args:
        fig (matplotlib.figure.Figure): Figure to write.
        path (str | pathlib.Path): Output PNG path; parent folders
            are created.

    Returns:
        pathlib.Path: The path that was written.
    """
```

### `northwind_analysis/site.py`

Module docstring: *Build the single-file webpage from the analysis results.*

#### `_usd` — [northwind_analysis/site.py:203](northwind_analysis/site.py:203)

```python
"""Format dollars with thousands separators.

    Args:
        value (float): Amount in US dollars.

    Returns:
        str: For example ``$1,234``.
    """
```

#### `_usdk` — [northwind_analysis/site.py:215](northwind_analysis/site.py:215)

```python
"""Format dollars in thousands.

    Args:
        value (float): Amount in US dollars.

    Returns:
        str: For example ``$12.3k``.
    """
```

#### `_pct` — [northwind_analysis/site.py:227](northwind_analysis/site.py:227)

```python
"""Format a fraction as a percentage.

    Args:
        value (float): Fraction, where 0.25 means 25%.
        digits (int): Decimal places to show.

    Returns:
        str: For example ``25%``.
    """
```

#### `_date` — [northwind_analysis/site.py:240](northwind_analysis/site.py:240)

```python
"""Format a date without a leading zero on the day.

    Args:
        value (Any): Anything ``pandas.Timestamp`` can parse.

    Returns:
        str: For example ``4 Jul 1996``.
    """
```

#### `_listing` — [northwind_analysis/site.py:253](northwind_analysis/site.py:253)

```python
"""Join names into a readable list.

    Args:
        items (Iterable[Any]): Names to join; each is HTML-escaped.

    Returns:
        str: ``A``, ``A and B`` or ``A, B and C``.
    """
```

#### `_esc` — [northwind_analysis/site.py:268](northwind_analysis/site.py:268)

```python
"""Escape text for safe use inside HTML.

    Args:
        text (Any): Value to convert and escape.

    Returns:
        str: HTML-escaped string.
    """
```

#### `_table` — [northwind_analysis/site.py:280](northwind_analysis/site.py:280)

```python
"""Render a table inside a horizontally scrollable box.

    Args:
        caption (str): Table caption.
        headers (list[str]): Column headings.
        rows (list[list[str]]): Cell text for each row; cells are
            escaped here.

    Returns:
        str: HTML for the table.
    """
```

#### `_figure` — [northwind_analysis/site.py:305](northwind_analysis/site.py:305)

```python
"""Embed a figure PNG as a base64 image with a caption.

    Args:
        figures (pathlib.Path): Folder containing the PNG files.
        name (str): PNG file name inside ``figures``.
        alt (str): Text alternative describing the chart.
        caption (str): Visible caption under the chart.

    Returns:
        str: HTML for the figure.
    """
```

#### `_row` — [northwind_analysis/site.py:325](northwind_analysis/site.py:325)

```python
"""Render one labelled block of a question section.

    Args:
        label (str): Short heading, such as ``Why it matters``.
        body (str): HTML content of the block.
        kind (str): Extra CSS class (``finding`` or ``action``).

    Returns:
        str: HTML for the block.
    """
```

#### `_question_one` — [northwind_analysis/site.py:342](northwind_analysis/site.py:342)

```python
"""Write the section on market growth.

    Args:
        results (dict[str, Any]): All reported numbers.
        tables (dict[str, pandas.DataFrame]): Supporting tables.
        figures (pathlib.Path): Folder containing the figure PNGs.

    Returns:
        str: HTML for question 1.
    """
```

#### `_question_two` — [northwind_analysis/site.py:462](northwind_analysis/site.py:462)

```python
"""Write the section on customer concentration and lapses.

    Args:
        results (dict[str, Any]): All reported numbers.
        tables (dict[str, pandas.DataFrame]): Supporting tables.
        figures (pathlib.Path): Folder containing the figure PNGs.

    Returns:
        str: HTML for question 2.
    """
```

#### `_question_three` — [northwind_analysis/site.py:612](northwind_analysis/site.py:612)

```python
"""Write the section on discounting.

    Args:
        results (dict[str, Any]): All reported numbers.
        tables (dict[str, pandas.DataFrame]): Supporting tables.
        figures (pathlib.Path): Folder containing the figure PNGs.

    Returns:
        str: HTML for question 3.
    """
```

#### `_question_four` — [northwind_analysis/site.py:770](northwind_analysis/site.py:770)

```python
"""Write the section on stock-out risk.

    Args:
        results (dict[str, Any]): All reported numbers.
        tables (dict[str, pandas.DataFrame]): Supporting tables.
        figures (pathlib.Path): Folder containing the figure PNGs.

    Returns:
        str: HTML for question 4.
    """
```

#### `build_site` — [northwind_analysis/site.py:892](northwind_analysis/site.py:892)

```python
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
```

### `verify_with_sql.py`

Module docstring: *Cross-check headline numbers with SQL instead of pandas logic.*

#### `load_database` — [verify_with_sql.py:14](verify_with_sql.py:14)

```python
"""Copy the workbook sheets into an in-memory SQLite database.

    Args:
        path (pathlib.Path): Path to the Northwind workbook.

    Returns:
        sqlite3.Connection: Connection with tables ``orders``,
        ``details``, ``customers`` and ``product``.
    """
```

#### `scalar` — [verify_with_sql.py:45](verify_with_sql.py:45)

```python
"""Run a query that returns a single value.

    Args:
        con (sqlite3.Connection): Open database connection.
        sql (str): SQL text returning one row and one column.
        params (tuple[Any, ...]): Values bound to ``?`` markers.

    Returns:
        float: The single value returned by the query.
    """
```

#### `check` — [verify_with_sql.py:59](verify_with_sql.py:59)

```python
"""Compare a reported number with the SQL result and print it.

    Args:
        label (str): Description shown in the output line.
        expected (float): Value reported by the pandas analysis.
        actual (float): Value recomputed with SQL.
        failures (list[str]): Collects labels of failed checks.

    Returns:
        None. Prints PASS or FAIL and appends to ``failures``.
    """
```

#### `main` — [verify_with_sql.py:81](verify_with_sql.py:81)

```python
"""Verify the numbers in ``outputs/results.json`` with SQL.

    Args:
        None.

    Returns:
        None. Exits with status 1 if any check fails.
    """
```

## Assumptions to check

1. `build_order_lines` / `Discount`: treated as a fraction off the unit price (0.05 = 5%) and rounded to two decimals, because the sheet holds values from 0 to 0.25 with float noise such as 0.0500000007.
2. `build_order_lines` / revenue: uses the price on the order line, not `Product.Price`, because the two differ on about 31% of lines (`data_checks` measures this).
3. `comparison_window` / `order_dates`: the last partial month is dropped unless the final order falls on a month end, because the data stop on 6 May 1998.
4. `market_growth` / `last_month`: treated as inclusive (4 means January through April), matching how `comparison_window` returns it.
5. `market_growth` / `PctChange`: left empty when the earlier revenue is under 2,500 USD (`MIN_BASE`). The threshold is a judgement call; the code does not say where it came from.
6. `market_growth` / `DriverShareOfChange`: left empty unless the country grew by at least 5,000 USD (`DRIVER_MIN_GROWTH`), because a share of a tiny or negative net change can exceed 100% and means little.
7. `lapsed_accounts` / `lines`: "today" is the latest `OrderDate` in the data (6 May 1998), not the calendar date, because the data end in 1998.
8. `lapsed_accounts` / `TypicalGapDays`: the median days between a customer's orders, defined only for customers with three or more orders (two or more gaps).
9. `product_cover` / `products`: stock and units on order are assumed current as of the last order, because the Product sheet carries no date.
10. `product_cover` / weekly demand: the average over the last 120 days (`DEMAND_WINDOW_DAYS`), a window chosen to be recent but long enough to smooth weekly noise.
11. `product_cover` / `Discontinued`: read as a true/false flag; the sheet stores it as boolean values.
12. `tier_lines`: the eight lines with other discounts (1-4% and 6%, one to three units) are excluded from the tier analysis because they are not one of the six standard levels.
13. `fulfillment_summary` / return: an order is late when `ShippedDate` is after `RequiredDate`; orders with no ship date are counted as open and not scored.
14. `plotting.money` / `pos`: documented as unused, because matplotlib tick formatters require the argument and the function ignores it.
15. `_native` / return: pandas timestamps are written to JSON as ISO-format text.
16. `robustness` / within-order comparison: only orders that contain both a full-price and a discounted line are used, and each order contributes the difference between the mean units of its discounted lines and of its full-price lines.
17. `_customer_interval` / bootstrap: whole customers are resampled (2,000 draws, seed `SEED` = 20261122) because lines from one customer are not independent; 95% intervals are the 2.5th and 97.5th percentiles.
18. `robustness` / `breakeven_lift_25_vs_5`: the unit lift a 25% discount needs over a 5% discount for revenue to break even, ignoring cost of goods: 0.95 / 0.75 - 1 = 26.7%. Margin is not in the data, so true break-even would be higher.

## Also noticed

- The `Product` sheet has leftover columns (`Cheap`, `NewPrice`, `Cheap.1`, `IsCheap`, `Unnamed: 14`, `NewPrice.1`) that look like they come from another exercise. The analysis does not use them.
- Two customers (FISSA Fabrica Inter. Salchichas S.A. and Paris specialites) have never ordered, so 89 of 91 customers appear in the revenue results.
- `Mishi Kobe Niku` is discontinued with 29 units in stock and sells about 0.2 units a week, so its weeks of cover (165.7) is an outlier.
- Pandas can also raise a merge error in `build_order_lines`; only the explicit `ValueError` is listed under `Raises:`.

Reply with numbered corrections (for example "1: it's a percent") or ask for any docstring to be rewritten.
