[**中文**](README.md) | [English](docs/README_en.md) | [日本語](docs/README_ja.md) | [한국어](docs/README_ko.md) | [Español](docs/README_es.md) | [Français](docs/README_fr.md)

<div align="center">

# 🐸 呱邻国

**完全由 AI 驱动。输入 API，实现语言自由。**

[![React](https://img.shields.io/badge/React-18-61dafb?logo=react)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776ab?logo=python)](https://python.org)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)

</div>

---

## 呱邻国是什么？

呱邻国是一个 AI 驱动的沉浸式外语学习平台。你提供任何文本，AI 自动生成词汇表、分句翻译和多种练习题，配合语音朗读，把每一段文字都变成你的专属学习材料。

**任何语言 → 任何语言，你的素材你做主。**

**只需一个 API Key，纯 LLM 能力驱动一切。**

---

## 详细介绍

👉 [查看完整介绍页面](https://gualingo.dpdns.org/)

---

## 核心设计理念

### 零手工干预，纯 LLM 驱动

从句子解析、单词划分到释义生成，**全程由 LLM 完成，没有任何手工规则或词典依赖**。AI 理解上下文，自动判断词边界、提取词根、生成释义和例句——你只需提供文本，剩下的交给 AI。

### 优雅的 LLM 输出格式

精心设计的 prompt 与结构化输出格式，确保 LLM 返回的数据干净、可解析、可直接使用。不依赖后处理修正，一次调用即得所需结果。

### 极致节省 Token

通过精简 prompt、压缩输出格式、避免冗余字段，**将 token 消耗降至最低**。同样的学习内容，用更少的 token 完成，降低 API 成本。

---

## 演示视频

<div align="center">

<!-- 视频占位，后续替换为实际演示视频 -->
<!-- <video src="docs/demo.mp4" controls width="100%"></video> -->

📹 *演示视频即将上线*

</div>

---

## 🚀 快速开始

### 方式一：下载桌面应用（推荐）

前往 [GitHub Releases](https://github.com/rhouselyn/Gualingo/releases) 下载对应平台的安装包：

| 平台 | 文件 |
|------|------|
| Windows | `Gualingo Setup x.x.x.exe`（安装程序） |
| macOS | `Gualingo-x.x.x.dmg` |
| Linux | `Gualingo-x.x.x.AppImage` |

Windows 运行安装程序即可；macOS 打开 dmg 后将应用拖入 Applications 文件夹；Linux 给 AppImage 添加执行权限后直接运行。

> **macOS 用户**：首次打开时如提示"无法验证开发者"，请右键点击应用 → 选择"打开" → 在弹窗中再次点击"打开"即可。如仍无法打开，可在终端执行 `xattr -cr /Applications/Gualingo.app`。

### 方式二：Docker 部署

```bash
docker run -d \
  -p 8000:8000 \
  -v gualingo-data:/root/.local/share/Gualingo \
  ghcr.io/rhouselyn/gualingo:latest
```

打开 http://localhost:8000 即可使用。

### 方式三：从源码运行

#### 环境要求

- Python 3.10+
- Node.js 18+
- 一个 LLM API Key（支持 OpenAI 兼容接口，如 SiliconFlow、DeepSeek 等）

#### 安装与启动

```bash
# 1. 安装后端依赖
cd backend
pip install -r requirements.txt

# 2. 构建前端
cd ../frontend && npm install && npm run build

# 3. 启动后端
cd .. && uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

打开 http://localhost:8000 即可使用。

#### 桌面应用模式

```bash
# 构建前端
cd frontend && npm install && npm run build

# 启动桌面应用
cd .. && python app.py
```

---

## 🛠 技术栈

| 层 | 技术 |
|----|------|
| 前端 | React 18 · Vite · TailwindCSS · Framer Motion · Web Speech API |
| 后端 | FastAPI · Uvicorn · OpenAI 兼容 LLM API |
| 存储 | SQLite（自动迁移旧文件数据） |
| 桌面端 | Electron · PyInstaller |

---

## 📖 使用流程

```
输入文本 → AI 分句翻译 → 生成词汇表 → 阶段一：学单词 → 阶段二：练句子 → 错题回顾
```

1. **输入文本**：直接粘贴、翻译成目标语言、或让 AI 生成
2. **浏览字典**：查看分句翻译和词汇释义，随时查阅任意单词
3. **阶段一**：单词选择、句子翻译、听力理解
4. **阶段二**：遮蔽填空、翻译重组
5. **错题回顾**：答错的题自动收集，强化练习直到掌握

---

## ⚙️ 配置

所有配置通过界面设置完成，无需编辑配置文件：

- **API Key**：支持多组配置轮询，限速自动切换
- **母语**：选择界面显示语言
- **每页数量**：控制词汇表每页显示的单词数
- **重试间隔**：API 限速后的等待时间

---

## 📄 许可

[GNU Affero General Public License v3](LICENSE)
