#!/usr/bin/env python3
"""Store a results.json into the benchmark SQLite database."""

import argparse
import json
import sqlite3
from pathlib import Path

from llm_benchmark.create_db import create_db, DEFAULT_DB


def store(results_path: Path, db_path: Path, model="", base_url="", notes="") -> int:
    create_db(db_path)
    data = json.loads(results_path.read_text())
    resolved_model = model or data.get("model", "unknown")
    resolved_base_url = base_url or data.get("base_url", "unknown")

    db = sqlite3.connect(str(db_path))
    cur = db.cursor()
    cur.execute(
        "INSERT INTO runs (model, base_url, notes) VALUES (?, ?, ?)",
        (resolved_model, resolved_base_url, notes),
    )
    run_id = cur.lastrowid

    for bench_name, s in data.get("summary", {}).items():
        cur.execute(
            "INSERT INTO scores (run_id, benchmark, passed, total, pass_at_1, time_sec) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (run_id, bench_name, s["passed"], s["total"], s["pass_at_1"], s["time_seconds"]),
        )

    for bench_name, problems in data.get("details", {}).items():
        for p in problems:
            cur.execute(
                "INSERT INTO problems (run_id, benchmark, task_id, passed, output) "
                "VALUES (?, ?, ?, ?, ?)",
                (run_id, bench_name, p["task_id"], 1 if p["passed"] else 0, p.get("output", "")),
            )

    db.commit()
    db.close()
    return run_id


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Store benchmark results in DB")
    parser.add_argument("results_json", type=Path)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--model", default="")
    parser.add_argument("--base-url", default="")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()
    run_id = store(args.results_json, args.db, args.model, args.base_url, args.notes)
    print(f"Stored as run_id={run_id} in {args.db}")


if __name__ == "__main__":
    main()
