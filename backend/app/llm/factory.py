import os

from .http import OpenAICompatibleProvider
from .mock import MockProvider


class FallbackProvider:
    """Keep the local demo usable when an external provider is unavailable."""
    def __init__(self, primary, fallback):
        self.primary = primary
        self.fallback = fallback

    async def structured_generate(self, *, messages, output_schema, temperature=0):
        try:
            return await self.primary.structured_generate(
                messages=messages, output_schema=output_schema, temperature=temperature
            )
        except Exception:
            return await self.fallback.structured_generate(
                messages=messages, output_schema=output_schema, temperature=temperature
            )


def get_provider():
    provider = os.getenv("LLM_PROVIDER", "mock").lower()
    if provider == "mock":
        return MockProvider()
    if provider in {"openai", "deepseek", "aliyun", "dashscope", "qwen"}:
        qwen_provider = provider in {"aliyun", "dashscope", "qwen"}
        api_key = ((os.getenv("DASHSCOPE_API_KEY", "").strip() or os.getenv("VISION_API_KEY", "").strip()) if qwen_provider else os.getenv("LLM_API_KEY", "").strip()) or os.getenv("LLM_API_KEY", "").strip()
        if not api_key or "在这里" in api_key or "YOUR_" in api_key.upper():
            return MockProvider()
        default_base = (
            "https://api.deepseek.com" if provider == "deepseek"
            else "https://dashscope.aliyuncs.com/compatible-mode/v1" if provider in {"aliyun", "dashscope", "qwen"}
            else "https://api.openai.com/v1"
        )
        configured_base = os.getenv("VISION_BASE_URL") if qwen_provider else os.getenv("LLM_BASE_URL")
        configured_model = os.getenv("VISION_MODEL") if qwen_provider else os.getenv("LLM_MODEL")
        primary = OpenAICompatibleProvider(
            base_url=configured_base or default_base,
            api_key=api_key,
            model=configured_model or ("qwen3-vl-flash" if qwen_provider else "deepseek-v4-flash" if provider == "deepseek" else "gpt-4o-mini"),
        )
        if os.getenv("LLM_FALLBACK_TO_MOCK", "true").lower() == "true":
            return FallbackProvider(primary, MockProvider())
        return primary
    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")


def get_vision_provider():
    provider = os.getenv("VISION_PROVIDER", "mock").lower()
    if provider == "mock":
        return MockProvider()
    if provider in {"aliyun", "dashscope", "qwen"}:
        api_key = (
            os.getenv("VISION_API_KEY", "").strip()
            or os.getenv("DASHSCOPE_API_KEY", "").strip()
            or os.getenv("LLM_API_KEY", "").strip()
        )
        if not api_key or "在这里" in api_key or "YOUR_" in api_key.upper():
            return MockProvider()
        return OpenAICompatibleProvider(
            base_url=os.getenv(
                "VISION_BASE_URL",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            ),
            api_key=api_key,
            model=os.getenv("VISION_MODEL", "qwen3-vl-flash"),
        )
    raise ValueError(f"Unsupported VISION_PROVIDER: {provider}")
