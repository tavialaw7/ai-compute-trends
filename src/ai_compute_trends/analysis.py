"""Run the SQL queries, fit growth rates, and write findings, charts and Tableau-ready CSVs."""

import csv
import json
from pathlib import Path

import numpy as np

from .load import build_database, run_query
from .stats import fit

ERAS = (
    ("Before 2010", 0, 2009),
    ("2010 to 2022", 2010, 2022),
    ("2023 to 2026", 2023, 2026),
)
SECTORS = ("Industry", "Collaboration", "Academia", "Other")


def fit_eras(db):
    rows = db.execute(
        "SELECT decimal_year AS t, compute_flop AS c, year, frontier FROM models"
        " WHERE compute_flop > 0 AND decimal_year IS NOT NULL"
    ).fetchall()
    result = {}
    for label, first, last in ERAS:
        chosen = [r for r in rows if first <= r["year"] <= last]
        result[label] = fit([r["t"] for r in chosen], [r["c"] for r in chosen])
    frontier = [r for r in rows if r["frontier"] and r["year"] >= 2010]
    result["Frontier models, 2010 on"] = fit([r["t"] for r in frontier], [r["c"] for r in frontier])
    return result


def pivot_sector(rows):
    table = {}
    for row in rows:
        table.setdefault(row["year"], dict.fromkeys(SECTORS, 0.0))[row["sector"]] = row["pct"]
    return table


def tableau_exports(db, out_dir, queries):
    out_dir.mkdir(parents=True, exist_ok=True)
    cursor = db.execute(
        "SELECT id, model, organization, pub_date, year, domain, is_language, sector, country,"
        " accessibility, open_weights, frontier, confidence, parameters, compute_flop,"
        " cost_usd_2023 FROM models ORDER BY id"
    )
    with (out_dir / "models_clean.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([c[0] for c in cursor.description] + ["log10_compute_flop"])
        for row in cursor:
            flop = row["compute_flop"]
            writer.writerow(list(row) + [round(float(np.log10(flop)), 4) if flop else ""])
    sectors = pivot_sector(queries["sector_share_by_year"])
    median = {r["year"]: r["median_flop"] for r in queries["median_compute_by_year"]}
    opened = {r["year"]: r["pct_open"] for r in queries["open_weights_by_year"]}
    with (out_dir / "yearly_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["year", "models", "with_compute", "pct_with_compute", "median_compute_flop",
                         *(f"pct_{s.lower()}" for s in SECTORS), "pct_open_weights"])
        for row in queries["coverage_by_year"]:
            year = row["year"]
            writer.writerow([year, row["models"], row["with_compute"], row["pct_with_compute"],
                             median.get(year, ""), *(sectors.get(year, {}).get(s, "") for s in SECTORS),
                             opened.get(year, "")])


def analyze(db, out_dir):
    names = ("coverage_by_year", "median_compute_by_year", "sector_share_by_year",
             "open_weights_by_year", "open_weights_by_sector", "country_share_by_period",
             "top_compute", "top_cost")
    queries = {name: run_query(db, name) for name in names}
    sectors = pivot_sector(queries["sector_share_by_year"])
    totals = db.execute(
        "SELECT COUNT(*) AS models, SUM(compute_flop IS NOT NULL) AS with_compute,"
        " SUM(cost_usd_2023 IS NOT NULL) AS with_cost, SUM(frontier) AS frontier, MIN(year) AS first_year, MAX(year) AS last_year,"
        " SUM(year = 2026) AS in_2026 FROM models"
    ).fetchone()
    findings = {
        "totals": dict(totals),
        "fits": fit_eras(db),
        "sector_share": {str(y): v for y, v in sectors.items()},
        "queries": queries,
    }
    (out_dir).mkdir(parents=True, exist_ok=True)
    (out_dir / "findings.json").write_text(json.dumps(findings, indent=2) + "\n", encoding="utf-8")
    tableau_exports(db, out_dir / "tableau", queries)
    return findings


def main(csv_path, out_dir, docs_dir):
    from .charts import draw_all
    from .report import write_report

    db = build_database(csv_path)
    findings = analyze(db, out_dir)
    draw_all(db, findings, docs_dir / "img")
    write_report(findings, docs_dir / "index.html")
    return findings
