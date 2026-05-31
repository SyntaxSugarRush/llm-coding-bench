---
name: llm-benchmark
description: "Run LLM coding benchmarks (HumanEval, MBPP, BigCodeBench) and store results in local SQLite DB with chart generation."
version: "2.0.0"
author: OWL / builderz-labs
source: https://github.com/builderz-labs/llm-coding-bench
---

# LLM Coding Benchmark

Run coding benchmarks against any OpenAI-compatible model, store results in SQLite, and generate comparison charts.

Install: `pip install llm-coding-bench` (or from source)

## Quick Workflow

```bash
# 1. Run benchmark
llm-bench \
  --base-url https://openrouter.ai/api/v1 \
  --api-key-file ~/.openrouter_key \
  --model MODEL_NAME

# 2. Store results
llm-bench-store results.json --model MODEL_NAME

# 3. Generate charts
llm-bench-chart
```

## Hermes Integration

When the user asks to benchmark a model:

1. **Get model name + API details** from user
2. **Write key to file** (execute_code — never echo/print the key):
   ```python
   from pathlib import Path
   key_file = Path.home() / '.openrouter_key'
   key_file.write_text('sk-or-...')
   key_file.chmod(0o600)
   ```
3. **Smoke test** (--sample 2) to verify key works
4. **Full run** with --api-key-file ~/.openrouter_key
5. **Store + chart** with llm-bench-store and llm-bench-chart
6. **Report** pass@1 scores and chart path

## Flags

| Tool | Key flags |
|------|-----------|
| llm-bench | `--base-url, --api-key-file, --model, --sample, --benchmarks, --workers` |
| llm-bench-store | `results.json, --model, --notes` |
| llm-bench-chart | `--run-ids, --model, --output, --no-table` |
| llm-bench-init-db | `--db` |

## Benchmarks

- HumanEval: 164 problems
- MBPP: 378 problems
- BigCodeBench: 1,140 problems
- **Total: 1,682**

## Pitfalls

**API key**: background(terminal) calls do NOT propagate shell env vars to Python subprocesses. Always use --api-key-file. A 401 on every call means the key wasn't read.

**MBPP**: Assertions are in `item["assertion"]`, not `item["test"]` — handled by the package.

**BigCodeBench**: Dataset split is `v0.1.4`, not `test` — handled by the package.

## DB Schema

- **runs**: run_id, model, base_url, created_at, notes
- **scores**: run_id, benchmark, passed, total, pass_at_1, time_sec
- **problems**: run_id, benchmark, task_id, passed, output

Default DB: `~/.llm-benchmark/benchmarks.db`

## See Also

- Source: https://github.com/builderz-labs/llm-coding-bench
- Dataset quirks: `references/dataset-quirks.md`
- API key patterns: `references/api-key-patterns.md`
