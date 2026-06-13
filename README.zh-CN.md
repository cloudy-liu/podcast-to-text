# Podcast To Text

[English](README.md) | [中文](README.zh-CN.md)

`podcast-to-text` 是一个本地命令行工具，可以把小宇宙单集链接或 YouTube
视频链接转成带时间戳的字幕文件。

它面向可审校的逐字稿工作流：

- 接收一个小宇宙单集 URL 或 YouTube URL。
- 生成 `source.srt`，作为源语言字幕产物。
- YouTube 优先使用平台已有字幕，再考虑语音识别。
- 没有可用平台字幕时，回退到本地 `faster-whisper` ASR。
- 在 `metadata.json` 中记录字幕来源、是否使用 ASR、字幕语言等 provenance。
- 需要最终中文字幕时，通过内置 agent skill 生成 `transcript.zh.srt`。

CLI 本身不包含大模型 API 客户端。英文到中文的翻译、中文轻校正由 Codex 或
Claude Code 等 agent runtime 使用 `skills/chinese-srt-adaptation/` 完成。

## 快速开始

### 1. 准备环境

要求：

- Python 3.10 或更新版本。
- 可以访问小宇宙 / YouTube 的网络环境。
- 如果使用 `--limit-seconds` 生成短音频样本，需要安装 `ffmpeg`。

创建虚拟环境：

```powershell
python -m venv .venv
```

在 Windows PowerShell 中激活：

```powershell
.\.venv\Scripts\Activate.ps1
```

在 macOS 或 Linux 中激活：

```bash
source .venv/bin/activate
```

安装项目：

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

### 2. 转录 YouTube 视频

```powershell
python -m podcast_to_text.cli `
  "https://www.youtube.com/watch?v=jNQXAC9IVRw" `
  --out-dir out-youtube `
  --model small `
  --device cpu `
  --compute-type int8
```

YouTube 会优先抓取平台字幕。如果没有可下载的支持字幕，CLI 会下载音频并走本地
ASR。

### 3. 转录小宇宙单集

```powershell
python -m podcast_to_text.cli `
  "https://www.xiaoyuzhoufm.com/episode/69b4d2f9f8b8079bfa3ae7f2" `
  --out-dir out-xiaoyuzhou `
  --model small `
  --device cpu `
  --compute-type int8
```

快速冒烟测试可以只处理前 45 秒：

```powershell
python -m podcast_to_text.cli `
  "https://www.xiaoyuzhoufm.com/episode/69b4d2f9f8b8079bfa3ae7f2" `
  --out-dir out-sample `
  --model small `
  --device cpu `
  --compute-type int8 `
  --limit-seconds 45
```

### 4. 生成中文字幕产物

CLI 到 `source.srt` 为止。需要 `transcript.zh.srt` 时，使用项目内置 skill：

```text
Use skills/chinese-srt-adaptation to convert <output-dir>/source.srt to
<output-dir>/transcript.zh.srt, then run the alignment validator.
```

这个 skill 会保持 cue 数量、顺序和时间戳不变。英文段落会翻译成中文，中文段落只做轻
校正；必要时会保留英文领域术语、产品名、人名、公司名、缩写和模型名。

## 输出文件

默认情况下，每次运行会生成一个可读的输出目录：

```text
<out-dir>/<title>__<short-id>/
```

输出目录包含：

- `metadata.json`：来源信息和字幕 provenance。
- `source.srt`：源语言字幕产物。
- `segments.json`：解析后的 segment 数据。
- `audio_sample.wav` 或下载的源音频：仅在本地 ASR 路径中出现。
- `transcript.zh.srt`：最终中文字幕产物，由 agent skill 生成，不由 CLI 直接生成。

新代码不应再生成旧的 `transcript.srt` 或 TXT 逐字稿文件。

## CLI 参数

```text
python -m podcast_to_text.cli <url> [options]
```

常用参数：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `url` | 必填 | 小宇宙单集 URL 或 YouTube URL。 |
| `--out-dir` | `out` | 生成产物的父目录。 |
| `--model` | `medium` | `faster-whisper` 模型名，例如 `tiny`、`small`、`medium`、`large-v3`。 |
| `--device` | `cpu` | Whisper 运行设备：`cpu`、`cuda` 或 `auto`。 |
| `--compute-type` | `int8` | Whisper 计算类型：`int8`、`float16`、`float32` 或 `default`。 |
| `--language` | `auto` | ASR 语言。`auto` 会让小宇宙默认中文，YouTube ASR fallback 自动检测源语言。 |
| `--beam-size` | `5` | Whisper beam size。较小值更快，较大值可能更充分。 |
| `--vad-filter` | 关闭 | 启用 Whisper 语音活动过滤。 |
| `--initial-prompt` | 无 | 给 Whisper 的词表或上下文提示，适合人名、产品名、术语。 |
| `--dir-template` | `title-id` | 输出目录命名方式：`title-id`、`id` 或 `title`。 |
| `--limit-seconds` | 无 | 只转录前 N 秒，适合测试。需要 `ffmpeg`。 |

## 限制和预期

- CLI 每次只处理一个 URL。
- 支持小宇宙单集页面和 YouTube watch、short、live、`youtu.be` 链接。
- 不抓取小宇宙 App 独有字幕数据。当前支持路径是网页/音频解析 + 本地 ASR。
- YouTube 字幕是否可用取决于视频本身。字幕下载也可能遇到平台限流；CLI 会尝试下
  一个字幕候选，最后回退到音频 ASR。
- 本地 ASR 质量受模型大小、音频质量、语言、口音和术语影响。人名、产品名、领域词
  建议通过 `--initial-prompt` 提示。
- CPU 转录可能较慢，尤其是大模型。快速测试用 `small`，质量优先时用 `large-v3`。
- 工具不做说话人分离、摘要或文章改写。
- `transcript.zh.srt` 由 agent skill 生成，不由 CLI 生成。

## 原理简介

### 小宇宙

1. CLI 拉取小宇宙单集页面。
2. 从页面中解析单集 metadata 和可播放音频 URL。
3. 如果页面暴露公开 transcript hint，会记录到 `metadata.json`，但不依赖私有 App API。
4. 下载音频；如果指定 `--limit-seconds`，则生成短音频样本。
5. 使用本地 `faster-whisper` ASR，写出 `source.srt`。

### YouTube

1. CLI 使用 `yt-dlp` 检查视频信息。
2. 在下载音频前优先尝试平台字幕。
3. 字幕优先级：
   - 人工中文字幕
   - 人工英文字幕
   - 自动中文字幕
   - 自动英文字幕
4. 下载到的字幕会标准化为 `source.srt`。
5. 如果某个字幕候选下载失败，CLI 会继续尝试下一个候选。
6. 如果没有可用字幕，CLI 会下载音频并运行本地 `faster-whisper` ASR。

## 中文适配 Skill

skill 位置：

```text
skills/chinese-srt-adaptation/
```

它会指导 agent：

- 读取 `source.srt`；
- 创建 `transcript.zh.srt`；
- 将英文翻译成中文；
- 对已有中文做轻校正；
- 保持 cue 编号、顺序、时间戳不变；
- 在标记 metadata complete 前运行 `scripts/validate_srt_alignment.py`。

需要时可以直接运行校验脚本：

```powershell
python skills/chinese-srt-adaptation/scripts/validate_srt_alignment.py `
  path\to\source.srt `
  path\to\transcript.zh.srt
```

## License

本项目使用 MIT License。详见 [LICENSE](LICENSE)。
