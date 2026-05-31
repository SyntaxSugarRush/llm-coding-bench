#!/usr/bin/env python3
"""Generate a visual chart from the benchmark DB.

Usage:
  python3 chart.py                          # all models, all benchmarks
  python3 chart.py --run-ids 1 3 5         # specific runs
  python3 chart.py --model "gpt-4o"        # all runs for a model
  python3 chart.py --output results.png    # output path (default: ~/llm-benchmark/results.png)
"""

import argparse
import sqlite3
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

DB_PATH = Path("~/llm-benchmark/benchmarks.db").expanduser()
DEFAULT_OUTPUT = Path("~/llm-benchmark/results.png").expanduser()

BENCHMARKS = ["humaneval", "mbpp", "bigcodebench"]
COLORS = {"humaneval": "#2196F3", "mbpp": "#FF9800", "bigcodebench": "#4CAF50"}
LABELS = {"humaneval": "HumanEval", "mbpp": "MBPP", "bigcodebench": "BigCodeBench"}


def fetch_runs(db, run_ids=None, model=None):
    """Return list of {run_id, model, base_url, created_at} dicts."""
    if run_ids:
        placeholders = ",".join("?" * len(run_ids))
        rows = db.execute(
            f"SELECT run_id, model, base_url, created_at, notes FROM runs WHERE run_id IN ({placeholders})",
            run_ids,
        ).fetchall()
    elif model:
        rows = db.execute(
            "SELECT run_id, model, base_url, created_at, notes FROM runs WHERE model = ? ORDER BY created_at",
            (model,),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT run_id, model, base_url, created_at, notes FROM runs ORDER BY created_at"
        ).fetchall()
    return [
        {"run_id": r[0], "model": r[1], "base_url": r[2], "created_at": r[3], "notes": r[4] or ""}
        for r in rows
    ]


def fetch_scores(db, run_ids):
    """Return {run_id: {bench: {pass_at_1, passed, total}}}."""
    result = {rid: {} for rid in run_ids}
    if not run_ids:
        return result
    placeholders = ",".join("?" * len(run_ids))
    rows = db.execute(
        f"SELECT run_id, benchmark, passed, total, pass_at_1, time_sec FROM scores WHERE run_id IN ({placeholders})",
        run_ids,
    ).fetchall()
    for run_id, bench, passed, total, pass_at_1, time_sec in rows:
        result[run_id][bench] = {"pass_at_1": pass_at_1, "passed": passed, "total": total, "time_sec": time_sec}
    return result


def make_runs_table(db, runs, scores, output):
    """Tabulated comparison of all runs."""
    fig_height = max(3, len(runs) * 0.6 + 2)
    fig, ax = plt.subplots(figsize=(14, fig_height))
    ax.axis("off")

    # Build table data
    header = ["Run", "Model", "Date", "HumanEval", "MBPP", "BigCodeBench", "Overall", "Notes"]
    table_data = []
    for run in runs:
        s = scores.get(run["run_id"], {})
        row = [
            str(run["run_id"]),
            run["model"][:25],
            run["created_at"][:16],
        ]
        overall_pass, overall_total = 0, 0
        for bench in BENCHMARKS:
            if bench in s:
                row.append(f"{s[bench]['pass_at_1']:.1%} ({s[bench]['passed']}/{s[bench]['total']})")
                overall_pass += s[bench]["passed"]
                overall_total += s[bench]["total"]
            else:
                row.append("—")
        row.append(f"{overall_pass/overall_total:.1%}" if overall_total else "—")
        row.append(run["notes"][:30])
        table_data.append(row)

    table = ax.table(cellText=table_data, colLabels=header, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.4)

    # Style header
    for j in range(len(header)):
        table[0, j].set_facecolor("#333333")
        table[0, j].set_text_props(color="white", fontweight="bold")

    plt.title("LLM Coding Benchmark Results", fontsize=14, fontweight="bold", pad=20)
    plt.tight_layout()
    output_table = output.with_stem(output.stem + "_table")
    fig.savefig(str(output_table), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Table saved to {output_table}")
    return output_table


def make_bar_chart(db, runs, scores, output):
    """Grouped bar chart: one group per run, bars = benchmarks."""
    run_ids = [r["run_id"] for r in runs]
    labels = [f"#{r['run_id']}\n{r['model'][:20]}" for r in runs]

    n_runs = len(runs)
    n_benches = len(BENCHMARKS)
    x = np.arange(n_runs)
    width = 0.25

    fig, ax = plt.subplots(figsize=(max(10, n_runs * 1.5), 6))

    for i, bench in enumerate(BENCHMARKS):
        vals = []
        for rid in run_ids:
            s = scores.get(rid, {}).get(bench, {})
            vals.append(s.get("pass_at_1", 0) * 100)
        bars = ax.bar(x + i * width, vals, width, label=LABELS[bench], color=COLORS[bench], zorder=3)
        # Value labels on bars
        for bar, val in zip(bars, vals):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                        f"{val:.1f}%", ha="center", va="bottom", fontsize=8)

    ax.set_ylabel("Pass@1 (%)")
    ax.set_title("LLM Coding Benchmark — Pass@1 by Model & Benchmark", fontweight="bold")
    ax.set_xticks(x + width * (n_benches - 1) / 2)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(0, 108)
    ax.legend(loc="upper right")
    ax.grid(axis="y", alpha=0.3, zorder=0)
    ax.set_axisbelow(True)

    plt.tight_layout()
    fig.savefig(str(output), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Chart saved to {output}")
    return output


def main():
    parser = argparse.ArgumentParser(description="Visualize benchmark results from DB")
    parser.add_argument("--run-ids", nargs="+", type=int, default=[], help="Specific run IDs to plot")
    parser.add_argument("--model", default="", help="Filter by model name")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT), help="Output PNG path")
    parser.add_argument("--no-table", action="store_true", help="Skip the table chart")
    args = parser.parse_args()

    db_path = DB_PATH
    if not db_path.exists():
        print(f"DB not found at {db_path}. Run create_db.py first.", file=sys.stderr)
        sys.exit(1)

    db = sqlite3.connect(str(db_path))
    runs = fetch_runs(db, run_ids=args.run_ids or None, model=args.model or None)
    if not runs:
        print("No runs found.", file=sys.stderr)
        sys.exit(1)

    run_ids = [r["run_id"] for r in runs]
    scores = fetch_scores(db, run_ids)
    db.close()

    output = Path(args.output)
    chart_path = make_bar_chart(db=None, runs=runs, scores=scores, output=output)

    table_path = None
    if not args.no_table:
        table_path = make_runs_table(db=None, runs=runs, scores=scores, output=output)

    print(f"\nGenerated:")
    print(f"  Chart: {chart_path}")
    if table_path:
        print(f"  Table: {table_path}")


if __name__ == "__main__":
    main()
