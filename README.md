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

`Provider Image` 是一个给 Codex 使用的本地 skill 和命令行脚本。它会读取本机已有的 Codex provider 配置，把图片生成请求发送到你当前选中的 OpenAI-compatible provider。

适合你已经明确要使用自定义 Provider 生成图片的场景。如果你希望使用 Codex 默认内置图片能力，或者不确定当前 provider 是否可信，请不要启用这个工具；先运行 `inspect` 确认配置。

### 特性

- 自动读取 `~/.codex/config.toml` 中的 `model_provider`
- 自动使用对应 provider 的 `base_url`
- 复用 Codex 本地鉴权配置
- 支持 `/v1/images/generations`
- 支持 `/v1/images/edits` 参考图模式
- 支持 `/v1/responses` + `image_generation`
- 优先使用 `httpx`，缺失时普通 JSON 请求会回退到 Python 标准库
- 可作为普通脚本运行，也可安装成 Codex skill

### 安装

最省事的方式：复制下面这句话交给 Codex，让它自动安装本 skill：

```text
请从 https://github.com/imochen/provider-image 安装 Provider Image 这个 Codex skill，安装到 ~/.codex/skills/provider-image；安装后运行 inspect 检查配置，但不要替我发起图片生成请求。
```

克隆仓库后，可以直接作为脚本使用：

```bash
python3 ./scripts/provider_imagegen.py inspect
```

也可以安装成 Codex skill：

```bash
python3 ./scripts/install.py
```

安装后会复制到：

```text
~/.codex/skills/provider-image
```

然后重启 Codex。

Windows PowerShell 对应命令：

```powershell
python .\scripts\provider_imagegen.py inspect
python .\scripts\install.py
```

### 依赖

推荐使用 Python 3.11 或更高版本：

```bash
python3 -m pip install -r requirements.txt
```

如果不使用 `requirements.txt`，至少建议安装：

```bash
python3 -m pip install httpx
```

Python 3.10 及更低版本还需要 `tomli`。

### Codex 配置

你的 `~/.codex/config.toml` 至少应包含：

```toml
model_provider = "custom"
model = "gpt-5.4"

[model_providers.custom]
base_url = "https://your-provider.example/v1"
wire_api = "responses"
```

如果 `~/.codex/auth.json` 中没有可用的 `OPENAI_API_KEY`，请在 `config.toml` 中提供：

```toml
experimental_bearer_token = "your-provider-token"
```

### 安全提示

这个工具会把图片请求发送到当前 Codex 配置解析出的 `base_url`。请只在你确认要使用该自定义 Provider 时使用它。

运行生成命令前，建议先检查：

```bash
python3 ./scripts/provider_imagegen.py inspect
```

确认输出里的 `provider_name`、`base_url` 和 `auth_source` 都符合预期后，再继续生成图片。

### 命令行用法

检查当前解析到的 provider：

```bash
python3 ./scripts/provider_imagegen.py inspect
```

快速诊断本地配置和常见 provider 拦截问题：

```bash
python3 ./scripts/provider_imagegen.py diagnose
```

通过 `/v1/images/generations` 生成图片：

```bash
python3 ./scripts/provider_imagegen.py generate \
  --prompt "一只可爱的小猫咪正在吃苹果，温馨治愈风格，柔和自然光，背景简洁干净" \
  --out ./output/kitten.png
```

通过 `/v1/responses` 的 `image_generation` 工具生成图片：

```bash
python3 ./scripts/provider_imagegen.py responses \
  --prompt "一只可爱的小猫咪正在吃苹果，温馨治愈风格，柔和自然光，背景简洁干净" \
  --out ./output/kitten-responses.png
```

使用参考图，通过 `/v1/images/edits` 生成新图：

```bash
python3 ./scripts/provider_imagegen.py reference \
  --image ./output/fixed-kitten.png \
  --prompt "参考这张图的小猫主体和整体风格，让它改成正在吃一个红苹果，画面更温馨治愈" \
  --out ./output/kitten-reference.png
```

在 `responses` 模式中传入参考图：

```bash
python3 ./scripts/provider_imagegen.py responses \
  --image ./output/fixed-kitten.png \
  --prompt "参考这张图，生成一张小猫正在吃苹果的温馨插画" \
  --out ./output/kitten-reference-responses.png
```

### 参考图提示词怎么写

使用参考图时，提示词最好同时说明“哪些要保留”和“哪些要改变”。不要只写“参考这张图生成一张图”，否则 provider 可能不知道你重视的是主体、构图、风格、配色还是细节。

推荐结构：

```text
参考这张图的{要保留的内容}，生成{新画面}。请保留{主体/构图/风格/配色/材质/表情}，将{需要改变的部分}改成{目标变化}。整体效果：{风格、氛围、用途、画幅}。
```

常用写法：

```text
参考这张图的小猫主体、柔和插画风格和温暖配色，生成一张小猫正在吃红苹果的图片。请保留小猫的外形特征和治愈氛围，把动作改成双爪抱着苹果，背景保持简洁干净，正方形构图。
```

如果你更在意风格而不是主体：

```text
参考这张图的光影、笔触和色彩氛围，不需要保留原图主体。生成一张咖啡杯放在窗边的温暖插画，画面干净，柔和自然光，适合作为博客封面。
```

如果你要在 Codex 中调用，可以这样写：

```text
使用 $provider-image，参考 output/reference.png，生成一张图：参考图里的主体外形和整体风格要保留，把场景改成夜晚书桌前，保存到 output/imagegen/result.png
```

Windows PowerShell 中可使用反引号换行：

```powershell
python .\scripts\provider_imagegen.py generate `
  --prompt "A warm tea cup illustration" `
  --out .\output\tea.png
```

### 在 Codex 中触发

最稳妥的方式是显式写出 skill 名：

```text
使用 $provider-image 生成一张图：一只可爱的小猫咪正在吃苹果，保存到 output/imagegen/kitten.png
```

如果要明确走 Responses 图片工具链路：

```text
使用 $provider-image，通过 Responses 的 image_generation 工具生成一张图：一只可爱的小猫咪正在吃苹果，保存到 output/imagegen/kitten-responses.png
```

自动触发不是强保证机制。想稳定触发，建议始终显式写出 `$provider-image`。

### 常见问题

#### `Error: No bearer token found`

检查 `~/.codex/auth.json` 是否包含可用的 `OPENAI_API_KEY`。如果没有，请在 `~/.codex/config.toml` 中设置 `experimental_bearer_token`。

#### `4xx from /images/generations` 或 `4xx from /responses`

确认 provider 支持对应接口、当前 token 具备图片生成权限，并且 `base_url` 指向 API 根路径，例如 `/v1`。

如果报 `403` 且包含 `error code: 1010`，通常是 Cloudflare 或 provider 侧策略拦截，不是 skill 安装失败。先运行 `inspect` 或 `diagnose`；如果本地配置正常，应联系 provider 管理员放行图片请求。

#### `urllib` 路径失败但 `httpx` 路径可用

某些 provider 或边缘层会对不同 HTTP 客户端表现不同。建议安装并使用 `httpx`。

### 开发

运行基础检查：

```bash
python3 -m py_compile scripts/provider_imagegen.py scripts/install.py
python3 -m unittest discover -s tests
```

### 仓库结构

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

### License

MIT License.
