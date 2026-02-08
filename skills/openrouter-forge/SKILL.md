---
name: openrouter-forge
description: Call any LLM model via OpenRouter API for generation, analysis, translation, summarization, code review, or any text task. Use when the user asks to use a specific model (GPT, Claude, Llama, Gemini, Mistral, etc.), when a task benefits from a specialized model, or when chaining multiple models for different subtasks. Also use to list available models or create reusable mini-tools that wrap specific model+prompt combinations.
---

# OpenRouter Forge

Call any model from the OpenRouter catalog with a single command.

## Quick start

```bash
# Simple generation
python3 {baseDir}/scripts/call_model.py --model "openai/gpt-4.1" --prompt "Explain quantum computing in 3 sentences"

# Use a system prompt
python3 {baseDir}/scripts/call_model.py --model "anthropic/claude-sonnet-4-5" --system "You are a Python expert" --prompt "Write a fibonacci generator"

# Save output to file
python3 {baseDir}/scripts/call_model.py --model "meta-llama/llama-4-maverick" --prompt "Write a haiku about AI" --output result.txt

# Read input from file
python3 {baseDir}/scripts/call_model.py --model "openai/gpt-4.1-mini" --prompt "Summarize this:" --input data.txt

# Adjust creativity
python3 {baseDir}/scripts/call_model.py --model "mistralai/mistral-large" --prompt "Creative story about a robot" --temperature 0.9

# JSON mode
python3 {baseDir}/scripts/call_model.py --model "openai/gpt-4.1" --prompt "List 5 countries with capitals" --json
```

## List available models

```bash
python3 {baseDir}/scripts/list_models.py
python3 {baseDir}/scripts/list_models.py --filter "claude"
python3 {baseDir}/scripts/list_models.py --filter "llama" --top 5
python3 {baseDir}/scripts/list_models.py --cheap  # sort by price ascending
```

## Model selection guide

| Task | Recommended model | Why |
|------|------------------|-----|
| Complex reasoning | `anthropic/claude-sonnet-4-5` | Strong reasoning + tools |
| Fast coding | `openai/gpt-4.1` | Fast, good at code |
| Cheap bulk tasks | `openai/gpt-4.1-mini` | Very cheap, decent quality |
| Creative writing | `meta-llama/llama-4-maverick` | Creative, free-form |
| Translation | `openai/gpt-4.1` | Reliable multilingual |
| Summarization | `openai/gpt-4.1-mini` | Cost-effective for bulk |
| Code review | `anthropic/claude-sonnet-4-5` | Catches subtle bugs |

See `references/models.md` for the full catalog with pricing.

## Chain multiple models

For complex tasks, call models sequentially:

```bash
# Step 1: Plan with a reasoning model
python3 {baseDir}/scripts/call_model.py --model "anthropic/claude-sonnet-4-5" \
  --prompt "Create a plan to build a REST API for a bookstore" --output plan.txt

# Step 2: Implement with a coding model
python3 {baseDir}/scripts/call_model.py --model "openai/gpt-4.1" \
  --system "Implement this plan in Python Flask" --input plan.txt --output app.py

# Step 3: Review with another model
python3 {baseDir}/scripts/call_model.py --model "meta-llama/llama-4-maverick" \
  --system "Review this code for bugs and security issues" --input app.py --output review.txt
```

## Create a reusable mini-tool

To turn a frequent model+prompt combo into a permanent skill, create a new skill in the workspace:

```bash
python3 {baseDir}/scripts/create_minitool.py \
  --name "news-summarizer" \
  --description "Summarize news articles in Spanish, 3 bullet points" \
  --model "openai/gpt-4.1-mini" \
  --system "Eres un editor de noticias. Resume en 3 bullet points en espanol." \
  --input-desc "URL or text of a news article"
```

This creates `skills/news-summarizer/` with SKILL.md and a ready-to-use script.

## API key

Uses `OPENROUTER_API_KEY` from environment (already configured).

## Notes

- Response is printed to stdout unless `--output` is specified.
- `--input` reads a file and appends its content to the prompt.
- `--json` adds `response_format: { type: "json_object" }` to the request.
- `--max-tokens` defaults to 4096. Set higher for long outputs.
- Errors print to stderr with the HTTP status and error body.
