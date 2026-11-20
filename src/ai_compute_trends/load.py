"""Load Epoch's CSV into SQLite with cleaned, analysis-ready columns."""

import csv
import sqlite3
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "sql"
DEFAULT_CSV = ROOT / "data" / "epoch_notable_ai_models.csv"


def number(value):
    """Parse a numeric cell; blank or malformed values become None."""
    try:
        return float(value) if value.strip() else None
    except ValueError:
        return None


def tokens(value):
    return [part.strip() for part in value.split(",") if part.strip()]


def sector(value):
    """Industry, Academia, Collaboration (any mix of organization types) or Other."""
    kinds = set(tokens(value))
    if not kinds:
        return None
    if len(kinds) > 1:
        return "Collaboration"
    return kinds.pop() if kinds <= {"Industry", "Academia"} else "Other"


def decimal_year(iso):
    if not iso:
        return None, None
    try:
        day = date.fromisoformat(iso)
    except ValueError:
        return None, None
    return day.year, day.year + (day.timetuple().tm_yday - 1) / 365.25


def clean_row(row):
    year, fractional = decimal_year(row["Publication date"].strip())
    countries = tokens(row["Country (of organization)"])
    open_flag = {"Yes": 1, "No": 0}.get(row["Open model weights?"].strip())
    return (
        row["Model"].strip(),
        row["Organization"].strip() or None,
        row["Publication date"].strip() or None,
        year,
        fractional,
        row["Domain"].strip() or None,
        int("Language" in tokens(row["Domain"])),
        sector(row["Organization categorization"]),
        countries[0] if countries else None,
        row["Model accessibility"].strip() or None,
        open_flag,
        int(row["Frontier model"].strip().lower() == "true"),
        row["Confidence"].strip() or None,
        number(row["Parameters"]),
        number(row["Training compute (FLOP)"]),
        number(row["Training compute cost (2023 USD)"]),
    )


def build_database(csv_path=DEFAULT_CSV):
    """Return an in-memory SQLite connection holding the cleaned `models` table."""
    with Path(csv_path).open(encoding="utf-8", newline="") as source:
        rows = [clean_row(row) for row in csv.DictReader(source) if row["Model"].strip()]
    if not rows:
        raise ValueError(f"{csv_path}: no models found")
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript((SQL_DIR / "schema.sql").read_text(encoding="utf-8"))
    db.executemany(
        "INSERT INTO models (model, organization, pub_date, year, decimal_year, domain, is_language,"
        " sector, country, accessibility, open_weights, frontier, confidence, parameters,"
        " compute_flop, cost_usd_2023) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        rows,
    )
    return db


def run_query(db, name):
    """Run sql/queries/<name>.sql and return a list of dicts."""
    sql = (SQL_DIR / "queries" / f"{name}.sql").read_text(encoding="utf-8")
    return [dict(row) for row in db.execute(sql)]
