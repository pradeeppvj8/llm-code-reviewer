# llm-code-reviewer

AI Code Review CLI — Phase 1 project (LLM Foundations & Prompt Engineering).

**Status: Week 1 (Friday setup).** Repo skeleton only — the MVP single-shot
script (`review.py`) lands in the Saturday/Sunday build block.

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

**Input:** path to a diff file

```bash
python review.py --diff path/to/diff.patch
```

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
$ python review.py --diff samples/auth.patch
[MAJOR] src/auth.py:42 — Password is compared with == instead of a constant-time compare.
[NIT]   src/auth.py:57 — Typo in error message: "occured" -> "occurred".
```

## Layout

```text
.
├── review.py              # CLI entry point (MVP, weekend build)
├── pyproject.toml         # dependencies + project metadata (uv)
├── requirements.txt       # same runtime deps for pip installs
├── .env.example           # copy to .env, fill in keys (never committed)
├── .gitignore
├── src/llm_code_reviewer/ # package code
│   └── config.py          # loads .env, exposes GEMINI_API_KEY / GROQ_API_KEY
└── tests/
    └── test_smoke.py
```
