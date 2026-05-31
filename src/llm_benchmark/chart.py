#!/usr/bin/env python3
"""Generate visual charts from the benchmark database."""

import argparse
import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from llm_benchmark.create_db import DEFAULT_DB

BENCHMARKS = ["humaneval", "mbpp", "bigcodebench"]
COLORS = {"humaneval": "#2196F3", "mbpp": "#FF9800", "bigcodebench": "#4CAF50"}
LABELS = {"humaneval": "HumanEval", "mbpp": "MBPP", "bigcodebench": "BigCodeBench"}


def fetch_runs(db, run_ids=None, model=None):
    if run_ids:
        ph = ",".join("?" * len(run_ids))
        rows = db.execute(
            f"SELECT run_id, model, base_url, created_at, notes FROM runs WHERE run_id IN ({ph})",
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
    result = {rid: {} for rid in run_ids}
    if not run_ids:
        return result
    ph = ",".join("?" * len(run_ids))
    rows = db.execute(
        f"SELECT run_id, benchmark, passed, total, pass_at_1, time_sec FROM scores WHERE run_id IN ({ph})",
        run_ids,
    ).fetchall()
    for run_id, bench, passed, total, p1, ts in rows:
        result[run_id][bench] = {"pass_at_1": p1, "passed": passed, "total": total, "time_sec": ts}
    return result


def make_bar_chart(runs, scores, output: Path):
    run_ids = [r["run_id"] for r in runs]
    labels = [f"#{r['run_id']}\n{r['model'][:20]}" for r in runs]
    n, nb = len(runs), len(BENCHMARKS)
    x = np.arange(n)
    width = 0.25

    fig, ax = plt.subplots(figsize=(max(10, n * 1.5), 6))
    for i, bench in enumerate(BENCHMARKS):
        vals = [scores.get(rid, {}).get(bench, {}).get("pass_at_1", 0) * 100 for rid in run_ids]
        bars = ax.bar(x + i * width, vals, width, label=LABELS[bench], color=COLORS[bench], zorder=3)
        for bar, val in zip(bars, vals):
            if val > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 1,
                    f"{val:.1f}%",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )

    ax.set_ylabel("Pass@1 (%)")
    ax.set_title("LLM Coding Benchmark — Pass@1 by Model & Benchmark", fontweight="bold")
    ax.set_xticks(x + width * (nb - 1) / 2)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(0, 108)
    ax.legend(loc="upper right")
    ax.grid(axis="y", alpha=0.3, zorder=0)
    ax.set_axisbelow(True)

    plt.tight_layout()
    fig.savefig(str(output), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Chart saved to {output}")


def make_table(runs, scores, output: Path):
    fig_height = max(3, len(runs) * 0.6 + 2)
    fig, ax = plt.subplots(figsize=(14, fig_height))
    ax.axis("off")

    header = ["Run", "Model", "Date", "HumanEval", "MBPP", "BigCodeBench", "Overall", "Notes"]
    rows = []
    for run in runs:
        s = scores.get(run["run_id"], {})
        row = [str(run["run_id"]), run["model"][:25], run["created_at"][:16]]
        op, ot = 0, 0
        for b in BENCHMARKS:
            if b in s:
                row.append(f"{s[b]['pass_at_1']:.1%} ({s[b]['passed']}/{s[b]['total']})")
                op += s[b]["passed"]
                ot += s[b]["total"]
            else:
                row.append("—")
        row.append(f"{op/ot:.1%}" if ot else "—")
        row.append(run["notes"][:30])
        rows.append(row)

    table = ax.table(cellText=rows, colLabels=header, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.4)
    for j in range(len(header)):
        table[0, j].set_facecolor("#333333")
        table[0, j].set_text_props(color="white", fontweight="bold")

    plt.title("LLM Coding Benchmark Results", fontsize=14, fontweight="bold", pad=20)
    plt.tight_layout()
    out = output.with_stem(output.stem + "_table")
    fig.savefig(str(out), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Table saved to {out}")
    return out


def main():
    parser = argparse.ArgumentParser(description="Visualize benchmark results")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--run-ids", nargs="+", type=int, default=[])
    parser.add_argument("--model", default="")
    parser.add_argument("--output", type=Path, default=Path("results.png"))
    parser.add_argument("--no-table", action="store_true")
    args = parser.parse_args()

    if not args.db.exists():
        print(f"DB not found: {args.db}. Run llm-bench-init-db first.", file=__import__("sys").stderr)
        exit(1)

    db = sqlite3.connect(str(args.db))
    runs = fetch_runs(db, run_ids=args.run_ids or None, model=args.model or None)
    if not runs:
        print("No runs found.", file=__import__("sys").stderr)
        exit(1)
    scores = fetch_scores(db, [r["run_id"] for r in runs])
    db.close()

    make_bar_chart(runs, scores, args.output)
    if not args.no_table:
        make_table(runs, scores, args.output)


if __name__ == "__main__":
    main()
