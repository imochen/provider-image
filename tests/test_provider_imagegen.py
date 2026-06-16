import base64
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "provider_imagegen.py"
SPEC = importlib.util.spec_from_file_location("provider_imagegen", SCRIPT)
provider_imagegen = importlib.util.module_from_spec(SPEC)
sys.modules["provider_imagegen"] = provider_imagegen
assert SPEC.loader is not None
SPEC.loader.exec_module(provider_imagegen)


class ProviderResolutionTests(unittest.TestCase):
    def test_resolves_provider_with_auth_json_key(self):
        resolved = provider_imagegen._resolve_provider(
            {
                "model_provider": "custom",
                "model": "gpt-5.4",
                "model_providers": {
                    "custom": {
                        "base_url": "https://provider.example/v1",
                    }
                },
            },
            {"OPENAI_API_KEY": " test-token "},
        )

        self.assertEqual(resolved["provider_name"], "custom")
        self.assertEqual(resolved["base_url"], "https://provider.example/v1")
        self.assertEqual(resolved["token"], "test-token")
        self.assertEqual(resolved["auth_source"], "auth.json:OPENAI_API_KEY")
        self.assertEqual(resolved["responses_model"], "gpt-5.4")

    def test_falls_back_to_config_token(self):
        resolved = provider_imagegen._resolve_provider(
            {
                "model_provider": "custom",
                "experimental_bearer_token": " config-token ",
                "model_providers": {
                    "custom": {
                        "base_url": "https://provider.example/v1/",
                    }
                },
            },
            {},
        )

        self.assertEqual(resolved["base_url"], "https://provider.example/v1")
        self.assertEqual(resolved["token"], "config-token")
        self.assertEqual(resolved["auth_source"], "config.toml:experimental_bearer_token")

    def test_missing_provider_exits(self):
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                provider_imagegen._resolve_provider(
                    {"model_provider": "missing", "model_providers": {}},
                    {"OPENAI_API_KEY": "token"},
                )


class ResponseParsingTests(unittest.TestCase):
    def test_extracts_image_generation_result(self):
        payload = {"output": [{"type": "image_generation_call", "result": "abc"}]}
        self.assertEqual(provider_imagegen._extract_b64_from_responses(payload), "abc")

    def test_extracts_nested_content_result(self):
        payload = {"output": [{"content": [{"b64_json": "nested"}]}]}
        self.assertEqual(provider_imagegen._extract_b64_from_responses(payload), "nested")


class TransportTests(unittest.TestCase):
    def test_detects_cloudflare_waf_block(self):
        self.assertTrue(
            provider_imagegen._is_provider_waf_block(
                403,
                "error code: 1010",
                {"Server": "cloudflare"},
            )
        )
        self.assertTrue(
            provider_imagegen._is_provider_waf_block(
                403,
                "Your request was blocked.",
                {},
            )
        )
        self.assertFalse(
            provider_imagegen._is_provider_waf_block(
                401,
                "invalid token",
                {"Server": "cloudflare"},
            )
        )

    def test_auto_transport_uses_curl_first(self):
        with mock.patch.object(
            provider_imagegen, "_request_json_curl", return_value={"ok": True}
        ) as curl_request:
            with mock.patch.object(provider_imagegen, "_request_json_python") as python_request:
                result = provider_imagegen._request_json(
                    "https://provider.example/v1",
                    "token",
                    "POST",
                    "/images/generations",
                    {"prompt": "cat"},
                )

        self.assertEqual(result, {"ok": True})
        curl_request.assert_called_once()
        python_request.assert_not_called()

    def test_auto_transport_falls_back_to_python_after_curl_block(self):
        curl_error = provider_imagegen.ProviderHTTPError(
            "/images/generations",
            403,
            "error code: 1010",
            {"transport": "curl"},
        )
        with mock.patch.object(
            provider_imagegen, "_request_json_curl", side_effect=curl_error
        ) as curl_request:
            with mock.patch.object(
                provider_imagegen, "_request_json_python", return_value={"ok": True}
            ) as python_request:
                with redirect_stderr(io.StringIO()) as stderr:
                    result = provider_imagegen._request_json(
                        "https://provider.example/v1",
                        "token",
                        "POST",
                        "/images/generations",
                        {"prompt": "cat"},
                    )

        self.assertEqual(result, {"ok": True})
        curl_request.assert_called_once()
        python_request.assert_called_once()
        self.assertIn("retrying with Python transport", stderr.getvalue())

    def test_auto_transport_falls_back_to_python_when_curl_missing(self):
        curl_error = provider_imagegen.ProviderTransportError("curl missing")
        with mock.patch.object(
            provider_imagegen, "_request_json_curl", side_effect=curl_error
        ) as curl_request:
            with mock.patch.object(
                provider_imagegen, "_request_json_python", return_value={"ok": True}
            ) as python_request:
                with redirect_stderr(io.StringIO()):
                    result = provider_imagegen._request_json(
                        "https://provider.example/v1",
                        "token",
                        "POST",
                        "/images/generations",
                        {"prompt": "cat"},
                    )

        self.assertEqual(result, {"ok": True})
        curl_request.assert_called_once()
        python_request.assert_called_once()

    def test_curl_transport_does_not_fallback(self):
        curl_error = provider_imagegen.ProviderHTTPError(
            "/images/generations",
            403,
            "error code: 1010",
            {"transport": "curl"},
        )
        with mock.patch.object(provider_imagegen, "_request_json_curl", side_effect=curl_error):
            with mock.patch.object(provider_imagegen, "_request_json_python") as python_request:
                with redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        provider_imagegen._request_json(
                            "https://provider.example/v1",
                            "token",
                            "POST",
                            "/images/generations",
                            {"prompt": "cat"},
                            transport="curl",
                        )

        python_request.assert_not_called()

    def test_auto_transport_reports_both_failures(self):
        curl_error = provider_imagegen.ProviderHTTPError(
            "/images/generations",
            403,
            "curl block",
            {"transport": "curl"},
        )
        python_error = provider_imagegen.ProviderHTTPError(
            "/images/generations",
            403,
            "error code: 1010",
            {"Server": "cloudflare"},
        )
        with mock.patch.object(provider_imagegen, "_request_json_curl", side_effect=curl_error):
            with mock.patch.object(
                provider_imagegen, "_request_json_python", side_effect=python_error
            ):
                with redirect_stderr(io.StringIO()) as stderr:
                    with self.assertRaises(SystemExit):
                        provider_imagegen._request_json(
                            "https://provider.example/v1",
                            "token",
                            "POST",
                            "/images/generations",
                            {"prompt": "cat"},
                        )

        self.assertIn("Python fallback also failed", stderr.getvalue())

    def test_python_transport_uses_only_python_path(self):
        with mock.patch.object(
            provider_imagegen, "_request_json_python", return_value={"ok": True}
        ) as python_request:
            with mock.patch.object(provider_imagegen, "_request_json_curl") as curl_request:
                result = provider_imagegen._request_json(
                    "https://provider.example/v1",
                    "token",
                    "POST",
                    "/images/generations",
                    {"prompt": "cat"},
                    transport="python",
                )

        self.assertEqual(result, {"ok": True})
        python_request.assert_called_once()
        curl_request.assert_not_called()

    def test_python_transport_does_not_fallback_to_curl(self):
        python_error = provider_imagegen.ProviderHTTPError(
            "/images/generations",
            403,
            "error code: 1010",
            {"Server": "cloudflare"},
        )
        with mock.patch.object(
            provider_imagegen, "_request_json_python", side_effect=python_error
        ):
            with mock.patch.object(provider_imagegen, "_request_json_curl") as curl_request:
                with redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        provider_imagegen._request_json(
                            "https://provider.example/v1",
                            "token",
                            "POST",
                            "/images/generations",
                            {"prompt": "cat"},
                            transport="python",
                        )

        curl_request.assert_not_called()

    def test_curl_transport_keeps_token_out_of_process_arguments(self):
        class CurlResult:
            returncode = 0
            stdout = "200"
            stderr = ""

        def fake_run(args, **_kwargs):
            self.assertNotIn("secret-token", " ".join(args))
            config_path = Path(args[-1])
            config_text = config_path.read_text(encoding="utf-8")
            self.assertIn("Authorization: Bearer secret-token", config_text)
            output_line = next(
                line for line in config_text.splitlines() if line.startswith("output = ")
            )
            body_path = Path(output_line.split('"', 2)[1])
            body_path.write_text(json.dumps({"ok": True}), encoding="utf-8")
            return CurlResult()

        with mock.patch.object(provider_imagegen.shutil, "which", return_value="/usr/bin/curl"):
            with mock.patch.object(provider_imagegen.subprocess, "run", side_effect=fake_run):
                result = provider_imagegen._request_json_curl(
                    "https://provider.example/v1",
                    "secret-token",
                    "POST",
                    "/images/generations",
                    {"prompt": "cat"},
                )

        self.assertEqual(result, {"ok": True})

    def test_reference_curl_transport_uses_multipart_without_json_content_type(self):
        class CurlResult:
            returncode = 0
            stdout = "200"
            stderr = ""

        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "cat.png"
            image_path.write_bytes(b"image")

            def fake_run(args, **_kwargs):
                self.assertNotIn("secret-token", " ".join(args))
                config_path = Path(args[-1])
                config_text = config_path.read_text(encoding="utf-8")
                self.assertIn("Authorization: Bearer secret-token", config_text)
                self.assertNotIn("Content-Type: application/json", config_text)
                self.assertIn('form-string = "prompt=cat \\"hero\\" = warm"', config_text)
                self.assertIn("form = \"image[]=@", config_text)
                output_line = next(
                    line for line in config_text.splitlines() if line.startswith("output = ")
                )
                body_path = Path(output_line.split('"', 2)[1])
                body_path.write_text(json.dumps({"ok": True}), encoding="utf-8")
                return CurlResult()

            with mock.patch.object(provider_imagegen.shutil, "which", return_value="/usr/bin/curl"):
                with mock.patch.object(provider_imagegen.subprocess, "run", side_effect=fake_run):
                    result = provider_imagegen._request_multipart_curl(
                        "https://provider.example/v1",
                        "secret-token",
                        "/images/edits",
                        {"prompt": 'cat "hero" = warm'},
                        [image_path],
                    )

        self.assertEqual(result, {"ok": True})

    def test_reference_auto_transport_falls_back_to_python_after_curl_failure(self):
        curl_error = provider_imagegen.ProviderHTTPError(
            "/images/edits",
            403,
            "curl block",
            {"transport": "curl"},
        )
        with mock.patch.object(
            provider_imagegen, "_request_multipart_curl", side_effect=curl_error
        ) as curl_request:
            with mock.patch.object(
                provider_imagegen, "_request_multipart_httpx", return_value={"ok": True}
            ) as python_request:
                with redirect_stderr(io.StringIO()):
                    result = provider_imagegen._request_multipart(
                        "https://provider.example/v1",
                        "token",
                        "/images/edits",
                        {"prompt": "cat"},
                        [Path("cat.png")],
                    )

        self.assertEqual(result, {"ok": True})
        curl_request.assert_called_once()
        python_request.assert_called_once()


class FileWriteTests(unittest.TestCase):
    def test_write_image_refuses_existing_file_without_force(self):
        image_b64 = base64.b64encode(b"image").decode("ascii")
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "image.png"
            output.write_bytes(b"old")

            with redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    provider_imagegen._write_image(output, image_b64, force=False)

            self.assertEqual(output.read_bytes(), b"old")

    def test_write_image_allows_force(self):
        image_b64 = base64.b64encode(b"image").decode("ascii")
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "image.png"
            output.write_bytes(b"old")

            with redirect_stdout(io.StringIO()):
                provider_imagegen._write_image(output, image_b64, force=True)

            self.assertEqual(output.read_bytes(), b"image")


if __name__ == "__main__":
    unittest.main()
