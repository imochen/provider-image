# Usage

`provider_imagegen.py` supports five subcommands:

- `inspect`: print the resolved provider name, base URL, auth source, and default model
- `diagnose`: print a quick local/provider diagnosis summary
- `generate`: call `/v1/images/generations`
- `reference`: call `/v1/images/edits` with one or more reference images
- `responses`: call `/v1/responses` with `tools: [{type: "image_generation"}]`

Authentication precedence:

1. `OPENAI_API_KEY` from `~/.codex/auth.json` when present and non-null
2. `experimental_bearer_token` from `~/.codex/config.toml`

Provider resolution:

1. Read top-level `model_provider`
2. Read `[model_providers.<name>]`
3. Use that section's `base_url`

JSON transport:

- `--transport auto`: default for `generate` and `responses`; first try Python (`httpx` or `urllib`), then retry provider/WAF 403 blocks with curl
- `--transport python`: use only the Python client path
- `--transport curl`: use `curl --http1.1` with browser-like headers
- `reference` mode is multipart and currently requires `httpx`

Common examples:

```powershell
python scripts/provider_imagegen.py inspect
python scripts/provider_imagegen.py generate --prompt "A warm tea cup illustration" --out output\imagegen\tea.png
python scripts/provider_imagegen.py generate --transport curl --prompt "A warm tea cup illustration" --out output\imagegen\tea-curl.png
python scripts/provider_imagegen.py responses --prompt "A warm tea cup illustration" --out output\imagegen\tea-resp.png
```
