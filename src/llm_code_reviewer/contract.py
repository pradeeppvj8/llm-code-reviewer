"""Exact input/output contract for the review pipeline (Phase 1, Week 1).

INPUT  : path to a unified diff / patch file on disk (see ``load_diff``).
OUTPUT : JSON list of findings, each ``{file, line, severity, comment}``
         (see ``Finding``, ``parse_review_json`` / ``dump_review_json``).

This module is the single source of truth for the contract. The weekend
MVP (``review.py``) and anything after it must build on these types instead
of redefining the shape ad hoc. Validation is intentionally stdlib-only;
structured-output validation with Pydantic lands in Week 2.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

CONTRACT_VERSION = "v0.1"

Severity = Literal["nit", "minor", "major", "critical"]

#: Allowed severity values, ordered lowest to highest.
SEVERITIES: tuple[str, ...] = ("nit", "minor", "major", "critical")


@dataclass(frozen=True)
class Finding:
    """One review finding: the OUTPUT unit of the contract."""

    file: str
    line: int
    severity: Severity
    comment: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the plain-JSON shape the LLM must return."""
        return {
            "file": self.file,
            "line": self.line,
            "severity": self.severity,
            "comment": self.comment,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Finding:
        """Validate a raw dict (e.g. one element of the LLM's JSON) and build a Finding.

        Raises:
            TypeError: if ``data`` is not a dict.
            ValueError: if a field is missing or fails contract validation.
        """
        if not isinstance(data, dict):
            raise ValueError(f"finding must be an object, got {type(data).__name__}")

        missing = {"file", "line", "severity", "comment"} - data.keys()
        if missing:
            raise ValueError(f"finding is missing fields: {sorted(missing)}")

        file, line, severity, comment = (
            data["file"],
            data["line"],
            data["severity"],
            data["comment"],
        )
        if not isinstance(file, str) or not file:
            raise ValueError("'file' must be a non-empty string")
        # bool is a subclass of int — reject it explicitly.
        if not isinstance(line, int) or isinstance(line, bool) or line < 1:
            raise ValueError("'line' must be a positive int (1-based, new file version)")
        if severity not in SEVERITIES:
            raise ValueError(f"'severity' must be one of {list(SEVERITIES)}, got {severity!r}")
        if not isinstance(comment, str) or not comment.strip():
            raise ValueError("'comment' must be a non-empty string")

        return cls(file=file, line=line, severity=severity, comment=comment)


def load_diff(diff_path: str | Path) -> str:
    """Load the INPUT of the contract: the diff file at ``diff_path``.

    Raises:
        FileNotFoundError: if the path does not exist or is not a file.
        ValueError: if the file is empty.
    """
    path = Path(diff_path)
    if not path.is_file():
        raise FileNotFoundError(f"diff file not found: {path}")
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError(f"diff file is empty: {path}")
    return text


def parse_review_json(raw: str) -> list[Finding]:
    """Parse the OUTPUT of the contract: a JSON list of finding objects.

    Raises:
        ValueError: if ``raw`` is not a JSON list of valid findings.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"review output is not valid JSON: {exc}") from exc
    if not isinstance(data, list):
        raise ValueError(
            f"review output must be a JSON list of findings, got {type(data).__name__}"
        )
    return [Finding.from_dict(item) for item in data]


def dump_review_json(findings: list[Finding]) -> str:
    """Serialize findings back to the contract's JSON output shape."""
    return json.dumps([f.to_dict() for f in findings], indent=2)
