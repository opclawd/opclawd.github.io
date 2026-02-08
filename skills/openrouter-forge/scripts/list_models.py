#!/usr/bin/env python3
"""List available models from OpenRouter catalog."""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error

MODELS_URL = "https://openrouter.ai/api/v1/models"


def format_price(price_str):
    """Format price per million tokens."""
    try:
        price = float(price_str) * 1_000_000
        if price == 0:
            return "free"
        if price < 0.01:
            return f"${price:.4f}/M"
        return f"${price:.2f}/M"
    except (ValueError, TypeError):
        return "?"


def main():
    parser = argparse.ArgumentParser(description="List OpenRouter models")
    parser.add_argument("--filter", "-f", default=None, help="Filter by name/id (case-insensitive)")
    parser.add_argument("--top", "-n", type=int, default=30, help="Show top N results")
    parser.add_argument("--cheap", action="store_true", help="Sort by price (cheapest first)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(MODELS_URL, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        print(f"Error fetching models: {e}", file=sys.stderr)
        sys.exit(1)

    models = result.get("data", [])

    # Filter
    if args.filter:
        q = args.filter.lower()
        models = [m for m in models if q in m.get("id", "").lower() or q in m.get("name", "").lower()]

    # Sort
    if args.cheap:
        def price_key(m):
            try:
                return float(m.get("pricing", {}).get("prompt", "999"))
            except (ValueError, TypeError):
                return 999
        models.sort(key=price_key)

    models = models[:args.top]

    if args.json:
        out = []
        for m in models:
            pricing = m.get("pricing", {})
            out.append({
                "id": m.get("id"),
                "name": m.get("name"),
                "context": m.get("context_length"),
                "prompt_price": format_price(pricing.get("prompt")),
                "completion_price": format_price(pricing.get("completion")),
            })
        print(json.dumps(out, indent=2))
        return

    # Table output
    print(f"{'Model ID':<45} {'Context':>8}  {'In':>10}  {'Out':>10}")
    print("-" * 80)
    for m in models:
        mid = m.get("id", "?")
        ctx = m.get("context_length", "?")
        pricing = m.get("pricing", {})
        pin = format_price(pricing.get("prompt"))
        pout = format_price(pricing.get("completion"))
        if len(mid) > 44:
            mid = mid[:41] + "..."
        print(f"{mid:<45} {ctx:>8}  {pin:>10}  {pout:>10}")

    print(f"\nShowing {len(models)} models" + (f" matching '{args.filter}'" if args.filter else ""))


if __name__ == "__main__":
    main()
