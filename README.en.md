<p align="center">
  <img src="assets/provider-image.svg" width="96" height="96" alt="Provider Image logo">
</p>

<h1 align="center">Provider Image</h1>

<p align="center">
  Generate images in Codex through your configured OpenAI-compatible custom provider.
</p>

<p align="center">
  <a href="README.md">中文</a> · English
</p>

<p align="center">
  <img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-0f766e.svg">
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-2563eb.svg">
  <img alt="Codex Skill" src="https://img.shields.io/badge/Codex-skill-7c3aed.svg">
</p>

`Provider Image` is a Codex skill and CLI script. It reads your local `~/.codex/config.toml` provider settings and sends image-generation requests to that OpenAI-compatible provider.

Use this tool only when you intentionally want image requests to go through your custom provider. If you want Codex's default built-in image path, or if you are unsure whether the active provider is trusted, do not enable it yet.

## What It Supports

- Resolves Codex's active `model_provider`, `base_url`, and auth settings
- Supports `/v1/images/generations`
- Supports `/v1/images/edits` for reference-image workflows
- Supports `/v1/responses` with `image_generation`
- Uses `curl --http1.1` with browser-like headers first for better Cloudflare/WAF compatibility
- Falls back to Python transport: JSON uses `httpx` or `urllib`, reference-image mode uses `httpx`
- Works as both a Codex skill and a standalone CLI script

## Quick Install

Easiest path: copy this sentence into Codex:

```text
Please install the Provider Image Codex skill from https://github.com/imochen/provider-image into ~/.codex/skills/provider-image; after installation, run inspect to check the configuration, but do not start image generation for me.
```

Manual install:

```bash
git clone https://github.com/imochen/provider-image.git
cd provider-image
python3 -m pip install -r requirements.txt
python3 ./scripts/install.py
```

Restart Codex after installation. You can also skip skill installation and run the script directly:

```bash
python3 ./scripts/provider_imagegen.py inspect
```

Windows PowerShell:

```powershell
python .\scripts\provider_imagegen.py inspect
python .\scripts\install.py
```

Python 3.11+ is recommended. Python 3.10 and older also need `tomli`.

## Codex Configuration

Your `~/.codex/config.toml` should contain an OpenAI-compatible provider:

```toml
model_provider = "custom"
model = "gpt-5.4"

[model_providers.custom]
base_url = "https://your-provider.example/v1"
wire_api = "responses"
```

If `~/.codex/auth.json` does not contain a usable `OPENAI_API_KEY`, provide a token in `config.toml`:

```toml
experimental_bearer_token = "your-provider-token"
```

Before generating, inspect the resolved provider:

```bash
python3 ./scripts/provider_imagegen.py inspect
```

Confirm that `provider_name`, `base_url`, and `auth_source` are all expected.

## Common Commands

### Text To Image

```bash
python3 ./scripts/provider_imagegen.py generate \
  --prompt "A cozy cat eating an apple, warm illustration style, soft natural light, clean background" \
  --out ./output/cat.png
```

Common parameters:

```bash
python3 ./scripts/provider_imagegen.py generate \
  --size 1024x1024 \
  --quality high \
  --prompt "A warm tea cup illustration" \
  --out ./output/tea.png
```

### Reference Image

```bash
python3 ./scripts/provider_imagegen.py reference \
  --image ./output/reference.png \
  --prompt "Use the cat subject and overall style from this image, change it so the cat is eating a red apple, keep the background simple and clean" \
  --out ./output/cat-reference.png
```

For reference images, say both what to keep and what to change:

```text
Use this image's {things to preserve} as reference, and generate {new scene}. Keep {subject/composition/style/colors/materials/expression}, change {parts to modify} into {target change}. Overall result: {style, mood, use case, aspect ratio}.
```

### Responses Image Tool

```bash
python3 ./scripts/provider_imagegen.py responses \
  --prompt "A cozy cat eating an apple, warm illustration style, soft natural light, clean background" \
  --out ./output/cat-responses.png
```

You can also pass a reference image in `responses` mode:

```bash
python3 ./scripts/provider_imagegen.py responses \
  --image ./output/reference.png \
  --prompt "Use this image as reference and generate a warm cat illustration" \
  --out ./output/cat-reference-responses.png
```

### Transport

The default `--transport auto` tries `curl --http1.1` first, then falls back to Python transport.

```bash
python3 ./scripts/provider_imagegen.py generate \
  --transport curl \
  --prompt "A warm tea cup illustration" \
  --out ./output/tea-curl.png
```

Use only Python transport when debugging the older path:

```bash
python3 ./scripts/provider_imagegen.py generate \
  --transport python \
  --prompt "A warm tea cup illustration" \
  --out ./output/tea-python.png
```

## Use In Codex

Explicit invocation is the most reliable:

```text
Use $provider-image to generate an image: a cozy cat eating an apple, save it to output/imagegen/cat.png
```

With a reference image:

```text
Use $provider-image with output/reference.png as the reference image. Generate an image that preserves the subject shape and overall style, changes the scene to a nighttime desk setup, and saves it to output/imagegen/result.png.
```

Automatic skill triggering is not guaranteed, so mention `$provider-image` when you want this provider path.

## Troubleshooting

### `Error: No bearer token found`

Check whether `~/.codex/auth.json` contains a usable `OPENAI_API_KEY`. If not, set `experimental_bearer_token` in `~/.codex/config.toml`.

### `4xx from /images/generations` or `4xx from /responses`

Confirm that the provider supports the endpoint, your token has image-generation permission, and `base_url` points to the API root, such as `/v1`.

If the response is `403` and contains `error code: 1010`, it is usually Cloudflare or provider-side policy blocking, not a broken skill install. The default `--transport auto` uses curl first; if both curl and Python fallback fail, run:

```bash
python3 ./scripts/provider_imagegen.py diagnose
```

If local config is correct, ask the provider administrator to allow image requests.

### `Curl transport failed; retrying with Python transport...`

This is the expected fallback path. It means curl transport did not succeed, so the tool is trying Python transport. Use `--transport curl` to use only curl, or `--transport python` to use only the Python path while debugging.

## Development

```bash
python3 -m py_compile scripts/provider_imagegen.py scripts/install.py
python3 -m unittest discover -s tests
```

## License

MIT License.
