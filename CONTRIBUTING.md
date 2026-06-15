# Contributing

Thanks for helping improve `provider-image`.

## Development

This project intentionally stays small and script-first. Before opening a pull request:

```bash
python3 -m py_compile scripts/provider_imagegen.py scripts/install.py
python3 -m unittest discover -s tests
```

If you use Python 3.10 or older, install `tomli` for TOML parsing. `httpx` is recommended for real provider calls and required for reference-image mode.

## Pull Requests

- Keep changes focused on one behavior or documentation topic.
- Do not include real API keys, provider tokens, personal `~/.codex` files, or generated output images.
- Document provider-specific behavior when adding compatibility workarounds.
- Prefer standard-library tests unless a dependency is necessary.

