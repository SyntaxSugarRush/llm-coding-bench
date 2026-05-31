#!/usr/bin/env python3
"""Initialize the benchmark results SQLite DB."""

import sqlite3
from pathlib import Path

DEFAULT_DB = Path("~/.llm-benchmark/benchmarks.db").expanduser()

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
    benchmark   TEXT NOT NULL,
    passed      INTEGER NOT NULL,
    total       INTEGER NOT NULL,
    pass_at_1   REAL NOT NULL,
    time_sec    REAL NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS problems (
    problem_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      INTEGER NOT NULL,
    benchmark   TEXT NOT NULL,
    task_id     TEXT NOT NULL,
    passed      INTEGER NOT NULL,
    output      TEXT DEFAULT '',
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_scores_run ON scores(run_id);
CREATE INDEX IF NOT EXISTS idx_problems_run ON problems(run_id, benchmark);
"""


def create_db(db_path: Path = DEFAULT_DB):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(db_path))
    db.executescript(SCHEMA)
    db.close()
    return db_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Initialize benchmark database")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    path = create_db(args.db)
    print(f"DB ready at {path}")


if __name__ == "__main__":
    main()
