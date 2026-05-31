#!/usr/bin/env python3
"""Initialize the benchmark results SQLite DB."""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path("~/llm-benchmark/benchmarks.db").expanduser()

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    model       TEXT NOT NULL,
    base_url    TEXT NOT NULL,
    created_at  TEXT DEFAULT (datetime('now')),
    notes       TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS scores (
    score_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      INTEGER NOT NULL,
    benchmark   TEXT NOT NULL,          -- humaneval | mbpp | bigcodebench
    passed      INTEGER NOT NULL,
    total       INTEGER NOT NULL,
    pass_at_1   REAL NOT NULL,          -- 0.0 – 1.0
    time_sec    REAL NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS problems (
    problem_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      INTEGER NOT NULL,
    benchmark   TEXT NOT NULL,
    task_id     TEXT NOT NULL,
    passed      INTEGER NOT NULL,       -- 0 or 1
    output      TEXT DEFAULT '',
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_scores_run ON scores(run_id);
CREATE INDEX IF NOT EXISTS idx_problems_run ON problems(run_id, benchmark);
"""

def main():
    db = sqlite3.connect(str(DB_PATH))
    db.executescript(SCHEMA)
    # Quick sanity check
    tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print(f"DB initialized at {DB_PATH}")
    print(f"Tables: {', '.join(t[0] for t in tables)}")
    db.close()

if __name__ == "__main__":
    main()
