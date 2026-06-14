# Usage

`provider_imagegen.py` supports three subcommands:

- `inspect`: print the resolved provider name, base URL, auth source, and default model
- `generate`: call `/v1/images/generations`
- `responses`: call `/v1/responses` with `tools: [{type: "image_generation"}]`

Authentication precedence:

1. `OPENAI_API_KEY` from `~/.codex/auth.json` when present and non-null
2. `experimental_bearer_token` from `~/.codex/config.toml`

Provider resolution:

1. Read top-level `model_provider`
2. Read `[model_providers.<name>]`
3. Use that section's `base_url`

Common examples:

```powershell
python scripts/provider_imagegen.py inspect
python scripts/provider_imagegen.py generate --prompt "A warm tea cup illustration" --out output\imagegen\tea.png
python scripts/provider_imagegen.py responses --prompt "A warm tea cup illustration" --out output\imagegen\tea-resp.png
```
