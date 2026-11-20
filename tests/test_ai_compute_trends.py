import csv
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np

from ai_compute_trends import analysis, load, stats
from ai_compute_trends.__main__ import main as cli


class Fixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = load.build_database()


class LoadingTests(Fixture):
    def test_row_counts_match_the_source_file(self):
        with load.DEFAULT_CSV.open(encoding="utf-8", newline="") as source:
            rows = list(csv.DictReader(source))
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM models").fetchone()[0], len(rows))
        self.assertEqual(len(rows), 1011)
        with_compute = sum(1 for r in rows if r["Training compute (FLOP)"].strip())
        self.assertEqual(self.db.execute("SELECT COUNT(compute_flop) FROM models").fetchone()[0], with_compute)

    def test_sector_rules(self):
        self.assertEqual(load.sector("Industry"), "Industry")
        self.assertEqual(load.sector("Academia,Academia"), "Academia")
        self.assertEqual(load.sector("Industry,Academia"), "Collaboration")
        self.assertEqual(load.sector("Government"), "Other")
        self.assertIsNone(load.sector(""))

    def test_dates_and_numbers_fail_safe(self):
        self.assertEqual(load.decimal_year("2020-01-01")[0], 2020)
        self.assertEqual(load.decimal_year("not a date"), (None, None))
        self.assertIsNone(load.number("n/a"))
        self.assertEqual(load.number("1e3"), 1000.0)

    def test_empty_input_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder, "empty.csv")
            path.write_text("Model\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load.build_database(path)

    def test_schema_rejects_bad_sector(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO models (model, is_language, frontier, sector) VALUES ('x', 0, 0, 'Bogus')")
        self.db.rollback()


class QueryTests(Fixture):
    def test_open_weights_query_matches_an_independent_count(self):
        with load.DEFAULT_CSV.open(encoding="utf-8", newline="") as source:
            known = [r for r in csv.DictReader(source)
                     if r["Open model weights?"] in ("Yes", "No") and r["Publication date"].startswith("2020")]
        expected = sum(r["Open model weights?"] == "Yes" for r in known)
        row = next(r for r in load.run_query(self.db, "open_weights_by_year") if r["year"] == 2020)
        self.assertEqual((row["known"], row["open_models"]), (len(known), expected))

    def test_sector_shares_sum_to_100_each_year(self):
        totals = {}
        for row in load.run_query(self.db, "sector_share_by_year"):
            totals[row["year"]] = totals.get(row["year"], 0) + row["pct"]
        for year, total in totals.items():
            self.assertAlmostEqual(total, 100, delta=0.35, msg=year)

    def test_median_handles_odd_and_even_counts(self):
        db = sqlite3.connect(":memory:")
        db.row_factory = sqlite3.Row
        db.executescript((load.SQL_DIR / "schema.sql").read_text())
        for year, values in ((2020, [1, 5, 9]), (2021, [1, 3, 5, 9])):
            for value in values:
                db.execute("INSERT INTO models (model, year, is_language, frontier, compute_flop)"
                           " VALUES ('m', ?, 0, 0, ?)", (year, value))
        medians = {r["year"]: r["median_flop"] for r in load.run_query(db, "median_compute_by_year")}
        self.assertEqual(medians, {2020: 5, 2021: 4})

    def test_top_compute_is_sorted_and_positive(self):
        rows = load.run_query(self.db, "top_compute")
        values = [r["compute_flop"] for r in rows]
        self.assertEqual(values, sorted(values, reverse=True))
        self.assertEqual(len(rows), 10)


class StatsTests(unittest.TestCase):
    def test_doubling_time_recovers_a_known_rate(self):
        years = np.linspace(2010, 2020, 50)
        flop = 2 ** (2 * (years - 2010))  # doubles every 6 months
        self.assertAlmostEqual(stats.doubling_time(years, flop), 6.0, places=6)

    def test_fit_is_deterministic_and_interval_brackets_truth(self):
        rng = np.random.default_rng(1)
        years = np.linspace(2010, 2020, 200)
        flop = 2 ** (2 * (years - 2010) + rng.normal(0, 1, 200))
        first, second = stats.fit(years, flop, reps=300, seed=7), stats.fit(years, flop, reps=300, seed=7)
        self.assertEqual(first, second)
        self.assertLess(first["ci_low"], 6.0)
        self.assertGreater(first["ci_high"], 6.0)

    def test_flat_data_reports_infinite_doubling_time(self):
        self.assertEqual(stats.doubling_time([2010, 2011, 2012], [5, 5, 5]), float("inf"))


class PipelineTests(unittest.TestCase):
    def test_cli_outputs_are_complete_and_repeatable(self):
        with tempfile.TemporaryDirectory() as folder:
            runs = []
            for name in ("a", "b"):
                out, docs = Path(folder, name, "out"), Path(folder, name, "docs")
                self.assertEqual(cli(["--out", str(out), "--docs", str(docs)]), 0)
                runs.append((out / "findings.json").read_text(encoding="utf-8"))
                for expected in ("tableau/models_clean.csv", "tableau/yearly_summary.csv"):
                    self.assertTrue((out / expected).stat().st_size > 0, expected)
                for chart in ("compute-over-time", "sector-share", "open-weights", "coverage", "country-share"):
                    self.assertTrue((docs / "img" / f"{chart}.png").stat().st_size > 1000, chart)
            self.assertEqual(runs[0], runs[1])
            findings = json.loads(runs[0])
            self.assertEqual(findings["totals"]["models"], 1011)
            page = Path(folder, "a", "docs", "index.html").read_text(encoding="utf-8")
            self.assertIn(f"{findings['fits']['2010 to 2022']['doubling_months']:.1f} months", page)

    def test_tableau_export_has_a_log_column_matching_compute(self):
        with tempfile.TemporaryDirectory() as folder:
            analysis.analyze(load.build_database(), Path(folder))
            with Path(folder, "tableau", "models_clean.csv").open(encoding="utf-8", newline="") as source:
                rows = [r for r in csv.DictReader(source) if r["compute_flop"]]
            self.assertTrue(rows)
            for row in rows[:25]:
                self.assertAlmostEqual(float(row["log10_compute_flop"]), np.log10(float(row["compute_flop"])), places=3)

    def test_missing_data_file_exits_with_status_2(self):
        with self.assertRaises(SystemExit) as caught:
            cli(["--data", "/nonexistent/file.csv"])
        self.assertEqual(caught.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
