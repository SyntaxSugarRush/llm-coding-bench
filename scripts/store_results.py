#!/usr/bin/env python3
"""Load a results.json and store it in the SQLite benchmark DB.

Usage:
  python3 store_results.py results.json [--model gpt-4o] [--base-url https://...] [--notes "run description"]
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path("~/llm-benchmark/benchmarks.db").expanduser()


def store(results_path: Path, model: str, base_url: str, notes: str = "") -> int:
    """Insert a results.json into the DB. Returns run_id."""
    data = json.loads(results_path.read_text())

    # Allow override from CLI, but prefer JSON fields
    if not model:
        model = data.get("model", "unknown")
    if not base_url:
        base_url = data.get("base_url", "unknown")

    db = sqlite3.connect(str(db_path := DB_PATH))
    cur = db.cursor()

    cur.execute(
        "INSERT INTO runs (model, base_url, notes) VALUES (?, ?, ?)",
        (model, base_url, notes),
    )
    run_id = cur.lastrowid

    summary = data.get("summary", {})
    details = data.get("details", {})

    for bench_name, s in summary.items():
        cur.execute(
            "INSERT INTO scores (run_id, benchmark, passed, total, pass_at_1, time_sec) VALUES (?, ?, ?, ?, ?, ?)",
            (run_id, bench_name, s["passed"], s["total"], s["pass_at_1"], s["time_seconds"]),
        )

    for bench_name, problems in details.items():
        for p in problems:
            cur.execute(
                "INSERT INTO problems (run_id, benchmark, task_id, passed, output) VALUES (?, ?, ?, ?, ?)",
                (run_id, bench_name, p["task_id"], 1 if p["passed"] else 0, p.get("output", "")),
            )

    db.commit()
    db.close()
    return run_id


def main():
    parser = argparse.ArgumentParser(description="Store benchmark results in DB")
    parser.add_argument("results_json", help="Path to results.json")
    parser.add_argument("--model", default="", help="Override model name")
    parser.add_argument("--base-url", default="", help="Override API base URL")
    parser.add_argument("--notes", default="", help="Optional notes about this run")
    args = parser.parse_args()

    path = Path(args.results_json)
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    run_id = store(path, args.model, args.base_url, args.notes)
    print(f"Stored as run_id={run_id} in {DB_PATH}")


if __name__ == "__main__":
    main()
