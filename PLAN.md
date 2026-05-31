# LLM Coding Benchmark — Plan

## Goal
One-file Python script that benchmarks any OpenAI-compatible model against
HumanEval, MBPP, and BigCodeBench and reports pass@1 scores.

## Assumptions
- No GPU on this machine — benchmarks must run via API (OpenAI-compatible endpoint)
- User has `openai` and `evalplus` pip packages (already installed)
- BigCodeBench problems fetched from HuggingFace datasets at runtime
- User sets API_BASE and API_KEY via env vars or CLI flags
- Default model: whatever the API provides (user picks)

## What this is NOT
- NOT a local inference benchmark
- NOT lm-eval-harness (too heavy, too many deps)
- NOT a full agent harness test — just code generation + execution scoring

## Success Criteria
- [ ] `python3 bench.py --base-url https://example.com/v1 --api-key sk-xxx --model gpt-4o`
      runs all 3 benchmarks and prints a table with pass@1 for each
- [ ] Script is a single file, no config files needed
- [ ] HumanEval: 164 problems, MBPP: 378 problems, BigCodeBench: ~1400 problems
- [ ] Each problem: send prompt → get completion → extract code → run tests → score
- [ ] Results saved to JSON file for later comparison
- [ ] --sample N flag to run a subset (for quick testing)
- [ ] Timeout per problem (default 30s) so one slow call doesn't block everything

## Architecture (deliberately simple)

```
bench.py
├── 1. Load datasets (evalplus for HE/MBPP, HF for BigCodeBench)
├── 2. For each problem:
│   ├── Build prompt (system + user message)
│   ├── Call API → get completion
│   ├── Extract code (parse ```python blocks or raw)
│   ├── Combine: prompt + completion → full function
│   ├── Execute tests in subprocess with timeout
│   └── Record pass/fail
├── 3. Compute pass@1 per benchmark
├── 4. Print summary table
└── 5. Save detailed results to JSON
```

## Steps
1. Write bench.py → verify: runs with --help, prints usage
2. Wire up dataset loading → verify: prints problem counts
3. Wire up API call → verify: gets a completion for 1 problem
4. Wire up test execution → verify: scores 1 problem correctly
5. Wire up full loop + summary → verify: runs --sample 5 all three benchmarks
6. Add JSON output → verify: results file written
