#!/usr/bin/env python3
"""
LLM Coding Benchmark — HumanEval + MBPP + BigCodeBench
Scores any OpenAI-compatible model on pass@1.

Usage:
  python3 bench.py --base-url https://example.com/v1 --api-key sk-xxx --model gpt-4o
  python3 bench.py --base-url https://example.com/v1 --api-key sk-xxx --model gpt-4o --sample 10
  python3 bench.py --base-url https://example.com/v1 --api-key sk-xxx --model gpt-4o --benchmarks humaneval mbpp
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import OpenAI

# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------

def load_humaneval():
    """Returns list of {task_id, prompt, test, entry_point}."""
    from evalplus.data import get_human_eval_plus
    raw = get_human_eval_plus()
    problems = []
    for item in raw.values():
        problems.append({
            "task_id": item["task_id"],
            "prompt": item["prompt"],
            "test": item["test"],
            "entry_point": item["entry_point"],
        })
    return problems


def load_mbpp():
    """Returns list of {task_id, prompt, test, entry_point}."""
    from evalplus.data import get_mbpp_plus
    raw = get_mbpp_plus()
    problems = []
    for item in raw.values():
        problems.append({
            "task_id": item["task_id"],
            "prompt": item["prompt"],
            "test": item.get("assertion", item.get("test", "")),
            "entry_point": item["entry_point"],
        })
    return problems


def load_bigcodebench():
    """Returns list of {task_id, prompt, test, entry_point} from HuggingFace."""
    from datasets import load_dataset
    ds = load_dataset("BigCode/bigcodebench", split="v0.1.4")
    problems = []
    for row in ds:
        # complete_prompt has full imports + function stub — that's what the model sees
        problems.append({
            "task_id": row["task_id"],
            "prompt": row["complete_prompt"],
            "test": row["test"],
            "entry_point": row["entry_point"],
        })
    return problems


# ---------------------------------------------------------------------------
# Code extraction
# ---------------------------------------------------------------------------

def extract_code(text):
    """Pull Python code from LLM output. Try ```python block, then ``` block, then raw."""
    # Try ```python ... ```
    m = re.search(r"```python\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Try ``` ... ```
    m = re.search(r"```\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Try def ... block
    m = re.search(r"((?:def |class ).*)", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()


# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------

def call_api(client, model, prompt, max_tokens=1024):
    """Send prompt to API, return generated text."""
    messages = [
        {"role": "system", "content": "You are a Python programmer. Write only the requested function. No explanations, no examples, no markdown."},
        {"role": "user", "content": prompt},
    ]
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.0,
    )
    return resp.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# Test execution
# ---------------------------------------------------------------------------

def run_tests(code, test_code, timeout=30):
    """
    Execute code + test in a subprocess. Returns (passed: bool, output: str).
    """
    full_code = code + "\n\n" + test_code + "\nprint('ALL_TESTS_PASSED')"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(full_code)
        f.flush()
        tmp_path = f.name
    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout + result.stderr
        passed = "ALL_TESTS_PASSED" in output and result.returncode == 0
        return passed, output
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    except Exception as e:
        return False, str(e)
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Run one benchmark
# ---------------------------------------------------------------------------

def run_benchmark(name, problems, client, model, max_tokens, timeout, workers):
    """Run all problems in a benchmark. Returns list of {task_id, passed, output}."""
    results = []

    def _run_one(prob):
        try:
            full_prompt = prob["prompt"]
            completion = call_api(client, model, full_prompt, max_tokens=max_tokens)
            code = extract_code(completion)
            passed, output = run_tests(code, prob["test"], timeout=timeout)
            return {"task_id": prob["task_id"], "passed": passed, "output": output[-500:] if len(output) > 500 else output}
        except Exception as e:
            return {"task_id": prob["task_id"], "passed": False, "output": f"ERROR: {e}\n{traceback.format_exc()[-300:]}"}

    total = len(problems)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_run_one, p): p for p in problems}
        done = 0
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            done += 1
            mark = "✓" if res["passed"] else "✗"
            print(f"  [{done}/{total}] {res['task_id']} {mark}", flush=True)

    passed_count = sum(1 for r in results if r["passed"])
    return results, passed_count, total


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LLM Coding Benchmark (HumanEval + MBPP + BigCodeBench)")
    parser.add_argument("--base-url", required=True, help="OpenAI-compatible API base URL")
    parser.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY", ""), help="API key (or set OPENAI_API_KEY)")
    parser.add_argument("--api-key-file", default="", help="Path to file containing API key")
    parser.add_argument("--model", required=True, help="Model name to benchmark")
    parser.add_argument("--benchmarks", nargs="+", default=["humaneval", "mbpp", "bigcodebench"],
                        choices=["humaneval", "mbpp", "bigcodebench"], help="Which benchmarks to run")
    parser.add_argument("--sample", type=int, default=0, help="Run only N random problems per benchmark (0 = all)")
    parser.add_argument("--max-tokens", type=int, default=1024, help="Max tokens for each completion")
    parser.add_argument("--timeout", type=int, default=30, help="Seconds per test execution")
    parser.add_argument("--workers", type=int, default=4, help="Parallel API calls")
    parser.add_argument("--output", default="results.json", help="Output JSON file")
    args = parser.parse_args()

    api_key = args.api_key
    if args.api_key_file:
        api_key = Path(args.api_key_file).read_text().strip()
    if not api_key:
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        print("ERROR: No API key. Use --api-key, --api-key-file, or set OPENROUTER_API_KEY env var.", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(base_url=args.base_url, api_key=api_key)

    print(f"Model: {args.model}")
    print(f"API:   {args.base_url}")
    print(f"Benchmarks: {', '.join(args.benchmarks)}")
    if args.sample:
        print(f"Sample: {args.sample} problems per benchmark")
    print()

    loaders = {"humaneval": load_humaneval, "mbpp": load_mbpp, "bigcodebench": load_bigcodebench}
    all_results = {}
    summary = {}

    for bench_name in args.benchmarks:
        print(f"=== Loading {bench_name} ===")
        problems = loaders[bench_name]()
        print(f"  {len(problems)} problems loaded")

        if args.sample and args.sample > 0:
            import random
            random.seed(42)
            problems = random.sample(problems, min(args.sample, len(problems)))
            print(f"  Sampled {len(problems)} problems")

        print(f"\n=== Running {bench_name} ===")
        t0 = time.time()
        results, passed, total = run_benchmark(
            bench_name, problems, client, model=args.model,
            max_tokens=args.max_tokens, timeout=args.timeout, workers=args.workers,
        )
        elapsed = time.time() - t0
        pass_at_1 = passed / total if total > 0 else 0.0

        all_results[bench_name] = results
        summary[bench_name] = {
            "passed": passed,
            "total": total,
            "pass_at_1": round(pass_at_1, 4),
            "time_seconds": round(elapsed, 1),
        }
        print(f"\n  {bench_name}: {passed}/{total} = {pass_at_1:.1%} ({elapsed:.1f}s)\n")

    # --- Final summary ---
    print("=" * 60)
    print(f"BENCHMARK RESULTS — {args.model}")
    print("=" * 60)
    total_passed = 0
    total_problems = 0
    for bench_name, s in summary.items():
        total_passed += s["passed"]
        total_problems += s["total"]
        print(f"  {bench_name:15s}  {s['passed']:4d}/{s['total']:<4d}  {s['pass_at_1']:6.1%}  ({s['time_seconds']}s)")
    print(f"  {'OVERALL':15s}  {total_passed:4d}/{total_problems:<4d}  {total_passed/total_problems:.1%}" if total_problems else "  No problems run")
    print("=" * 60)

    # --- Save JSON ---
    output = {
        "model": args.model,
        "base_url": args.base_url,
        "summary": summary,
        "details": all_results,
    }
    out_path = Path(args.output)
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\nResults saved to {out_path.resolve()}")


if __name__ == "__main__":
    main()
