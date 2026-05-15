from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # --- 千问 API ---
    qwen_api_key: str
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen-plus"
    qwen_temperature: float = 0.7
    qwen_max_tokens: int = 2048

    # --- LangSmith 可观察性 ---
    langsmith_tracing: bool = True
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_api_key: str = ""
    langsmith_project: str = "ai-tools-guider"

    # --- 安全 ---
    api_key: str = ""
    query_max_length: int = 500

    # --- Agent ---
    agent_max_tool_calls: int = 10
    agent_timeout_seconds: int = 120

    # --- 会话 ---
    session_max_history: int = 20
    session_ttl_minutes: int = 60

    # --- 工具数据 ---
    tools_json_path: str = "../ai-tools-nav/data/tools.json"

    # --- 限流 ---
    rate_limit_per_minute: int = 10


settings = Settings()


def _export_langsmith_env():
    """将 LangSmith 配置导出到环境变量，LangChain/LangGraph 自动读取。"""
    import os
    if settings.langsmith_api_key:
        os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGSMITH_TRACING"] = str(settings.langsmith_tracing).lower()
        os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
        os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project


_export_langsmith_env()
