# Security

## Supported Versions

The latest `main` branch is the supported version.

## Reporting a Vulnerability

Please open a private report if GitHub security advisories are enabled for the repository. Otherwise, open an issue with reproduction details but do not include real API keys, bearer tokens, provider URLs that should remain private, or generated private images.

## Provider and Token Safety

`provider-image` reads local Codex configuration and sends requests to the active provider `base_url`. Use this tool only when you intentionally want image requests to go through that configured provider.

Before running generation commands, verify:

- the active `model_provider` points to the provider you expect
- the provider `base_url` is trusted
- the token used by Codex is intended for that provider

Run this first when in doubt:

```bash
python3 ./scripts/provider_imagegen.py inspect
```

