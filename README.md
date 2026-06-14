# provider-image

`provider-image` 是一个给 Codex 用的本地 skill，用来通过你已经配置好的自定义 provider 生图。

它会自动复用：

- `~/.codex/config.toml`
- `~/.codex/auth.json`

适合这些情况：

- 你已经在 Codex 里配置了 OpenAI 兼容 provider
- 这个 provider 支持图片生成
- 你希望生成图片时直接复用 Codex 现有配置，而不是另外单独维护一套 API 参数

## 特性

- 自动读取当前 `model_provider`
- 自动读取对应 provider 的 `base_url`
- 优先使用 `~/.codex/auth.json` 里的 `OPENAI_API_KEY`
- 如果 `OPENAI_API_KEY` 不可用，自动回退到 `config.toml` 里的 `experimental_bearer_token`
- 支持 `/v1/images/generations`
- 支持 `/v1/responses` + `image_generation`
- 默认仅依赖 Python 标准库

## 1 分钟安装

### 方式一：直接作为本地脚本使用

克隆或下载仓库后，直接执行：

Windows PowerShell:

```powershell
python .\scripts\provider_imagegen.py inspect
```

macOS / Linux:

```bash
python3 ./scripts/provider_imagegen.py inspect
```

### 方式二：安装成 Codex skill

在仓库目录下执行：

Windows PowerShell:

```powershell
python .\scripts\install.py
```

macOS / Linux:

```bash
python3 ./scripts/install.py
```

它会自动安装到：

```text
~/.codex/skills/provider-image
```

安装完成后重启 Codex。

## 依赖要求

- 推荐 Python 3.11 或更高版本
- Python 3.11+：通常不需要额外安装依赖
- Python 3.10 及更低版本：需要安装 `tomli`

如果你的 Python 版本较低，再执行：

Windows PowerShell:

```powershell
python -m pip install tomli
```

macOS / Linux:

```bash
python3 -m pip install tomli
```

## 期望的 Codex 配置

你的 `~/.codex/config.toml` 至少应包含：

```toml
model_provider = "newapi"
model = "gpt-5.4"

[model_providers.newapi]
base_url = "https://your-provider.example/v1"
wire_api = "responses"
```

如果 `~/.codex/auth.json` 中没有可用的 `OPENAI_API_KEY`，请在 `config.toml` 中提供：

```toml
experimental_bearer_token = "your-provider-token"
```

## 命令行用法

查看当前会解析到哪个 provider 和鉴权来源：

Windows PowerShell:

```powershell
python .\scripts\provider_imagegen.py inspect
```

macOS / Linux:

```bash
python3 ./scripts/provider_imagegen.py inspect
```

通过 `/v1/images/generations` 生图：

Windows PowerShell:

```powershell
python .\scripts\provider_imagegen.py generate `
  --prompt "一只可爱的小猫咪正在吃苹果，温馨治愈风格，柔和自然光，背景简洁干净" `
  --out .\output\kitten.png
```

macOS / Linux:

```bash
python3 ./scripts/provider_imagegen.py generate \
  --prompt "一只可爱的小猫咪正在吃苹果，温馨治愈风格，柔和自然光，背景简洁干净" \
  --out ./output/kitten.png
```

通过 `/v1/responses` 的 `image_generation` 工具生图：

Windows PowerShell:

```powershell
python .\scripts\provider_imagegen.py responses `
  --prompt "一只可爱的小猫咪正在吃苹果，温馨治愈风格，柔和自然光，背景简洁干净" `
  --out .\output\kitten-responses.png
```

macOS / Linux:

```bash
python3 ./scripts/provider_imagegen.py responses \
  --prompt "一只可爱的小猫咪正在吃苹果，温馨治愈风格，柔和自然光，背景简洁干净" \
  --out ./output/kitten-responses.png
```

## 安装后如何在 Codex 中触发

最稳妥的方式是显式写出 skill 名：

```text
使用 $provider-image 生成一张图：一只可爱的小猫咪正在吃苹果，保存到 output/imagegen/kitten.png
```

如果你想明确要求走 `/responses` 的图片工具链路：

```text
使用 $provider-image，通过 Responses 的 image_generation 工具生成一张图：一只可爱的小猫咪正在吃苹果，保存到 output/imagegen/kitten-responses.png
```

如果你想先检查当前 provider 再生成图片：

```text
使用 $provider-image，先检查当前 Codex provider 配置，然后生成一张温馨治愈风格的小猫插画
```

## 自动触发说明

这个 skill 已经针对常见图片意图做了触发优化，下面这类表达更容易命中：

- `生成一张图`
- `帮我画一张插画`
- `做一张海报`
- `生成一个头像`
- `create an image`
- `generate a poster`

但自动触发不是强保证机制。想稳定触发，建议始终显式写出：

```text
$provider-image
```

## 常用提示词模板

最推荐的写法：

```text
使用 $provider-image，生成一张图：{你的提示词}，保存到 {你的输出路径}
```

例如：

```text
使用 $provider-image，生成一张图：一只可爱的小猫咪正在吃苹果，温馨治愈风格，柔和自然光，细节丰富，背景干净，保存到 output/imagegen/cat-apple.png
```

## 常见问题

`Error: No bearer token found`

- 检查 `~/.codex/auth.json`
- 如果 `OPENAI_API_KEY` 是 `null` 或不存在，请在 `~/.codex/config.toml` 中设置 `experimental_bearer_token`

`4xx from /images/generations` 或 `4xx from /responses`

- 确认 provider 真的支持这个接口
- 确认当前 token 具备图片生成权限
- 确认 `base_url` 指向的是 API 根路径，例如 `/v1`

`No module named tomli`

- 你的 Python 版本较低
- Windows: 运行 `python -m pip install tomli`
- macOS / Linux: 运行 `python3 -m pip install tomli`

## 仓库结构

```text
provider-image/
├── agents/
├── references/
├── scripts/
│   ├── install.py
│   └── provider_imagegen.py
├── README.md
└── SKILL.md
```
