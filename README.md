<p align="center">
  <img src="assets/provider-image.svg" width="96" height="96" alt="Provider Image logo">
</p>

<h1 align="center">Provider Image</h1>

<p align="center">
  让 Codex 通过你已经配置好的 OpenAI-compatible 自定义 Provider 生成图片。
</p>

<p align="center">
  中文 · <a href="README.en.md">English</a>
</p>

<p align="center">
  <img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-0f766e.svg">
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-2563eb.svg">
  <img alt="Codex Skill" src="https://img.shields.io/badge/Codex-skill-7c3aed.svg">
</p>

`Provider Image` 是一个 Codex skill 和命令行脚本。它读取本机 `~/.codex/config.toml` 中已经配置好的自定义 Provider，把图片生成请求发送到该 OpenAI-compatible provider。

请只在你明确希望使用自定义 Provider 生成图片时使用本工具。如果你想用 Codex 默认内置图片能力，或不确定当前 provider 是否可信，请先不要启用。

## 支持能力

- 自动读取 Codex 当前 `model_provider`、`base_url` 和鉴权信息
- 支持 `/v1/images/generations` 文生图
- 支持 `/v1/images/edits` 参考图生成
- 支持 `/v1/responses` + `image_generation`
- 默认优先使用 `curl --http1.1` 和浏览器风格请求头，兼容部分 Cloudflare/WAF provider
- 支持 Python transport 兜底：JSON 使用 `httpx` 或 `urllib`，参考图模式使用 `httpx`
- 可作为 Codex skill 使用，也可直接作为 CLI 脚本运行

## 快速安装

最省事的方式：复制下面这句话交给 Codex：

```text
请从 https://github.com/imochen/provider-image 安装 Provider Image 这个 Codex skill，安装到 ~/.codex/skills/provider-image；安装后运行 inspect 检查配置，但不要替我发起图片生成请求。
```

手动安装：

```bash
git clone https://github.com/imochen/provider-image.git
cd provider-image
python3 -m pip install -r requirements.txt
python3 ./scripts/install.py
```

安装后重启 Codex。你也可以不安装 skill，直接运行脚本：

```bash
python3 ./scripts/provider_imagegen.py inspect
```

Windows PowerShell：

```powershell
python .\scripts\provider_imagegen.py inspect
python .\scripts\install.py
```

Python 3.11+ 推荐。Python 3.10 及更低版本需要额外安装 `tomli`。

## Codex 配置

你的 `~/.codex/config.toml` 至少应包含一个 OpenAI-compatible provider：

```toml
model_provider = "custom"
model = "gpt-5.4"

[model_providers.custom]
base_url = "https://your-provider.example/v1"
wire_api = "responses"
```

如果 `~/.codex/auth.json` 中没有可用的 `OPENAI_API_KEY`，请在 `config.toml` 中提供 token：

```toml
experimental_bearer_token = "your-provider-token"
```

生成前建议先确认实际解析到的 provider：

```bash
python3 ./scripts/provider_imagegen.py inspect
```

确认 `provider_name`、`base_url`、`auth_source` 都符合预期后，再继续生成图片。

## 常用命令

### 文生图

```bash
python3 ./scripts/provider_imagegen.py generate \
  --prompt "一只可爱的小猫咪正在吃苹果，温馨治愈风格，柔和自然光，背景简洁干净" \
  --out ./output/kitten.png
```

常用参数：

```bash
python3 ./scripts/provider_imagegen.py generate \
  --size 1024x1024 \
  --quality high \
  --prompt "A warm tea cup illustration" \
  --out ./output/tea.png
```

### 参考图生成

```bash
python3 ./scripts/provider_imagegen.py reference \
  --image ./output/reference.png \
  --prompt "参考这张图的小猫主体和整体风格，让它改成正在吃一个红苹果，背景保持简洁干净" \
  --out ./output/kitten-reference.png
```

参考图提示词建议同时说明“保留什么”和“改变什么”：

```text
参考这张图的{要保留的内容}，生成{新画面}。请保留{主体/构图/风格/配色/材质/表情}，将{需要改变的部分}改成{目标变化}。整体效果：{风格、氛围、用途、画幅}。
```

### Responses 图片工具

```bash
python3 ./scripts/provider_imagegen.py responses \
  --prompt "一只可爱的小猫咪正在吃苹果，温馨治愈风格，柔和自然光，背景简洁干净" \
  --out ./output/kitten-responses.png
```

也可以在 `responses` 模式中传入参考图：

```bash
python3 ./scripts/provider_imagegen.py responses \
  --image ./output/reference.png \
  --prompt "参考这张图，生成一张小猫正在吃苹果的温馨插画" \
  --out ./output/kitten-reference-responses.png
```

### Transport

默认 `--transport auto` 会先走 `curl --http1.1`，失败时再尝试 Python transport。

```bash
python3 ./scripts/provider_imagegen.py generate \
  --transport curl \
  --prompt "A warm tea cup illustration" \
  --out ./output/tea-curl.png
```

调试旧路径时可以只走 Python：

```bash
python3 ./scripts/provider_imagegen.py generate \
  --transport python \
  --prompt "A warm tea cup illustration" \
  --out ./output/tea-python.png
```

## 在 Codex 中使用

最稳定的方式是显式写出 skill 名：

```text
使用 $provider-image 生成一张图：一只可爱的小猫咪正在吃苹果，保存到 output/imagegen/kitten.png
```

使用参考图：

```text
使用 $provider-image，参考 output/reference.png，生成一张图：保留参考图里的主体外形和整体风格，把场景改成夜晚书桌前，保存到 output/imagegen/result.png
```

自动触发不是强保证机制；想稳定触发时，请明确写出 `$provider-image`。

## 故障排查

### `Error: No bearer token found`

检查 `~/.codex/auth.json` 是否包含可用的 `OPENAI_API_KEY`。如果没有，请在 `~/.codex/config.toml` 中设置 `experimental_bearer_token`。

### `4xx from /images/generations` 或 `4xx from /responses`

确认 provider 支持对应接口、当前 token 具备图片生成权限，并且 `base_url` 指向 API 根路径，例如 `/v1`。

如果报 `403` 且包含 `error code: 1010`，通常是 Cloudflare 或 provider 侧策略拦截，不是 skill 安装失败。默认 `--transport auto` 会先使用 curl；如果 curl 和 Python fallback 都失败，先运行：

```bash
python3 ./scripts/provider_imagegen.py diagnose
```

如果本地配置正常，应联系 provider 管理员放行图片请求。

### `Curl transport failed; retrying with Python transport...`

这是预期 fallback。说明 curl transport 没有成功，工具正在尝试 Python transport。可用 `--transport curl` 只走 curl，或用 `--transport python` 只走 Python 路径排查。

## 开发

```bash
python3 -m py_compile scripts/provider_imagegen.py scripts/install.py
python3 -m unittest discover -s tests
```

## License

MIT License.
