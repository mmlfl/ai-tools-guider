import json
import os
from pathlib import Path
from typing import Literal

BASE_DIR = Path(__file__).resolve().parent
TOOLS_PATH = Path(os.getenv(
    "TOOLS_JSON_PATH",
    str(BASE_DIR.parent / "ai-tools-nav" / "data" / "tools.json")
))

Category = Literal["chat", "image", "video", "code", "audio", "office", "search"]
CATEGORY_LABELS: dict[str, str] = {
    "chat": "对话聊天",
    "image": "图像生成",
    "video": "视频创作",
    "code": "编程开发",
    "audio": "音频语音",
    "office": "办公效率",
    "search": "智能搜索",
}


def _load_tools():
    with open(TOOLS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def search_tools(query: str, n: int = 5) -> str:
    """Search AI tools by keyword. Matches against name, description, tags, and category.
    Returns top-n matching tools with name, description, url, category, pricing, and tags.
    Use this when the user describes a task and you need to find relevant tools.

    Args:
        query: Chinese or English keywords to search for (e.g. "视频", "编程")
        n: Maximum number of results to return (default 5)
    """
    tools = _load_tools()
    keywords = query.lower().split()
    scored = []
    for t in tools:
        text = f"{t['name']} {t['description']} {' '.join(t['tags'])} {t['category']} {CATEGORY_LABELS.get(t['category'], '')}"
        score = 0
        for kw in keywords:
            if kw in text.lower():
                score += 1
        if score > 0:
            scored.append((score, t))
    scored.sort(key=lambda x: x[0], reverse=True)
    results = scored[:n]
    if not results:
        return json.dumps({"message": "No tools found for this query. Try broader keywords."}, ensure_ascii=False)
    return json.dumps([{
        "name": t["name"],
        "description": t["description"],
        "url": t["url"],
        "category": t["category"],
        "category_label": CATEGORY_LABELS.get(t["category"], t["category"]),
        "pricing": t["pricing"],
        "tags": t["tags"],
    } for _, t in results], ensure_ascii=False, indent=2)


def get_tools_by_category(category: str) -> str:
    """Get all AI tools in a specific category.
    Use this to browse tools when the user's task clearly maps to a category.

    Args:
        category: One of: chat, image, video, code, audio, office, search
    """
    tools = _load_tools()
    matched = [t for t in tools if t["category"] == category]
    if not matched:
        valid = ", ".join(CATEGORY_LABELS.keys())
        return json.dumps({"message": f"Unknown category '{category}'. Valid categories: {valid}"}, ensure_ascii=False)
    return json.dumps([{
        "name": t["name"],
        "description": t["description"],
        "url": t["url"],
        "pricing": t["pricing"],
        "tags": t["tags"],
    } for t in matched], ensure_ascii=False, indent=2)


def list_categories() -> str:
    """List all available AI tool categories with their Chinese labels.
    Use this when the user asks what kinds of tools are available.
    """
    return json.dumps(CATEGORY_LABELS, ensure_ascii=False, indent=2)
