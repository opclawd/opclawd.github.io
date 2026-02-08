#!/usr/bin/env python3
"""Call any LLM model via OpenRouter API."""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error

API_URL = "https://openrouter.ai/api/v1/chat/completions"


def main():
    parser = argparse.ArgumentParser(description="Call an LLM model via OpenRouter")
    parser.add_argument("--model", "-m", required=True, help="Model ID (e.g. openai/gpt-4.1)")
    parser.add_argument("--prompt", "-p", required=True, help="User prompt")
    parser.add_argument("--system", "-s", default=None, help="System prompt")
    parser.add_argument("--input", "-i", default=None, help="Read file and append to prompt")
    parser.add_argument("--output", "-o", default=None, help="Write response to file")
    parser.add_argument("--temperature", "-t", type=float, default=0.7, help="Temperature (0-2)")
    parser.add_argument("--max-tokens", type=int, default=4096, help="Max output tokens")
    parser.add_argument("--json", action="store_true", help="Request JSON output format")
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    # Build prompt
    user_content = args.prompt
    if args.input:
        try:
            with open(args.input, "r") as f:
                file_content = f.read()
            user_content = f"{args.prompt}\n\n---\n\n{file_content}"
        except FileNotFoundError:
            print(f"Error: Input file not found: {args.input}", file=sys.stderr)
            sys.exit(1)

    # Build messages
    messages = []
    if args.system:
        messages.append({"role": "system", "content": args.system})
    messages.append({"role": "user", "content": user_content})

    # Build request body
    body = {
        "model": args.model,
        "messages": messages,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
    }
    if args.json:
        body["response_format"] = {"type": "json_object"}

    data = json.dumps(body).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://back.pulpouplatform.com",
        "X-Title": "OpenClaw Forge",
    }

    req = urllib.request.Request(API_URL, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        print(f"Error: HTTP {e.code} from OpenRouter", file=sys.stderr)
        print(error_body[:500], file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Error: Connection failed: {e.reason}", file=sys.stderr)
        sys.exit(1)

    # Extract response text
    try:
        content = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        print("Error: Unexpected response format", file=sys.stderr)
        print(json.dumps(result, indent=2)[:500], file=sys.stderr)
        sys.exit(1)

    # Usage info to stderr
    usage = result.get("usage", {})
    model_used = result.get("model", args.model)
    prompt_tokens = usage.get("prompt_tokens", "?")
    completion_tokens = usage.get("completion_tokens", "?")
    print(f"[{model_used}] {prompt_tokens} in / {completion_tokens} out tokens", file=sys.stderr)

    # Output
    if args.output:
        with open(args.output, "w") as f:
            f.write(content)
        print(f"Saved to {args.output}", file=sys.stderr)
    else:
        print(content)


if __name__ == "__main__":
    main()
