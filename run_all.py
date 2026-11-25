"""Run the full Northwind analysis and rebuild every output."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from northwind_analysis import (
    customers,
    data,
    discounts,
    fulfillment,
    inventory,
    markets,
    site,
)

ROOT = Path(__file__).resolve().parent


def parse_args(argv=None):
    """Parse command-line options.

    Args:
        argv (list[str] | None): Arguments to parse; None reads
            ``sys.argv``.

    Returns:
        argparse.Namespace: Fields ``data``, ``out``, ``site`` and
        ``repo_url``.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data",
        default=ROOT / "data" / "Northwind_Database.xlsx",
        type=Path,
        help="Path to the Northwind workbook.",
    )
    parser.add_argument(
        "--out",
        default=ROOT / "outputs",
        type=Path,
        help="Folder for figures, tables and results.json.",
    )
    parser.add_argument(
        "--site",
        default=ROOT / "docs" / "index.html",
        type=Path,
        help="Path of the webpage to write.",
    )
    parser.add_argument(
        "--repo-url",
        default="",
        help="Public GitHub URL to show in the page footer.",
    )
    return parser.parse_args(argv)


def _native(value):
    """Convert numpy and pandas scalars to JSON-safe Python values.

    Args:
        value (Any): Object passed by ``json.dump`` for unknown types.

    Returns:
        Any: A plain int, float, bool, str or list.

    Raises:
        TypeError: If the type cannot be converted.
    """
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    raise TypeError(f"Cannot serialise {type(value)}")


def run(data_path, out_dir, site_path, repo_url=""):
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
    out_dir, site_path = Path(out_dir), Path(site_path)
    tables = data.load_tables(data_path)
    lines = data.build_order_lines(tables)
    prev_year, cur_year, last_month = data.comparison_window(
        tables["Orders"]["OrderDate"]
    )
    figures = out_dir / "figures"
    tabs = out_dir / "tables"
    tabs.mkdir(parents=True, exist_ok=True)

    growth = markets.market_growth(lines, prev_year, cur_year, last_month)
    q1 = markets.growth_summary(
        lines, growth, prev_year, cur_year, last_month
    )
    monthly = markets.monthly_revenue(lines)
    markets.plot_monthly_revenue(monthly, q1, figures / "q1_monthly.png")
    markets.plot_market_growth(growth, q1, figures / "q1_markets.png")
    monthly.to_csv(tabs / "q1_monthly_revenue.csv", index=False)
    growth.to_csv(tabs / "q1_market_growth.csv", index=False)

    ranked = customers.revenue_by_customer(lines)
    lapsed = customers.lapsed_accounts(lines)
    q2 = customers.concentration_summary(
        ranked, lines, prev_year, cur_year, last_month
    )
    q2.update(customers.lapse_summary(lapsed))
    customers.plot_concentration(
        ranked, lapsed, q2, figures / "q2_customers.png"
    )
    ranked.to_csv(tabs / "q2_revenue_by_customer.csv", index=False)
    lapsed.to_csv(tabs / "q2_lapsed_accounts.csv", index=False)

    tiers = discounts.tier_table(lines)
    q3 = discounts.discount_tests(lines)
    q3.update(discounts.robustness(lines))
    discounts.plot_discounts(tiers, figures / "q3_discounts.png")
    discounts.plot_lift_estimates(q3, figures / "q3_lift_estimates.png")
    tiers.to_csv(tabs / "q3_discount_tiers.csv", index=False)

    cover = inventory.product_cover(
        lines, tables["Product"], tables["Categories"]
    )
    q4 = inventory.inventory_summary(cover)
    inventory.plot_inventory(cover, figures / "q4_inventory.png")
    cover.to_csv(tabs / "q4_product_cover.csv", index=False)

    extra, shippers = fulfillment.fulfillment_summary(tables, lines)
    shippers.to_csv(tabs / "side_check_shippers.csv", index=False)

    results = {
        "meta": {
            "first_order": lines["OrderDate"].min(),
            "last_order": lines["OrderDate"].max(),
            "orders": int(lines["OrderID"].nunique()),
            "order_lines": int(len(lines)),
            "net_revenue": float(lines["NetRevenue"].sum()),
            "customers_with_orders": int(lines["CustomerID"].nunique()),
            "customers_total": int(len(tables["Customers"])),
            **data.data_checks(tables),
        },
        "q1": q1,
        "q2": q2,
        "q3": q3,
        "q4": q4,
        "side_check": extra,
    }
    with open(out_dir / "results.json", "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=_native)
    site.build_site(
        results,
        {
            "q1": growth,
            "q1_monthly": monthly,
            "q2_ranked": ranked,
            "q2_lapsed": lapsed,
            "q3": tiers,
            "q4": cover,
            "shippers": shippers,
        },
        figures,
        site_path,
        repo_url,
    )
    site.copy_downloads(out_dir, site_path)
    return results


def main(argv=None):
    """Run the analysis from the command line.

    Args:
        argv (list[str] | None): Arguments to parse; None reads
            ``sys.argv``.

    Returns:
        None. Writes figures, tables, results.json and the webpage.
    """
    args = parse_args(argv)
    run(args.data, args.out, args.site, args.repo_url)
    print(f"Done. Webpage: {args.site}")
    print(f"Figures, tables and results.json: {args.out}")


if __name__ == "__main__":
    main()
