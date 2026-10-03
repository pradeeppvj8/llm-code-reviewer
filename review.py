"""Entry point: review a diff file with a single LLM prompt."""

import argparse,sys
from pathlib import Path
from dotenv import load_dotenv
import os

sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))

from llm_code_reviewer.reviewer import build_review_prompt, _call_gemini, _call_groq, extract_json,format_findings
from llm_code_reviewer.contract import parse_review_json, load_diff


load_dotenv()

DEFAULT_GROQ_MODEL = "openai/gpt-oss-20b"
DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"
DEFAULT_GEMINI_MODEL_2 = "gemini-3.5-flash-lite"

def parse_args(argv=None):
    parser= argparse.ArgumentParser(description="Review a git diff with LLM")
    parser.add_argument("--diff", required=True, help="Path to a .patch file")
    parser.add_argument("--llm", required=False, default="groq", help="LLM provider to use . Default - Groq")
    return parser.parse_args(argv)

def main(argv=None):
    args= parse_args(argv)
    diff_path= args.diff
    llm = str(args.llm).lower()

    if llm not in ('groq' ,'gemini'):
        print("Error: --llm must be only groq or gemini", file=sys.stderr)
        return 2

    if diff_path:
        try:
            diff = load_diff(diff_path)
        except (FileNotFoundError, ValueError) as e:
            print(f"Loading diff failed: {str(e)}", file=sys.stderr)
            return 2

    prompt = build_review_prompt(diff)

    if llm == 'groq':
        groq_key = os.environ.get('GROQ_API_KEY');

        if not groq_key:
            print("Error: GROQ_API_KEY not set...", file=sys.stderr)
            return 2

        try:
            ans = _call_groq(prompt=prompt,model=DEFAULT_GROQ_MODEL,api_key=groq_key)
            #print("DEBUG:RAW", repr(ans[:1000]),file=sys.stderr)
        except Exception as e:
            print(f"LLM call failed: {str(e)}", file=sys.stderr)
            return 1
    else:
        gemini_key = os.environ.get('GEMINI_API_KEY');
        
        if not gemini_key:
            print("Error: GEMINI_API_KEY not set...", file=sys.stderr)
            return 2

        try:
            ans = _call_gemini(prompt=prompt,model=DEFAULT_GEMINI_MODEL,api_key=os.environ.get('GEMINI_API_KEY'))
        except Exception as e:
            print(f"LLM call failed: {str(e)}", file=sys.stderr)
            return 1

    try:
        ans = extract_json(ans)
        formatted_ans = parse_review_json(ans)
    except ValueError as e:
        print(f"Error reading LLM output: {str(e)}", file=sys.stderr)
        return 1;

    print(format_findings(formatted_ans))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())