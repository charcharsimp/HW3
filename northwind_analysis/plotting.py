"""Shared matplotlib style and formatting helpers."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

COLORS = {
    "blue": "#2563a8",
    "light_blue": "#a9c6e8",
    "orange": "#d9772b",
    "grey": "#8b93a0",
    "dark": "#1f2933",
}


def apply_style():
    """Set the shared matplotlib style used by every figure.

    Args:
        None.

    Returns:
        None. Updates ``matplotlib.rcParams`` in place.
    """
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.edgecolor": COLORS["grey"],
            "axes.labelcolor": COLORS["dark"],
            "xtick.color": COLORS["dark"],
            "ytick.color": COLORS["dark"],
            "text.color": COLORS["dark"],
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.dpi": 160,
        }
    )


def money(value, pos=None):
    """Format a dollar amount compactly.

    Args:
        value (float): Amount in US dollars.
        pos (int | None): Tick position; unused but required by
            matplotlib tick formatters.

    Returns:
        str: Text such as ``$12.3k``, ``-$850`` or ``$1.2M``.
    """
    sign = "-" if value < 0 else ""
    size = abs(value)
    if size >= 1_000_000:
        return f"{sign}${size / 1_000_000:.1f}M"
    if size >= 1_000:
        return f"{sign}${size / 1_000:.1f}k"
    return f"{sign}${size:,.0f}"


def save_figure(fig, path):
    """Save a figure as a PNG and close it.

    Args:
        fig (matplotlib.figure.Figure): Figure to write.
        path (str | pathlib.Path): Output PNG path; parent folders
            are created.

    Returns:
        pathlib.Path: The path that was written.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path
