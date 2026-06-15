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

`Provider Image` is a local Codex skill and CLI script for generating images through the OpenAI-compatible provider already configured in your Codex environment.

Use it only when you intentionally want image requests to go through your custom provider. If you want Codex's default built-in image path, or if you are unsure whether the active provider is trusted, do not enable this tool. Run `inspect` first.

## Features

- Reads the active `model_provider` from `~/.codex/config.toml`
- Uses the selected provider's `base_url`
- Reuses local Codex authentication settings
- Supports `/v1/images/generations`
- Supports `/v1/images/edits` for reference-image workflows
- Supports `/v1/responses` with `image_generation`
- Prefers `httpx`; plain JSON requests can fall back to Python's standard library
- Supports a `curl --http1.1` fallback for providers whose Cloudflare/WAF rules block Python clients
- Works as both a standalone script and a Codex skill

## Install

Easiest path: copy this sentence into Codex and let Codex install the skill:

```text
Please install the Provider Image Codex skill from https://github.com/imochen/provider-image into ~/.codex/skills/provider-image; after installation, run inspect to check the configuration, but do not start image generation for me.
```

Run directly:

```bash
python3 ./scripts/provider_imagegen.py inspect
```

Install as a Codex skill:

```bash
python3 ./scripts/install.py
```

The installer copies the skill to:

```text
~/.codex/skills/provider-image
```

Restart Codex after installation.

Windows PowerShell:

```powershell
python .\scripts\provider_imagegen.py inspect
python .\scripts\install.py
```

## Dependencies

Python 3.11+ is recommended:

```bash
python3 -m pip install -r requirements.txt
```

At minimum, install `httpx` for the most compatible request path:

```bash
python3 -m pip install httpx
```

Python 3.10 and older also need `tomli`.

## Configuration

Your `~/.codex/config.toml` should include an OpenAI-compatible provider:

```toml
model_provider = "custom"
model = "gpt-5.4"

[model_providers.custom]
base_url = "https://your-provider.example/v1"
wire_api = "responses"
```

If `~/.codex/auth.json` does not contain a usable `OPENAI_API_KEY`, provide:

```toml
experimental_bearer_token = "your-provider-token"
```

## Safety

This tool sends image requests to the `base_url` resolved from your local Codex configuration. Use it only after confirming that the provider and token are the ones you intend to use.

Check first:

```bash
python3 ./scripts/provider_imagegen.py inspect
```

Confirm that `provider_name`, `base_url`, and `auth_source` are all expected before generating images.

## Usage

Inspect the active provider:

```bash
python3 ./scripts/provider_imagegen.py inspect
```

Run a quick local/provider diagnosis:

```bash
python3 ./scripts/provider_imagegen.py diagnose
```

Generate through `/v1/images/generations`:

```bash
python3 ./scripts/provider_imagegen.py generate \
  --prompt "A cozy cat sleeping near a window, soft morning light" \
  --out ./output/cat.png
```

By default, `--transport auto` tries the Python client first, meaning `httpx` or `urllib`. If the provider/WAF returns `403`, Cloudflare, `1010`, or `Your request was blocked`, it retries with `curl --http1.1` and browser-like headers.

You can also choose the transport explicitly:

```bash
python3 ./scripts/provider_imagegen.py generate \
  --transport curl \
  --prompt "A cozy cat sleeping near a window, soft morning light" \
  --out ./output/cat-curl.png
```

To preserve the old behavior and disable fallback:

```bash
python3 ./scripts/provider_imagegen.py generate \
  --transport python \
  --prompt "A cozy cat sleeping near a window, soft morning light" \
  --out ./output/cat-python.png
```

Generate through `/v1/responses` with `image_generation`:

```bash
python3 ./scripts/provider_imagegen.py responses \
  --prompt "A cozy cat sleeping near a window, soft morning light" \
  --out ./output/cat-responses.png
```

Use one or more reference images through `/v1/images/edits`:

```bash
python3 ./scripts/provider_imagegen.py reference \
  --image ./output/fixed-kitten.png \
  --prompt "Use the cat in this image as reference and generate a warm illustration of it eating an apple" \
  --out ./output/cat-reference.png
```

Use a reference image in `responses` mode:

```bash
python3 ./scripts/provider_imagegen.py responses \
  --image ./output/fixed-kitten.png \
  --prompt "Use this image as reference and generate a warm cat illustration" \
  --out ./output/cat-reference-responses.png
```

## Writing Prompts For Reference Images

When using reference images, say both what should stay the same and what should change. Avoid prompts like "use this image as reference" by itself; the provider may not know whether you care about the subject, composition, style, colors, or fine details.

Recommended structure:

```text
Use this image's {things to preserve} as reference, and generate {new scene}. Keep {subject/composition/style/colors/materials/expression}, change {parts to modify} into {target change}. Overall result: {style, mood, use case, aspect ratio}.
```

Common example:

```text
Use the cat subject, soft illustration style, and warm color palette from this image as reference. Generate an image of the cat eating a red apple. Keep the cat's visual identity and cozy mood, change the pose so it is holding the apple with both paws, keep the background simple and clean, square composition.
```

If you care more about style than the original subject:

```text
Use this image's lighting, brushwork, and color mood as reference. Do not preserve the original subject. Generate a warm illustration of a coffee cup beside a window, clean composition, soft natural light, suitable for a blog cover.
```

In Codex, you can write:

```text
Use $provider-image with output/reference.png as the reference image. Generate an image that preserves the subject shape and overall style, changes the scene to a nighttime desk setup, and saves it to output/imagegen/result.png.
```

## Use In Codex

Explicit invocation is the most reliable:

```text
Use $provider-image to generate an image: a cozy cat sleeping near a window, save it to output/imagegen/cat.png
```

Automatic skill triggering is not guaranteed, so mention `$provider-image` when you want this provider path.

## FAQ

### `Error: No bearer token found`

Check whether `~/.codex/auth.json` contains a usable `OPENAI_API_KEY`. If not, set `experimental_bearer_token` in `~/.codex/config.toml`.

### `4xx from /images/generations` or `4xx from /responses`

Confirm that the provider supports the endpoint, your token has image-generation permission, and `base_url` points to the API root, such as `/v1`.

If the response is `403` and contains `error code: 1010`, it is usually Cloudflare or provider-side policy blocking, not a broken skill install. The default `--transport auto` retries with the curl fallback. If curl also fails, run `inspect` or `diagnose`; if local config is correct, ask the provider administrator to allow image requests.

### `Python transport was blocked by provider/WAF; retrying with curl transport...`

This is the expected fallback path. It means the Python HTTP client was blocked by the provider/WAF, so the tool is retrying with `curl --http1.1` and browser-like headers. Use `--transport curl` to go directly through curl, or `--transport python` to disable fallback while debugging the old path.

### `urllib` fails but `httpx` works

Some providers or edge layers behave differently across HTTP clients. Installing `httpx` is recommended.

## Development

```bash
python3 -m py_compile scripts/provider_imagegen.py scripts/install.py
python3 -m unittest discover -s tests
```

## Project Layout

```text
provider-image/
├── agents/
├── assets/
├── references/
├── scripts/
│   ├── install.py
│   └── provider_imagegen.py
├── tests/
├── CONTRIBUTING.md
├── LICENSE
├── README.en.md
├── README.md
└── SKILL.md
```

## License

MIT License.
