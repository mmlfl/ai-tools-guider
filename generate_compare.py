#!/usr/bin/env python3
"""Tool Comparison Article Generator.
Reads tools.json, generates comparison Markdown via LangChain + Qwen (阿里千问),
writes to ../content/compare/
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
CONTENT_DIR = BASE_DIR / "content" / "compare"
INDEX_PATH = BASE_DIR / "data" / "content-index.json"
COMPARE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一个专业的 AI 工具评测写手。根据提供的工具信息，写一篇深度工具对比文章。

要求：
1. 标题格式: "工具A vs 工具B：2026年全面对比评测"
2. 正文使用 Markdown 格式，必须以 YAML frontmatter 开头
3. YAML frontmatter 包含: title, description, tools (slugs数组), date (今日日期)
4. 正文结构:
   - ## 概述 — 2-3段介绍两个工具
   - ## 功能对比 — 至少1张 Markdown 表格
   - ## 价格对比 — 1张表格
   - ## 适用场景 — 分别说明每个工具最适合的场景
   - ## 总结与推荐 — 给出明确的推荐建议
   - *免责声明*
5. 字数 1500-2500 字，中文
6. 客观中立，列出每个工具的优缺点
7. 表格至少要有 4 行数据

输出格式示例：
---
title: "ChatGPT vs Claude：2026年全面对比评测"
description: "详细对比 ChatGPT 和 Claude 的功能、价格、适用场景，帮助你选择最合适的 AI 对话工具"
tools: ["chatgpt", "claude"]
date: "{today}"
---

## 概述
...
"""),
    ("user", "请为以下两个工具写对比文章：\n\n工具1：{tool1}\n工具2：{tool2}\n\n分类：{category}")
]).partial(today=str(date.today()))


def load_tools():
    with open(TOOLS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_compare(tool1, tool2, category):
    llm = ChatOpenAI(
        model=os.getenv("QWEN_MODEL", "qwen-plus"),
        base_url=os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        api_key=os.getenv("QWEN_API_KEY"),
        temperature=0.7,
    )
    messages = COMPARE_PROMPT.format_messages(
        tool1=json.dumps(tool1, ensure_ascii=False, indent=2),
        tool2=json.dumps(tool2, ensure_ascii=False, indent=2),
        category=category,
    )
    response = llm.invoke(messages)
    return response.content



def save_article(slugs, content):
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{slugs[0]}-vs-{slugs[1]}.md"
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
        "tools": frontmatter.get("tools", []),
        "date": frontmatter.get("date", str(date.today())),
    }

    existing = [i for i in index["compare"] if i["slug"] != slug]
    existing.append(entry)
    index["compare"] = existing

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
    categories = {}
    for t in tools:
        categories.setdefault(t["category"], []).append(t)

    for cat, cat_tools in categories.items():
        if len(cat_tools) < 2:
            continue
        t1, t2 = cat_tools[0], cat_tools[1]
        slugs = [t1["slug"], t2["slug"]]
        output_filename = f"{slugs[0]}-vs-{slugs[1]}"

        if (CONTENT_DIR / f"{output_filename}.md").exists():
            print(f"Skip existing: {output_filename}.md")
            continue

        print(f"Generating: {t1['name']} vs {t2['name']} ({cat})")
        for attempt in range(2):
            try:
                content = generate_compare(t1, t2, cat)
                slug = save_article(slugs, content)
                fm = parse_frontmatter(content)
                update_index(slug, fm)
                break
            except Exception as e:
                print(f"  Attempt {attempt + 1} failed: {e}", file=sys.stderr)
                if attempt == 1:
                    print(f"  Giving up on {output_filename}")


if __name__ == "__main__":
    main()
