"""Draw the five charts used on the findings page."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .analysis import SECTORS, pivot_sector

COLORS = {"Industry": "#2a6f97", "Collaboration": "#e09f3e", "Academia": "#6a994e", "Other": "#9aa0a6"}
INK, MUTED, GRID, BACKGROUND = "#1d2a33", "#5b6b76", "#e3e7ea", "#ffffff"


def style(ax, title, subtitle=None):
    ax.figure.patch.set_facecolor(BACKGROUND)
    ax.set_facecolor(BACKGROUND)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(length=0, colors=MUTED, labelsize=9)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.figure.text(0.05, 0.955, title, fontsize=14, fontweight="bold", color=INK, va="top")
    if subtitle:
        ax.figure.text(0.05, 0.885, subtitle, fontsize=9.5, color=MUTED, va="top")


def save(fig, path):
    fig.savefig(path, dpi=160, facecolor=BACKGROUND)
    plt.close(fig)


def compute_chart(db, findings, path):
    rows = db.execute(
        "SELECT decimal_year AS t, compute_flop AS c, frontier FROM models"
        " WHERE compute_flop > 0 AND decimal_year IS NOT NULL AND year >= 1990"
    ).fetchall()
    t = np.array([r["t"] for r in rows])
    y = np.log10([r["c"] for r in rows])
    frontier = np.array([bool(r["frontier"]) for r in rows])
    fig, ax = plt.subplots(figsize=(9, 5.2))
    fig.subplots_adjust(top=0.78, left=0.08, right=0.97, bottom=0.1)
    ax.scatter(t[~frontier], y[~frontier], s=11, color="#9db4c0", alpha=0.65, label="Other notable models")
    ax.scatter(t[frontier], y[frontier], s=18, color=COLORS["Industry"], label="Frontier models (top of compute at release)")
    for label, first, last, color in (("2010 to 2022", 2010, 2022.999, "#1d2a33"), ("2023 to 2026", 2023, 2027, "#c1440e")):
        mask = (t >= first) & (t <= last)
        slope, intercept = np.polyfit(t[mask], y[mask], 1)
        xs = np.array([t[mask].min(), t[mask].max()])
        months = findings["fits"][label]["doubling_months"]
        ax.plot(xs, slope * xs + intercept, color=color, linewidth=2.2,
                label=f"Fit, {label}: doubles every {months:.1f} months")
    ax.set_ylabel("Training compute (FLOP, log scale)", color=MUTED, fontsize=9)
    ax.set_yticks(range(0, 30, 5))
    ax.set_yticklabels([f"1e{v}" for v in range(0, 30, 5)])
    ax.legend(frameon=False, fontsize=8.5, loc="upper left", bbox_to_anchor=(0.0, 0.98))
    style(ax, f"Training compute doubled about every {findings['fits']['2010 to 2022']['doubling_months']:.0f} months from 2010 to 2022",
          "Each dot is a notable model with a compute estimate. Lines are log-linear fits.")
    save(fig, path)


def sector_chart(findings, path):
    table = pivot_sector(findings["queries"]["sector_share_by_year"])
    years = sorted(table)
    first_n = findings["queries"]["coverage_by_year"][0]["models"]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    fig.subplots_adjust(top=0.78, left=0.08, right=0.82, bottom=0.1)
    ax.stackplot(years, *[[table[y][s] for y in years] for s in SECTORS],
                 colors=[COLORS[s] for s in SECTORS], labels=SECTORS, alpha=0.95)
    for index, sector in enumerate(SECTORS):
        base = sum(table[years[-1]][s] for s in SECTORS[:index])
        if table[years[-1]][sector] >= 3:
            ax.text(years[-1] + 0.2, base + table[years[-1]][sector] / 2, f"{sector} {table[years[-1]][sector]:.0f}%",
                    va="center", fontsize=9, color=COLORS[sector], fontweight="bold")
    ax.set_ylim(0, 100)
    ax.set_xlim(years[0], years[-1])
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels([f"{v}%" for v in (0, 25, 50, 75, 100)])
    style(ax, f"Industry built {table[years[-1]]['Industry']:.0f}% of notable models in {years[-1]}",
          f"Share of notable models by developer type, by publication year. Early years have few models ({first_n} in {years[0]}).")
    save(fig, path)


def open_chart(findings, path):
    rows = findings["queries"]["open_weights_by_year"]
    fig, ax = plt.subplots(figsize=(9, 4.6))
    fig.subplots_adjust(top=0.78, left=0.08, right=0.97, bottom=0.12)
    years = [r["year"] for r in rows]
    values = [r["pct_open"] for r in rows]
    ax.plot(years, values, color=COLORS["Industry"], linewidth=2.5, marker="o")
    for r in rows:
        ax.text(r["year"], r["pct_open"] + 3.5, f"{r['pct_open']:.0f}%", ha="center", fontsize=9, color=INK)
        ax.text(r["year"], 3, f"n={r['known']}", ha="center", fontsize=8, color=MUTED)
    ax.set_ylim(0, 75)
    ax.set_yticks([0, 25, 50, 75])
    ax.set_yticklabels([f"{v}%" for v in (0, 25, 50, 75)])
    style(ax, f"Open weights: {next(r for r in rows if r['year'] == 2020)['pct_open']:.0f}% of models in 2020, {rows[-1]['pct_open']:.0f}% in {rows[-1]['year']}",
          "Share of notable models with publicly released weights, among models where this is recorded.")
    save(fig, path)


def coverage_chart(findings, path):
    rows = findings["queries"]["coverage_by_year"]
    fig, ax = plt.subplots(figsize=(9, 4.4))
    fig.subplots_adjust(top=0.78, left=0.08, right=0.97, bottom=0.12)
    ax.bar([r["year"] for r in rows], [r["pct_with_compute"] for r in rows], color="#9db4c0")
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels([f"{v}%" for v in (0, 25, 50, 75, 100)])
    style(ax, "Compute estimates are missing for a large share of models",
          "Share of each year's notable models with a training-compute estimate. Read the growth fits with this in mind.")
    save(fig, path)


def country_chart(findings, path):
    rows = findings["queries"]["country_share_by_period"]
    periods = sorted({r["period"] for r in rows})
    groups = ["United States", "China", "United Kingdom", "Other"]
    palette = ["#2a6f97", "#c1440e", "#e09f3e", "#9aa0a6"]
    share = {(r["period"], r["country_group"]): r["pct"] for r in rows}
    fig, ax = plt.subplots(figsize=(9, 4.6))
    fig.subplots_adjust(top=0.78, left=0.08, right=0.97, bottom=0.12)
    width = 0.2
    for index, (group, color) in enumerate(zip(groups, palette)):
        xs = np.arange(len(periods)) + (index - 1.5) * width
        values = [share.get((p, group), 0) for p in periods]
        ax.bar(xs, values, width, color=color, label=group)
        for x, v in zip(xs, values):
            ax.text(x, v + 1.2, f"{v:.0f}", ha="center", fontsize=8, color=INK)
    ax.set_xticks(range(len(periods)))
    ax.set_xticklabels(periods)
    ax.set_ylim(0, 80)
    ax.set_yticks([0, 20, 40, 60, 80])
    ax.set_yticklabels([f"{v}%" for v in (0, 20, 40, 60, 80)])
    ax.legend(frameon=False, fontsize=9, ncol=4, loc="upper right")
    style(ax, f"China's share doubled from {share[(periods[1], 'China')]:.0f}% to {share[(periods[2], 'China')]:.0f}% between {periods[1]} and {periods[2]}",
          "Share of notable models by the first listed country of the developing organization.")
    save(fig, path)


def draw_all(db, findings, img_dir):
    img_dir.mkdir(parents=True, exist_ok=True)
    compute_chart(db, findings, img_dir / "compute-over-time.png")
    sector_chart(findings, img_dir / "sector-share.png")
    open_chart(findings, img_dir / "open-weights.png")
    coverage_chart(findings, img_dir / "coverage.png")
    country_chart(findings, img_dir / "country-share.png")
