#!/usr/bin/env python3
"""Tool Guide Generator.
Reads tools.json, generates individual tool guide Markdown via LangChain + Qwen,
writes to ../content/guide/
"""
import json
import os
import sys
from pathlib import Path
from datetime import date

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
TOOLS_PATH = BASE_DIR / "data" / "tools.json"
CONTENT_DIR = BASE_DIR / "content" / "guide"
INDEX_PATH = BASE_DIR / "data" / "content-index.json"

GUIDE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一个专业的 AI 工具使用教程写手。根据提供的工具信息，写一篇详细的工具使用指南。

要求：
1. 标题格式: "{{工具名}} 完整使用指南：从入门到精通"
2. 正文使用 Markdown 格式，必须以 YAML frontmatter 开头
3. YAML frontmatter 包含: title, description, tool (单个工具slug), date (今日日期)
4. 正文结构:
   - ## 工具简介 — 1-2段介绍工具的定位、背景和核心价值
   - ## 核心功能 — 至少1张 Markdown 表格，列出主要功能及说明
   - ## 如何使用 — 分步骤说明使用方法，包含具体操作指导
   - ## 价格说明 — 列出不同套餐和价格
   - ## 适用场景 — 列出最适合的使用场景（至少3个）
   - ## 优缺点 — 分别列出优点和缺点
   - ## 同类替代工具 — 简要介绍2-3个同类替代工具
   - *免责声明*
5. 字数 1500-2500 字，中文
6. 内容详实、实用，侧重于实际操作指导
7. 表格至少要有 4 行数据

输出格式示例：
---
title: "ChatGPT 完整使用指南：从入门到精通"
description: "详细介绍 ChatGPT 的核心功能、使用方法、定价策略及适用场景，帮助你充分发挥这款 AI 对话工具的潜力"
tool: "chatgpt"
date: "{today}"
---

## 工具简介
...
"""),
    ("user", "请为以下工具写一篇详细的使用指南：\n\n{tool}")
]).partial(today=str(date.today()))


def load_tools():
    with open(TOOLS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_guide(tool):
    llm = ChatOpenAI(
        model=os.getenv("QWEN_MODEL", "qwen-plus"),
        base_url=os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        api_key=os.getenv("QWEN_API_KEY"),
        temperature=0.7,
    )
    messages = GUIDE_PROMPT.format_messages(
        tool=json.dumps(tool, ensure_ascii=False, indent=2),
    )
    response = llm.invoke(messages)
    return response.content


def save_article(slug, content):
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{slug}.md"
    filepath = CONTENT_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved: {filepath}")
    return filename.replace(".md", "")


def update_index(slug, frontmatter):
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    if INDEX_PATH.exists():
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            index = json.load(f)
    else:
        index = {"compare": [], "list": [], "guide": []}

    entry = {
        "slug": slug,
        "title": frontmatter.get("title", ""),
        "description": frontmatter.get("description", ""),
        "tool": frontmatter.get("tool", ""),
        "date": frontmatter.get("date", str(date.today())),
    }

    if "guide" not in index:
        index["guide"] = []

    existing = [i for i in index["guide"] if i["slug"] != slug]
    existing.append(entry)
    index["guide"] = existing

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"Updated index: {INDEX_PATH}")


def parse_frontmatter(content):
    import yaml
    lines = content.split("\n")
    if lines[0].strip() == "---":
        try:
            end = lines.index("---", 1)
            fm = yaml.safe_load("\n".join(lines[1:end]))
            return fm or {}
        except (ValueError, yaml.YAMLError):
            return {}
    return {}


def main():
    if not os.getenv("QWEN_API_KEY"):
        print("Error: QWEN_API_KEY not set. Create python-service/.env with your API key.", file=sys.stderr)
        sys.exit(1)

    tools = load_tools()

    for tool in tools:
        slug = tool["slug"]
        output_filename = slug

        if (CONTENT_DIR / f"{output_filename}.md").exists():
            print(f"Skip existing: {output_filename}.md")
            continue

        print(f"Generating guide for: {tool['name']} ({tool['category']})")
        for attempt in range(2):
            try:
                content = generate_guide(tool)
                saved_slug = save_article(slug, content)
                fm = parse_frontmatter(content)
                update_index(saved_slug, fm)
                break
            except Exception as e:
                print(f"  Attempt {attempt + 1} failed: {e}", file=sys.stderr)
                if attempt == 1:
                    print(f"  Giving up on {output_filename}")


if __name__ == "__main__":
    main()
