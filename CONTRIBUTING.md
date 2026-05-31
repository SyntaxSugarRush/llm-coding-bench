# Contributing

Thanks for your interest in `llm-coding-bench`!

## Development Setup

```bash
git clone https://github.com/SyntaxSugarRush/llm-coding-bench.git
cd llm-coding-bench
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/ -q
```

## Adding a New Benchmark

1. Add a loader function in `src/llm_benchmark/bench.py`
2. Register it in `LOADER_MAP`
3. Update README.md with the benchmark count
4. Add any dataset-specific quirks to `references/dataset-quirks.md`

## Code Style

- Python 3.10+
- Type hints preferred but not required
- Keep functions short and focused — Karpathy guidelines apply
- No speculative abstractions — solve the problem at hand

## Submitting Changes

1. Fork the repo
2. Create a feature branch
3. Make your changes with clear commits
4. Open a PR with a description of what and why

## Publishing to Hermes Skills Hub

After merging to main:
```bash
hermes skills publish skill/ --to github --repo SyntaxSugarRush/llm-coding-bench
```
