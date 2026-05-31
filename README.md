# llm-coding-bench

LLM coding benchmark tool — scores any OpenAI-compatible model on
**HumanEval**, **MBPP**, and **BigCodeBench** with pass@1 metric.

Stores results in SQLite and generates comparison charts.

## Install

```bash
pip install llm-coding-bench
```

Or install from source:

```bash
git clone https://github.com/builderz-labs/llm-coding-bench.git
cd llm-coding-bench
pip install -e .
```

## Quick Start

```bash
# 1. Run benchmark (all 3 benchmarks, 1,682 problems)
llm-bench \
  --base-url https://openrouter.ai/api/v1 \
  --api-key-file ~/.openrouter_key \
  --model openrouter/owl-alpha

# 2. Quick test (5 problems per benchmark)
llm-bench \
  --base-url https://openrouter.ai/api/v1 \
  --api-key-file ~/.openrouter_key \
  --model openrouter/owl-alpha \
  --sample 5

# 3. Specific benchmarks only
llm-bench \
  --base-url https://openrouter.ai/api/v1 \
  --api-key-file ~/.openrouter_key \
  --model openrouter/owl-alpha \
  --benchmarks humaneval mbpp

# 4. Store results in DB
llm-bench-store results.json --model openrouter/owl-alpha

# 5. Generate comparison chart
llm-bench-chart

# 6. Compare specific runs
llm-bench-chart --run-ids 1 3 5
```

## Benchmarks

| Benchmark | Problems | Description |
|-----------|----------|-------------|
| HumanEval | 164 | Classic Python function synthesis |
| MBPP | 378 | Broader Python programming tasks |
| BigCodeBench | 1,140 | Complex, multi-function, real-world tasks |

**Total: 1,682 problems**

## API Key Security

**Never pass API keys directly in shell commands** — they leak to history.

```bash
# Good: key from file
echo 'sk-or-...' > ~/.openrouter_key
chmod 600 ~/.openrouter_key
llm-bench --api-key-file ~/.openrouter_key ...

# Good: key from env var
export OPENROUTER_API_KEY=sk-or-...
llm-bench --base-url ... --model ...

# BAD: key in command (leaks to history)
llm-bench --api-key sk-or-...   # never do this
```

## Results

After a run you get:
- `results.json` — raw scores + per-problem details
- SQLite DB (`~/.llm-benchmark/benchmarks.db`) — cumulative results across runs
- `results.png` — bar chart comparing models
- `results_table.png` — tabulated comparison

## DB Schema

- **runs**: run_id, model, base_url, created_at, notes
- **scores**: per benchmark — passed, total, pass_at_1, time_sec
- **problems**: per task — pass/fail + output

## Hermes Agent

This tool is also available as a Hermes skill.
See `references/hermes-skill.md` for integration details.

## License

MIT
