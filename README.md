<div align="center">

# 📡 AgentFeed

### The Universal Information Perception, LLM Curation & Ingestion Framework for AI Agents
**专为各大 AI Agent 打造的全源信息感知、大模型智能梳理与多渠道分发框架**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Framework: FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Agent Ready](https://img.shields.io/badge/Agent--Ready-Claude%20%7C%20Codex%20%7C%20Antigravity-purple.svg)]()
[![Cloudflare R2](https://img.shields.io/badge/Deploy-Cloudflare%20R2%20%7C%20Local-F38020.svg)]()

[English](#english) | [简体中文](#-为什么需要-agentfeed)

</div>

---

## 💡 为什么需要 AgentFeed？

在构建自主智能体（AI Agents，如 Claude Code、OpenAI Operator、Antigravity、AutoGPT 等）时，开发者面临的核心痛点是：**缺乏开箱即用、免登录、抗反爬、结构化的外部世界实时信息感知层（Perception Layer）**。

传统爬虫方案脆弱且极易被封禁，而直接调用搜索 API 成本高昂且缺乏垂直领域深度。**AgentFeed** 提供了全链路的一体化开箱即用方案：

1. **🌐 全源免登录感知矩阵 (Perception Layer)**：覆盖 11 大核心渠道（原生 XML/RSS 直链、全网新闻媒体、𝕏 行业博主、Telegram 突发频道、Discord 社区、Substack 深度研报、微信公众号、Y Combinator Hacker News、Reddit 极客社区、ArXiv & HuggingFace AI 顶会论文、SEC EDGAR 官方申报与全球宏观利率）。
2. **🧠 大模型智能梳理流水线 (LLM Curation)**：跨源语义去重、多维聚类分类、核心事实与宏观推演摘要、行业实体与行情标的提取。
3. **🚀 多渠道分发中心 (Distribution Hub)**：原生支持飞书云文档（自动排版）、飞书群机器人（交互卡片）、Obsidian（双链笔记归档）、SMTP 邮件与全球 CDN RSS / Web 晚报。
4. **🔌 零配置与优雅降级**：未配置外置大模型 Key 时，全自动启用电脑内置 Agent CLI（Antigravity / Codex / Claude）或高性能规则引擎；未配置云存储时自动输出本地静态文件。

---

## 🏛️ 系统架构 (Architecture)

```mermaid
flowchart TD
    subgraph S1 [🌐 1. 全源感知采集矩阵 (Perception Layer)]
        A1[📡 1. 原生 XML / RSS / RSSHub]
        A2[🌐 2. 全网媒体网站 (跳付费墙/反反爬)]
        A3[𝕏 3. 博主大V (X/Twitter)]
        A4[✈️ 4. Telegram 开放预览通道]
        A5[🎮 5. Discord 官方社区]
        A6[📑 6. Substack 顶级投研专栏]
        A7[💬 7. 微信公众号买方长文]
        A8[🔶 8. Hacker News 热门讨论]
        A9[🤖 9. Reddit 垂直极客社区]
        A10[📚 10. ArXiv & HuggingFace Papers]
        A11[🏛️ 11. SEC EDGAR 申报与宏观利率]
    end

    subgraph S2 [🧠 2. 大模型智能梳理引擎 (LLM Curation)]
        B1[多源聚类与跨通道语义去重]
        B2[核心事实与买方级推演摘要]
        B3[实体提取、标的行情关联与双链构建]
        B4[OpenAI / Gemini / Claude / 本地 Agent 引擎]
    end

    subgraph S3 [🚀 3. 多渠道分发中心 (Distribution Hub)]
        C1[📄 飞书云文档 (Docx OpenAPI 自动创建)]
        C2[💬 飞书群自定义机器人 (富文本交互卡片)]
        C3[💎 Obsidian 知识库 (Frontmatter + 双链笔记)]
        C4[📧 电子邮箱 (SMTP 每日简报)]
        C5[☁️ 在线晚报 & RSS 全球 CDN (Cloudflare R2 / 本地静态发布)]
    end

    S1 --> S2 --> S3
```

---

## ✨ 核心特性

- **⚡ 100% 零登录与反反爬引擎**：基于 RSSHub 节点池、Defuddle、Camoufox 与 Ego Lite 浏览器静默复用，全自动绕过 Cloudflare 与付费墙。
- **🤖 多模型协议与本地 Agent 兜底**：
  - OpenAI 兼容协议（DeepSeek / SiliconFlow / Qwen / Moonshot / OpenRouter）
  - Google Gemini 原生 API（Gemini 2.5 Pro / Flash）
  - Anthropic Claude 原生 API（Claude 3.7 / 3.5 Sonnet）
  - 💻 电脑内置 Agent 降级（自动调度本地 Antigravity / Codex CLI 与高性能投研规则引擎，零配置零成本）
- **📄 飞书双模式分发**：
  - **飞书云文档**：自动调用 Docx OpenAPI 在云空间生成排版完善的日报，包含 Callout 引用框、行情指标与标的跳转。
  - **飞书群机器人**：推送带涨跌红绿条、分类折叠与直达云文档的富文本卡片。
- **🔍 Obsidian 本地 Vault 智能探测**：一键探测本机所有 Obsidian 知识库，自动写入符合买方投研规范的 Markdown 双链笔记。
- **☁️ 双模静态发布 (Cloudflare R2 / Local Static)**：
  - 支持配置自己的 Cloudflare R2 / S3 兼容存储桶与自定义域名，全自动生成全球 CDN 加速的沉浸式晚报网页与标准 RSS 源。
  - 无需云存储时，自动降级在本地 `./dist/` 生成静态 HTML 与 XML 文件。
- **🎛️ 现代极简 Web 控制台**：单页可视化管理 11 大板块、单源即时测速、实时测试各分发渠道。

---

## 🚀 快速开始

### 1. 克隆仓库与安装依赖

```bash
git clone https://github.com/your-username/agentfeed.git
cd agentfeed

# 创建虚拟环境并激活
python3 -m venv .venv
source .venv/bin/activate  # Windows 用户: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境凭据（可选）

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件填入您的 Cloudflare R2、大模型 Key 或飞书凭据（非必填，均支持默认降级）
vim .env
```

### 3. 启动可视化管理控制台 (Web Admin)

```bash
python server.py
```
打开浏览器访问：👉 **`http://127.0.0.1:9830`**

### 4. 命令行一键触发全流程执行

```bash
python run_daily_brief.py
```

---

## 🔌 在 AI Agent 中作为感知层使用

### Python SDK 方式：

```python
from llm_curator import curate_daily_intel
from scraper_rss import fetch_all_rss
from scraper_sec import fetch_all_sec_filings

# 1. 抓取多源实时情报
rss_items = fetch_all_rss()
sec_items = fetch_all_sec_filings(["NVDA", "TSLA", "AAPL"])

# 2. 调用大模型结构化提炼
curated_intel = curate_daily_intel(raw_items=rss_items, sec_filings=sec_items)

# 3. 注入 Agent 上下文消费
print(curated_intel["lead_summary"])
print(curated_intel["categories"])
```

---

## ⚙️ 核心配置说明 (`sources.json`)

`sources.json` 包含了全部 11 大感知板块的订阅列表与 4 大分发渠道的配置：

```json
{
  "channel_toggles": {
    "rss": true,
    "web": true,
    "blog": true,
    "tg": true,
    "dc": true,
    "sub": true,
    "wx": true,
    "hn": true,
    "reddit": true,
    "arxiv": true,
    "sec": true
  },
  "distribution_settings": {
    "feishu": { "enabled": false, "webhook_url": "" },
    "feishu_doc": { "enabled": false, "app_id": "", "app_secret": "" },
    "obsidian": { "enabled": true, "vault": "DefaultVault", "folder": "Daily Intel" },
    "email": { "enabled": false, "smtp_host": "smtp.qq.com" },
    "web_and_rss": {
      "enabled": true,
      "web_url": "https://feed.your-domain.com/",
      "rss_url": "https://feed.your-domain.com/feed.xml"
    }
  }
}
```

---

## 🗺️ 路线图 (Roadmap)

- [x] 全源免登录数据采集矩阵（11 大渠道）
- [x] 大模型语义去重、多维分类与实体提炼
- [x] 飞书群卡片与飞书原生云文档自动生成
- [x] Obsidian 本地 Vault 智能探测与双链归档
- [x] 多 LLM 协议支持（OpenAI / Gemini / Claude / 本地 Agent）
- [x] Cloudflare R2 / 本地双模静态晚报与 RSS 发布
- [ ] 标准 MCP (Model Context Protocol) Server 插件封装
- [ ] GitHub Actions 自动化定时运行流水线
- [ ] 基于向量数据库 (Chroma / Qdrant) 的历史情报 RAG 检索

---

## 📄 开源许可证 (License)

本项目基于 [MIT License](LICENSE) 开源。欢迎提交 Issue 与 Pull Request！
