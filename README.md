# llm-code-reviewer

AI Code Review CLI — Phase 1 project (LLM Foundations & Prompt Engineering).

**Status: Week 1 done.** Single-shot MVP works end to end on both providers
(Groq + Gemini) — tested on 3 sample diffs.

## Problem statement

Reviewing diffs by hand is slow and inconsistent. This CLI takes a git diff
and uses an LLM (Gemini or a Groq-hosted model, both free tier) to return
structured review findings, so every diff gets a fast, repeatable first pass.

## How it works (Week 1 scope)

1. Read a diff/patch file from disk.
2. Send it as a single prompt to the LLM.
3. Parse the structured JSON response and pretty-print it to the terminal.

No function calling or streaming yet — those land in Weeks 3–4 of Phase 1.

## Input / output contract

**Input:** path to a diff file, plus provider choice

```bash
python review.py --diff path/to/diff.patch --llm groq    # default
python review.py --diff path/to/diff.patch --llm gemini
```

| Flag | Values | Default | Notes |
|------|--------|---------|-------|
| `--diff` | path to `.patch` file | (required) | Loaded via `load_diff` — must exist, non-empty |
| `--llm` | `groq`, `gemini` (case-insensitive) | `groq` | Groq uses `openai/gpt-oss-20b` (`reasoning_effort="low"`, `max_completion_tokens=4096`); Gemini uses `gemini-3.5-flash-lite` (`max_output_tokens=8192`). Keys come from `.env` (`GROQ_API_KEY` / `GEMINI_API_KEY`). |

**Output:** JSON list of findings, one object per issue:

```json
[
  {
    "file": "src/auth.py",
    "line": 42,
    "severity": "major",
    "comment": "Password is compared with == instead of a constant-time compare."
  }
]
```

| Field      | Type   | Values / notes                              |
|------------|--------|---------------------------------------------|
| `file`     | string | Path of the file within the diff            |
| `line`     | int    | Line number in the new version of the file  |
| `severity` | string | One of `nit`, `minor`, `major`, `critical`  |
| `comment`  | string | One concrete, actionable review comment     |

Machine-readable source of truth: `src/llm_code_reviewer/contract.py`
(`Finding`, `SEVERITIES`, `load_diff`, `parse_review_json`).

## Setup

Both providers have a free API tier — get keys at
[aistudio.google.com/apikey](https://aistudio.google.com/apikey) and
[console.groq.com/keys](https://console.groq.com/keys).

```bash
cp .env.example .env   # fill in your real keys (.env is git-ignored)
uv sync                # or: pip install -r requirements.txt
uv run pytest          # run the tests
```

## Example output

```text
$ python review.py --diff samples/review_sample.patch --llm gemini
[CRITICAL] src/auth.py:47 - Passwords must not be compared directly in plaintext; use a secure hash verification function like `check_password_hash`.
[NIT] src/auth.py:57 - Typo in error message: 'occured' should be spelled 'occurred'.
[CRITICAL] src/auth.py:64 - Reset tokens must be cryptographically random and unguessable (e.g., using `secrets.token_urlsafe()`), not derived predictably from `user_id`.
```

Exit codes: `0` findings printed (or `No Issues Found`), `2` usage/config error
(bad `--llm`, missing key, unreadable diff), `1` LLM call or output-parse failure.

## Layout

```text
.
├── review.py              # CLI entry point: --diff + --llm, error handling, exit codes
├── pyproject.toml         # dependencies + project metadata (uv)
├── requirements.txt       # same runtime deps for pip installs
├── .env.example           # copy to .env, fill in keys (never committed)
├── .gitignore
├── samples/               # sample diffs for MVP testing (review_sample, wisdom_rag, wisdom_rag_2)
├── src/llm_code_reviewer/ # package code
│   ├── contract.py        # I/O contract: Finding, SEVERITIES, load_diff, parse/dump_review_json
│   ├── reviewer.py        # prompt template, Groq/Gemini callers, extract_json, format_findings
│   └── config.py          # loads .env, exposes GEMINI_API_KEY / GROQ_API_KEY
└── tests/
    ├── test_contract.py   # contract validation tests
    ├── test_reviewer.py   # prompt / fence-strip / pretty-print tests
    └── test_smoke.py
```
