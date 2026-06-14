---
name: provider-image
description: Generate or edit raster images through the OpenAI-compatible provider configured in ~/.codex/config.toml and ~/.codex/auth.json. Use when the user's intent is to create or edit an image, illustration, poster, cover, banner, product shot, concept art, avatar, icon mockup, wallpaper, social image, thumbnail, or other bitmap visual, and the environment should reuse the Codex-configured custom provider instead of the default built-in image path. Trigger especially on requests like "生成一张图", "帮我画", "做一张海报", "生成插画", "出一张封面图", "生成图片", "create an image", "generate an illustration", or "make a poster", especially when base_url comes from model_providers and auth may come from OPENAI_API_KEY or experimental_bearer_token.
---

# Provider Image

Use this skill when the active Codex environment already has an OpenAI-compatible image provider configured in `~/.codex/config.toml`, but normal image tooling does not automatically reuse that provider configuration.

Treat common image-intent wording as a strong trigger. Examples:

- `生成一张图`
- `帮我画一张插画`
- `做一张海报`
- `出一张封面图`
- `生成一个头像`
- `create an image`
- `generate a poster`
- `make an illustration`

## Quick Start

Run the bundled script:

```powershell
python scripts/provider_imagegen.py generate `
  --prompt "A small red paper airplane on a clean light background" `
  --out output\imagegen\paper-airplane.png
```

The script automatically:

- reads `~/.codex/config.toml`
- resolves the active `model_provider`
- uses that provider's `base_url`
- authenticates with `OPENAI_API_KEY` from `~/.codex/auth.json` when present
- falls back to `experimental_bearer_token` from `~/.codex/config.toml` when `OPENAI_API_KEY` is missing or null

## Workflow

1. Detect whether the user's intent is raster image generation or editing through the configured provider.
2. Use `scripts/provider_imagegen.py`.
3. Prefer `generate` for new images.
4. Prefer `responses` mode only when the user explicitly wants the Responses image tool path.
5. Save project-bound outputs inside the workspace and report the final file path.

## Commands

Generate through `/v1/images/generations`:

```powershell
python scripts/provider_imagegen.py generate `
  --prompt "A cozy cat sleeping near a window, soft morning light" `
  --size 1024x1024 `
  --quality low `
  --out output\imagegen\cat.png
```

Generate through `/v1/responses` with the `image_generation` tool:

```powershell
python scripts/provider_imagegen.py responses `
  --prompt "A cozy cat sleeping near a window, soft morning light" `
  --out output\imagegen\cat-responses.png
```

Dry-run the resolved provider configuration without calling the network:

```powershell
python scripts/provider_imagegen.py inspect
```

## Notes

- Default image model is `gpt-image-2`.
- Default Responses model comes from top-level `model` in `~/.codex/config.toml`.
- If the user needs direct background transparency and the provider supports only legacy transparent behavior, treat that as a separate capability check.
- If the provider returns a 4xx or 5xx, surface the status code and response body instead of silently retrying with different auth.

## Resources

- Script implementation: `scripts/provider_imagegen.py`
- Minimal usage reference: `references/usage.md`
