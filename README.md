# AI Tools Nav - 智能助手

> 为 [lflaitool.top](https://lflaitool.top) 提供 AI 驱动的智能任务引导服务。

## 它是什么

AI Tools Nav 智能助手不是普通的工具推荐引擎——它是一个 **AI 任务教练**。你告诉它你想做什么，它教你如何用 AI 工具一步一步完成。

不需要自己研究几十个 AI 工具哪个好、怎么用、顺序是什么。智能助手已经帮你理清了——每一步用什么工具、为什么选它、具体怎么操作、有什么坑要避开。

## 怎么工作的

用户在前端输入任意自然语言需求（比如"我想做一个产品宣传视频"），后端接入大模型，通过 **ReAct Agent** 自主调用工具搜索 AI 工具库，理解任务后将需求拆解为可执行的步骤，并**流式输出**每一步的详细指导：

- **第一步做什么** — 清晰的任务拆解
- **用什么工具** — 精准匹配，给出理由
- **具体怎么操作** — 提示词示例、参数建议、避坑指南

整个过程词接词实时呈现，就像在跟一个有经验的教练对话。

## 技术栈

| 层级 | 技术 |
|------|------|
| AI Agent 框架 | LangGraph ReAct Agent |
| 大模型 | 阿里千问（Qwen） |
| API 框架 | FastAPI |
| 流式传输 | Server-Sent Events (SSE) |
| 前端集成 | Next.js（[lflaitool.top](https://lflaitool.top)） |

## 项目结构

```
ai-tools-recommendation/
├── server.py              # FastAPI 服务入口
├── recommend_engine.py    # LangGraph ReAct Agent + 流式推理
├── tools_data.py          # AI 工具库搜索函数
├── pyproject.toml         # 依赖管理 (uv)
└── uv.lock                # 依赖锁定
```
