#!/usr/bin/env python3
"""Create a reusable mini-tool skill that wraps a specific model+prompt combo."""
import argparse
import os
import sys
import stat


def main():
    parser = argparse.ArgumentParser(description="Create a mini-tool skill")
    parser.add_argument("--name", required=True, help="Skill name (lowercase-hyphenated)")
    parser.add_argument("--description", required=True, help="What the tool does")
    parser.add_argument("--model", required=True, help="OpenRouter model ID")
    parser.add_argument("--system", required=True, help="System prompt for the model")
    parser.add_argument("--input-desc", default="Text input", help="Description of expected input")
    parser.add_argument("--workspace", default=None, help="Workspace path (auto-detected)")
    args = parser.parse_args()

    # Find workspace skills dir
    if args.workspace:
        ws = args.workspace
    else:
        ws = os.environ.get("HOME", "/home/node") + "/.openclaw/workspace"

    skill_dir = os.path.join(ws, "skills", args.name)
    scripts_dir = os.path.join(skill_dir, "scripts")

    if os.path.exists(skill_dir):
        print(f"Error: Skill '{args.name}' already exists at {skill_dir}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(scripts_dir, exist_ok=True)

    # Write SKILL.md
    skill_md = f"""---
name: {args.name}
description: {args.description}. Powered by {args.model} via OpenRouter.
---

# {args.name.replace('-', ' ').title()}

{args.description}

## Usage

```bash
python3 {{baseDir}}/scripts/run.py --input "your input here"
python3 {{baseDir}}/scripts/run.py --file input.txt
python3 {{baseDir}}/scripts/run.py --input "your input" --output result.txt
```

## Model

- **Model**: `{args.model}`
- **API**: OpenRouter (uses `OPENROUTER_API_KEY` from environment)

## Input

{args.input_desc}
"""
    with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
        f.write(skill_md)

    # Write run.py script
    run_py = f'''#!/usr/bin/env python3
"""Auto-generated mini-tool: {args.name}"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error

MODEL = "{args.model}"
SYSTEM = """{args.system}"""
API_URL = "https://openrouter.ai/api/v1/chat/completions"


def call_model(user_input):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    body = json.dumps({{
        "model": MODEL,
        "messages": [
            {{"role": "system", "content": SYSTEM}},
            {{"role": "user", "content": user_input}},
        ],
        "temperature": 0.7,
        "max_tokens": 4096,
    }}).encode("utf-8")

    headers = {{
        "Authorization": f"Bearer {{api_key}}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://back.pulpouplatform.com",
        "X-Title": "OpenClaw - {args.name}",
    }}

    req = urllib.request.Request(API_URL, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        content = result["choices"][0]["message"]["content"]
        usage = result.get("usage", {{}})
        print(f"[{{MODEL}}] {{usage.get(\'prompt_tokens\', \'?\')}} in / {{usage.get(\'completion_tokens\', \'?\')}} out", file=sys.stderr)
        return content
    except urllib.error.HTTPError as e:
        print(f"Error: HTTP {{e.code}}", file=sys.stderr)
        print(e.read().decode("utf-8", errors="replace")[:300], file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="{args.description}")
    parser.add_argument("--input", "-i", default=None, help="Direct text input")
    parser.add_argument("--file", "-f", default=None, help="Read input from file")
    parser.add_argument("--output", "-o", default=None, help="Save output to file")
    a = parser.parse_args()

    if a.file:
        with open(a.file, "r") as f:
            user_input = f.read()
    elif a.input:
        user_input = a.input
    else:
        user_input = sys.stdin.read()

    result = call_model(user_input)

    if a.output:
        with open(a.output, "w") as f:
            f.write(result)
        print(f"Saved to {{a.output}}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()
'''
    run_path = os.path.join(scripts_dir, "run.py")
    with open(run_path, "w") as f:
        f.write(run_py)
    os.chmod(run_path, os.stat(run_path).st_mode | stat.S_IEXEC)

    print(f"Mini-tool '{args.name}' created at {skill_dir}")
    print(f"  SKILL.md: {os.path.join(skill_dir, 'SKILL.md')}")
    print(f"  Script:   {run_path}")
    print(f"  Model:    {args.model}")
    print(f"\nUsage: python3 {run_path} --input \"your text here\"")


if __name__ == "__main__":
    main()
