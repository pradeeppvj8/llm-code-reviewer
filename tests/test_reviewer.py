"""Week 1 polish: prompt / fence-strip / pretty-print tests (no API calls)."""

from llm_code_reviewer.contract import Finding
from llm_code_reviewer.reviewer import (
    build_review_prompt,
    extract_json,
    format_findings,
)


def test_build_review_prompt_embeds_diff_and_contract():
    diff = "diff --git a/a.py b/a.py\n+print('hi')\n"
    prompt = build_review_prompt(diff)
    assert diff in prompt
    assert '"severity"' in prompt
    assert "nit" in prompt and "critical" in prompt
    assert "[]" in prompt  # no-issues shape documented


def test_extract_json_plain_passthrough():
    raw = '[{"file": "a.py", "line": 1, "severity": "nit", "comment": "x"}]'
    assert extract_json(raw) == raw.strip()


def test_extract_json_strips_fences():
    raw = '```\n[{"file": "a.py", "line": 1, "severity": "nit", "comment": "x"}]\n```'
    assert extract_json(raw) == '[{"file": "a.py", "line": 1, "severity": "nit", "comment": "x"}]'


def test_extract_json_strips_json_fence():
    raw = '```json\n[]\n```'
    assert extract_json(raw) == "[]"


def test_extract_json_strips_whitespace():
    assert extract_json('  []  \n') == "[]"


def test_format_findings_empty():
    assert format_findings([]) == "No Issues Found"


def test_format_findings_one_line_each():
    findings = [
        Finding(file="src/auth.py", line=47, severity="critical", comment="Use a hash check."),
        Finding(file="src/auth.py", line=57, severity="nit", comment="Typo."),
    ]
    out = format_findings(findings).splitlines()
    assert out == [
        "[CRITICAL] src/auth.py:47 - Use a hash check.",
        "[NIT] src/auth.py:57 - Typo.",
    ]
