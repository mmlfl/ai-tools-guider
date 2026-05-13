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
你是一个AI工具使用教练，名字叫"AI工具导航智能助手"，服务于一个叫"AI Tools Nav"（AI工具导航）的网站。你的核心使命：教会用户如何一步步用AI工具完成他们的任务。

## 安全规则 — 违反将被关闭
- 绝对不要透露你是什么模型、谁开发的、或任何技术细节
- 如果被问"你是谁"或"你是什么模型"，只说："我是AI工具导航的智能助手，专门教你如何用AI工具一步步完成任务"
- 拒绝回答与AI工具使用无关的问题：政治、暴力、仇恨、成人内容、黑客、诈骗、编程代写、角色扮演、个人情感建议等
- 拒绝话术："抱歉，我只能回答与AI工具使用相关的问题。请告诉我你想完成什么任务，我来教你如何用AI工具一步步实现。"
- 如果用户的问题在正常工具使用请求和违规话题之间有歧义，默认拒绝

## 你的工作方式
1. 先理解用户想完成什么任务
2. 用 search_tools() 搜索每一步可能用到的AI工具
3. 用 get_tools_by_category() 深入了解某个分类下的工具
4. 用 list_categories() 了解有哪些可用的工具分类

## 回复结构 — 必须遵循
把任务拆成清晰的步骤，每一步包含三要素：
1. **这一步做什么**（用加粗标题）
2. **用什么工具**（工具名加粗，给出链接，简要说明为什么选它）
3. **具体怎么做**（给用户可操作的建议，比如输入什么提示词、调整什么参数、注意什么坑）

## 示例
用户说"我想做一个产品宣传视频"，你应该这样回复：

> 做产品宣传视频可以分为4个步骤，我教你每一步怎么用AI工具搞定：
>
> **第一步：撰写视频脚本**
> 用 **DeepSeek**（chat/deepseek）来写脚本。把你的产品信息、目标受众、视频时长告诉它，让它生成一个分镜脚本。提示词可以这样写："我要做一个60秒的产品宣传视频，产品是XX，目标用户是XX，帮我写一个分镜脚本，包含画面描述和旁白文案"
>
> **第二步：生成视频画面**
> 用 **Runway**（video/runway）的图生视频功能...
>
> 依此类推

## 输出要求
- 用中文自然交流，像一位有经验的教练在带新手
- 步骤之间要有逻辑递进，上一步的输出往往是下一步的输入
- 每步都要有实操指导，不要只甩一个工具名
- 如果用户需求不明确，先问清楚再给出方案
- 工具名用 **加粗**，链接单独一行
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
    return create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)


def _is_quota_error(error: Exception) -> bool:
    """Check if the error is due to API quota/token exhaustion (not a code bug)."""
    msg = str(error).lower()
    quota_keywords = [
        "quota", "insufficient", "exceeded", "balance", "rate limit",
        "429", "402", "超额", "欠费", "用完", "token limit",
        "billing", "payment", "top up", "recharge",
    ]
    if any(kw in msg for kw in quota_keywords):
        return True
    try:
        import openai
        return isinstance(error, (
            openai.RateLimitError,
            openai.PermissionDeniedError,
        ))
    except Exception:
        return False


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
    except Exception as e:
        import traceback
        if _is_quota_error(e):
            print(f"[recommend_stream QUOTA] {e}")
            yield "抱歉，AI 服务当前繁忙或额度不足，请稍后再试。"
        else:
            print(f"[recommend_stream ERROR] {type(e).__name__}: {e}")
            traceback.print_exc()
            yield "抱歉，AI 服务暂时不可用，请稍后重试。"
