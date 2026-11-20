-- One row per notable AI model. Built from data/epoch_notable_ai_models.csv.
-- Derived columns (year, sector, country, open_weights, ...) are cleaned in load.py.
CREATE TABLE models (
    id            INTEGER PRIMARY KEY,
    model         TEXT NOT NULL,
    organization  TEXT,
    pub_date      TEXT,            -- ISO date, NULL when Epoch has no date
    year          INTEGER,
    decimal_year  REAL,
    domain        TEXT,
    is_language   INTEGER NOT NULL CHECK (is_language IN (0, 1)),
    sector        TEXT CHECK (sector IN ('Industry', 'Academia', 'Collaboration', 'Other')),
    country       TEXT,            -- first listed country of the developing organization(s)
    accessibility TEXT,
    open_weights  INTEGER CHECK (open_weights IN (0, 1)),   -- NULL when unknown
    frontier      INTEGER NOT NULL CHECK (frontier IN (0, 1)),
    confidence    TEXT,
    parameters    REAL,
    compute_flop  REAL,            -- training compute; NULL when Epoch has no estimate
    cost_usd_2023 REAL
);
CREATE INDEX idx_models_year ON models (year);
