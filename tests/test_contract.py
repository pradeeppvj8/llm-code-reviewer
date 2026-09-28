import json

import pytest

from llm_code_reviewer.contract import (
    CONTRACT_VERSION,
    SEVERITIES,
    Finding,
    dump_review_json,
    load_diff,
    parse_review_json,
)


def test_contract_version_pinned():
    assert CONTRACT_VERSION == "v0.1"


def test_severities_match_readme():
    assert SEVERITIES == ("nit", "minor", "major", "critical")


def test_finding_round_trip():
    finding = Finding(file="src/auth.py", line=42, severity="major", comment="Use a constant-time compare.")
    assert Finding.from_dict(finding.to_dict()) == finding


def test_parse_valid_output():
    raw = json.dumps(
        [
            {"file": "src/auth.py", "line": 42, "severity": "major", "comment": "Use a constant-time compare."},
            {"file": "src/auth.py", "line": 57, "severity": "nit", "comment": 'Typo: "occured" -> "occurred".'},
        ]
    )
    findings = parse_review_json(raw)
    assert [f.severity for f in findings] == ["major", "nit"]
    assert findings[0].line == 42


def test_parse_empty_list_ok():
    assert parse_review_json("[]") == []


def test_parse_rejects_non_list():
    with pytest.raises(ValueError):
        parse_review_json('{"file": "a.py"}')


def test_parse_rejects_bad_json():
    with pytest.raises(ValueError):
        parse_review_json("not json")


@pytest.mark.parametrize(
    "bad",
    [
        {"file": "a.py", "line": 1, "severity": "major"},  # missing comment
        {"file": "a.py", "line": 1, "severity": "blocker", "comment": "x"},  # bad severity
        {"file": "a.py", "line": 0, "severity": "minor", "comment": "x"},  # line < 1
        {"file": "a.py", "line": "42", "severity": "minor", "comment": "x"},  # line not int
        {"file": "", "line": 1, "severity": "minor", "comment": "x"},  # empty file
        {"file": "a.py", "line": 1, "severity": "minor", "comment": "  "},  # blank comment
        ["not", "a", "dict"],  # finding not an object
    ],
)
def test_from_dict_rejects_bad_findings(bad):
    with pytest.raises(ValueError):
        Finding.from_dict(bad)


def test_dump_matches_output_shape():
    findings = [Finding(file="a.py", line=1, severity="nit", comment="x")]
    assert json.loads(dump_review_json(findings)) == [
        {"file": "a.py", "line": 1, "severity": "nit", "comment": "x"}
    ]


def test_load_diff_reads_file(tmp_path):
    diff = tmp_path / "sample.patch"
    diff.write_text("diff --git a/a.py b/a.py\n")
    assert load_diff(diff).startswith("diff --git")


def test_load_diff_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_diff(tmp_path / "nope.patch")


def test_load_diff_empty_file(tmp_path):
    diff = tmp_path / "empty.patch"
    diff.write_text("  \n")
    with pytest.raises(ValueError):
        load_diff(diff)
