# Dataset Quirks

## HumanEval+
- Source: `evalplus` package (`get_human_eval_plus()`)
- 164 problems
- `item["test"]` contains unittest-style test code with `check(candidate)` function
- Tests use sentinel pattern — bench.py appends check automatically

## MBPP+
- Source: `evalplus` package (`get_mbpp_plus()`)
- 378 problems
- **CRITICAL**: Uses `item["assertion"]` NOT `item["test"]` — handled by bench.py
- Assertions are plain `assert expr == value` statements

## BigCodeBench
- Source: HuggingFace `datasets` (`BigCode/bigcodebench`, split `v0.1.4`)
- 1,140 problems
- **CRITICAL**: Split is versioned (`v0.1.4`), NOT `test` — handled by bench.py
- Use `row["complete_prompt"]` (includes imports + stub), NOT `row["instruct_prompt"]`
- `row["test"]` contains unittest-style test classes

## Common Issues
- LLM sometimes wraps code in markdown fences — `extract_code()` handles this
- BigCodeBench problems can be multi-function — harder to extract correctly
- Timeout of 30s per test is generous; most complete in <1s
