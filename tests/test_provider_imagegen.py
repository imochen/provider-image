import base64
import importlib.util
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


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
