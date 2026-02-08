# OpenRouter Model Catalog - Quick Reference

## Tier 1: Premium (best quality)

| Model ID | Strengths | Price (in/out per M tokens) |
|----------|-----------|---------------------------|
| `anthropic/claude-sonnet-4-5` | Reasoning, code, analysis | $3 / $15 |
| `openai/gpt-4.1` | General, code, multilingual | $2 / $8 |
| `google/gemini-2.5-pro-preview` | Long context, reasoning | $1.25 / $10 |

## Tier 2: Balanced (good quality, lower cost)

| Model ID | Strengths | Price (in/out per M tokens) |
|----------|-----------|---------------------------|
| `openai/gpt-4.1-mini` | Fast, cheap, decent quality | $0.4 / $1.6 |
| `meta-llama/llama-4-maverick` | Creative, open-source | $0.2 / $0.6 |
| `mistralai/mistral-large` | European, multilingual | $2 / $6 |
| `google/gemini-2.5-flash` | Very fast, cheap | $0.15 / $0.60 |

## Tier 3: Budget (high volume, low cost)

| Model ID | Strengths | Price (in/out per M tokens) |
|----------|-----------|---------------------------|
| `meta-llama/llama-4-scout` | Free/cheap, decent | $0.1 / $0.3 |
| `mistralai/mistral-small` | Fast, cheap | $0.1 / $0.3 |
| `qwen/qwen3-235b-a22b` | Large MoE, open-source | $0.2 / $0.6 |

## Specialized

| Model ID | Use case |
|----------|----------|
| `openai/gpt-4.1` + `--json` | Structured data extraction |
| `anthropic/claude-sonnet-4-5` | Code review, debugging |
| `meta-llama/llama-4-maverick` | Creative writing, brainstorming |
| `google/gemini-2.5-flash` | Bulk summarization |

## Notes

- Prices are approximate and change. Run `list_models.py` for current prices.
- All models accessible with the same `OPENROUTER_API_KEY`.
- OpenRouter auto-routes to the cheapest provider for each model.
- Context lengths vary: check with `list_models.py --filter <model>`.
