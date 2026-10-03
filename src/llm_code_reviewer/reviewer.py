"""single-shot diff review (prompt building only for now)."""

PROMPT_TEMPLATE = """\
You are an expert senior code reviewer. Review the unified diff below and report only real, actionable issues.

Return a JSON array (and nothing else) where each element has exactly these keys:
- "file": path of the file within the diff (string)
- "line": line number in the NEW version of the file (positive integer)
- "severity": one of "nit", "minor", "major", "critical"
- "comment": one concrete, actionable concise review comment (string)

Severity guide:
- nit: style, typo, naming — no behaviour change needed
- minor: small improvement worth making, low risk if skipped
- major: likely bug, security concern, or wrong behaviour — should fix
- critical: definite vulnerability, data loss, or broken behaviour — must fix

Rules:
- Output ONLY the JSON array. No explanation, no prose, no markdown fences.
- If the diff has no issues, output exactly: []
- One object per issue; keep comments short and specific.
- Base "line" on the new-file side of the diff hunks.

Diff to review:
```diff
__DIFF__
```\
"""

def build_review_prompt(diff: str) -> str:
    """Slot ``diff`` into the template and return the full prompt."""
    return PROMPT_TEMPLATE.replace("__DIFF__", diff)

def _call_groq(prompt: str, model: str, api_key: str) -> str:
    from groq import Groq

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert senior code reviewer. Reply with a JSON array only."},
            {"role": "user", "content": prompt}, 
        ],
        temperature=0,
        max_completion_tokens=4096,
        reasoning_effort="low"
    )
    return response.choices[0].message.content

def _call_gemini(prompt: str, model: str, api_key: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model = model , 
                                              contents = prompt, 
                                              config= types.GenerateContentConfig(
                                                    max_output_tokens=8192,
                                                    temperature=0
                                                )
                                              )
    return response.text

def extract_json(raw: str) -> str:
    ''' Strip optional markdown fences so fenced JSON still parses. '''
    lines = raw.strip().splitlines()

    if len(lines) >= 2 and lines[0].startswith("```") and lines[-1].startswith("```"):
        return "\n".join(lines[1:-1]).strip()
    return raw.strip()

def format_findings(findings: list) -> str:
    """ Pretty-print findings for the terminal (one line each). """

    if not findings:
        return "No Issues Found"
    
    return "\n".join(
        f"[{f.severity.upper()}] {f.file}:{f.line} - {f.comment}" for f in findings
    )


    