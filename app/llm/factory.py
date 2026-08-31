from typing import Optional
from app.core.exceptions import LLMProviderError
from app.llm.base import BaseLLMClient
from app.llm.groq import GroqClient
from app.llm.mock import MockLLMClient
from app.llm.nim import NIMClient
from app.utils.config import Settings, get_settings


def create_llm_client(settings: Optional[Settings] = None) -> BaseLLMClient:
    cfg = settings or get_settings()
    provider = cfg.LLM_PROVIDER.lower()

    if provider == "mock":
        return MockLLMClient()
    elif provider == "groq":
        return GroqClient(
            api_key=cfg.LLM_API_KEY or "",
            model=cfg.LLM_MODEL,
            base_url=cfg.LLM_BASE_URL or "https://api.groq.com/openai/v1",
        )
    elif provider == "nim":
        return NIMClient(
            api_key=cfg.LLM_API_KEY or "",
            model=cfg.LLM_MODEL,
            base_url=cfg.LLM_BASE_URL or "https://integrate.api.nvidia.com/v1",
        )
    else:
        raise LLMProviderError(f"Unsupported LLM provider '{cfg.LLM_PROVIDER}'. Supported: 'mock', 'groq', 'nim'")
