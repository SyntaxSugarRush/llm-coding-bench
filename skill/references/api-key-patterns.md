# API Key Security Patterns

## The Problem
Shell commands are logged to history. API keys in commands leak to `~/.bash_history`.

## Good Patterns

### File-based (preferred)
```bash
echo 'sk-or-...' > ~/.openrouter_key
chmod 600 ~/.openrouter_key
llm-bench --api-key-file ~/.openrouter_key ...
```

### Environment variable
```bash
export OPENROUTER_API_KEY=sk-or-...ench --base-url URL --model MODEL
```

### In Hermes sessions
Use execute_code to write the key file securely, then run with --api-key-file.

## Bad Patterns (never do)
```bash
llm-bench --api-key sk-or-...   # leaks to history
```

## Verification
Always run `--sample 2` first. If all results FAIL with 401, the key wasn't read correctly.
