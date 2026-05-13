import functools
import os
from typing import AsyncIterator
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

from tools_data import search_tools, get_tools_by_category, list_categories

load_dotenv()

SYSTEM_PROMPT = """\
You are an AI tool recommendation expert. Your mission: understand the user's task and recommend the best AI tools to accomplish it.

## How to work
1. Understand what the user wants to accomplish (read their query carefully)
2. Use search_tools() to find relevant tools for each aspect of their task
3. Use get_tools_by_category() if you need to explore a specific category
4. Use list_categories() if the user asks what's available

## Recommendation rules
- Recommend tools across categories as a WORKFLOW, not just one tool
- For example: "做视频" -> script writing (chat) -> video generation (video) -> voiceover (audio)
- Every recommended tool MUST include: name, why it fits the task, and its URL
- Be specific: explain WHY each tool is a good fit, not just that it's "powerful"
- If the user's task is vague, ask a clarifying question instead of guessing

## Output format
Write naturally in Chinese, as a conversation. Structure your recommendation with clear steps. Put each tool name in **bold** and its URL on a separate line.
"""


@functools.lru_cache(maxsize=1)
def create_recommend_agent():
    api_key = os.getenv("QWEN_API_KEY")
    if not api_key:
        raise RuntimeError("QWEN_API_KEY 未设置，请在 .env 文件中配置 QWEN_API_KEY")
    llm = ChatOpenAI(
        model=os.getenv("QWEN_MODEL", "qwen-plus"),
        base_url=os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        api_key=api_key,
        temperature=0.7,
        streaming=True,
    )
    tools = [search_tools, get_tools_by_category, list_categories]
    return create_react_agent(llm, tools, state_modifier=SYSTEM_PROMPT)


async def recommend_stream(query: str) -> AsyncIterator[str]:
    try:
        agent = create_recommend_agent()
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=query)]},
            version="v2",
        ):
            kind = event.get("event")
            if kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and chunk.content:
                    yield chunk.content
    except Exception:
        yield "抱歉，AI 服务暂时不可用，请稍后重试。"
