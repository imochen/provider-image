#!/usr/bin/env python3
"""
Generate images through the OpenAI-compatible provider configured for Codex.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import importlib.util
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Tuple


def _die(message: str, code: int = 1) -> None:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(code)


def _format_http_error(path: str, status: int, body: str, headers: Dict[str, str]) -> str:
    text = (body or "").strip()
    server = headers.get("Server", "")
    if status == 403 and ("1010" in text or server.lower() == "cloudflare"):
        return (
            f"{status} from {path}: provider-side request blocked"
            f" (Cloudflare/provider policy). Response body: {text or '<empty>'}. "
            "The skill configuration is likely valid if `inspect` works. "
            "Ask the provider administrator to allow image requests for this base_url, token, and client."
        )
    return f"{status} from {path}: {text}"


def _load_toml(path: Path) -> Dict[str, Any]:
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore
    try:
        with path.open("rb") as fh:
            return tomllib.load(fh)
    except FileNotFoundError:
        _die(f"Config not found: {path}")
    except Exception as exc:
        _die(f"Failed to parse TOML {path}: {exc}")
    return {}


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except Exception as exc:
        _die(f"Failed to parse JSON {path}: {exc}")
    return {}


def _resolve_paths() -> Tuple[Path, Path]:
    codex_home = Path.home() / ".codex"
    return codex_home / "config.toml", codex_home / "auth.json"


def _resolve_provider(config: Dict[str, Any], auth: Dict[str, Any]) -> Dict[str, Any]:
    provider_name = config.get("model_provider")
    providers = config.get("model_providers") or {}
    if not provider_name:
        _die("config.toml is missing top-level model_provider")
    provider = providers.get(provider_name)
    if not isinstance(provider, dict):
        _die(f"config.toml is missing [model_providers.{provider_name}]")

    base_url = provider.get("base_url")
    if not base_url:
        _die(f"Provider {provider_name} is missing base_url")

    auth_key = auth.get("OPENAI_API_KEY")
    token = auth_key if isinstance(auth_key, str) and auth_key.strip() else None
    auth_source = "auth.json:OPENAI_API_KEY"
    if not token:
        token = config.get("experimental_bearer_token") or provider.get("experimental_bearer_token")
        auth_source = "config.toml:experimental_bearer_token"
    if not isinstance(token, str) or not token.strip():
        _die(
            "No bearer token found. Expected OPENAI_API_KEY in ~/.codex/auth.json or "
            "experimental_bearer_token in ~/.codex/config.toml."
        )

    return {
        "provider_name": provider_name,
        "provider": provider,
        "base_url": str(base_url).rstrip("/"),
        "token": token.strip(),
        "auth_source": auth_source,
        "responses_model": config.get("model") or "gpt-5.4",
    }


def _write_image(output_path: Path, image_b64: str, *, force: bool) -> None:
    if output_path.exists() and not force:
        _die(f"Output already exists: {output_path} (use --force to overwrite)")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(base64.b64decode(image_b64))
    print(output_path)


def _extract_b64_from_responses(payload: Dict[str, Any]) -> str:
    for item in payload.get("output", []):
        if item.get("type") == "image_generation_call":
            result = item.get("result")
            if isinstance(result, str) and result.strip():
                return result
        for content in item.get("content", []) or []:
            for key in ("b64_json", "image_base64", "result"):
                value = content.get(key)
                if isinstance(value, str) and value.strip():
                    return value
    _die("Responses payload did not include image data.")
    return ""


def _request_json(base_url: str, token: str, method: str, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if importlib.util.find_spec("httpx") is not None:
        return _request_json_httpx(base_url, token, method, path, payload)
    return _request_json_urllib(base_url, token, method, path, payload)


def _request_json_httpx(
    base_url: str, token: str, method: str, path: str, payload: Dict[str, Any]
) -> Dict[str, Any]:
    import httpx

    url = f"{base_url}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    try:
        with httpx.Client(timeout=180.0) as client:
            response = client.request(method, url, headers=headers, json=payload)
    except httpx.HTTPError as exc:
        _die(f"Network error while calling {path}: {exc}")

    if response.status_code >= 400:
        _die(_format_http_error(path, response.status_code, response.text, dict(response.headers)))
    try:
        return response.json()
    except Exception as exc:
        _die(f"Failed to decode JSON from {path}: {exc}")
    return {}


def _request_json_urllib(
    base_url: str, token: str, method: str, path: str, payload: Dict[str, Any]
) -> Dict[str, Any]:
    url = f"{base_url}{path}"
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        try:
            error_body = exc.read().decode("utf-8", errors="replace").strip()
        except Exception:
            error_body = str(exc)
        _die(_format_http_error(path, exc.code, error_body, dict(exc.headers)))
    except urllib.error.URLError as exc:
        _die(f"Network error while calling {path}: {exc}")
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception as exc:
        _die(f"Failed to decode JSON from {path}: {exc}")
    return {}


def _cmd_inspect(_: argparse.Namespace, resolved: Dict[str, Any]) -> int:
    print(f"provider_name={resolved['provider_name']}")
    print(f"base_url={resolved['base_url']}")
    print(f"auth_source={resolved['auth_source']}")
    print(f"responses_model={resolved['responses_model']}")
    print("image_model=gpt-image-2")
    return 0


def _cmd_diagnose(_: argparse.Namespace, resolved: Dict[str, Any]) -> int:
    print(f"provider_name={resolved['provider_name']}")
    print(f"base_url={resolved['base_url']}")
    print(f"auth_source={resolved['auth_source']}")
    print(f"responses_model={resolved['responses_model']}")
    print("image_model=gpt-image-2")
    print("diagnose_status=inspect_ok")
    print("next_step=try_generate_or_responses")
    print(
        "if_generate_returns_403_1010=provider_side_block_not_skill_install_problem"
    )
    return 0


def _cmd_generate(args: argparse.Namespace, resolved: Dict[str, Any]) -> int:
    payload = {
        "model": args.model,
        "prompt": args.prompt,
        "size": args.size,
        "quality": args.quality,
    }
    if args.background:
        payload["background"] = args.background
    if args.output_format:
        payload["output_format"] = args.output_format

    data = _request_json(
        resolved["base_url"],
        resolved["token"],
        "POST",
        "/images/generations",
        payload,
    )
    try:
        image_b64 = data["data"][0]["b64_json"]
    except Exception as exc:
        _die(f"Unexpected /images/generations response shape: {exc}")
    _write_image(Path(args.out), image_b64, force=args.force)
    return 0


def _cmd_responses(args: argparse.Namespace, resolved: Dict[str, Any]) -> int:
    payload = {
        "model": args.responses_model or resolved["responses_model"],
        "input": args.prompt,
        "tools": [{"type": "image_generation"}],
    }
    data = _request_json(
        resolved["base_url"],
        resolved["token"],
        "POST",
        "/responses",
        payload,
    )
    image_b64 = _extract_b64_from_responses(data)
    _write_image(Path(args.out), image_b64, force=args.force)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate images through the Codex-configured custom provider."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect resolved provider config")
    inspect_parser.set_defaults(handler=_cmd_inspect)

    diagnose_parser = subparsers.add_parser(
        "diagnose",
        help="Explain whether failures are likely local config issues or provider-side blocking",
    )
    diagnose_parser.set_defaults(handler=_cmd_diagnose)

    gen_parser = subparsers.add_parser("generate", help="Call /v1/images/generations")
    gen_parser.add_argument("--prompt", required=True)
    gen_parser.add_argument("--out", required=True)
    gen_parser.add_argument("--model", default="gpt-image-2")
    gen_parser.add_argument("--size", default="1024x1024")
    gen_parser.add_argument("--quality", default="low")
    gen_parser.add_argument("--background")
    gen_parser.add_argument("--output-format")
    gen_parser.add_argument("--force", action="store_true")
    gen_parser.set_defaults(handler=_cmd_generate)

    resp_parser = subparsers.add_parser(
        "responses", help="Call /v1/responses with the image_generation tool"
    )
    resp_parser.add_argument("--prompt", required=True)
    resp_parser.add_argument("--out", required=True)
    resp_parser.add_argument("--responses-model")
    resp_parser.add_argument("--force", action="store_true")
    resp_parser.set_defaults(handler=_cmd_responses)

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    config_path, auth_path = _resolve_paths()
    config = _load_toml(config_path)
    auth = _load_json(auth_path)
    resolved = _resolve_provider(config, auth)

    return int(args.handler(args, resolved))


if __name__ == "__main__":
    raise SystemExit(main())
