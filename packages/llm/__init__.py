import os
from typing import Optional
from .base import BaseLLMProvider
from .mock_provider import MockLLMProvider


def get_llm_provider(provider_type: Optional[str] = None) -> BaseLLMProvider:
    """
    Factory resolving provider from environment or argument.
    Defaults to MockLLMProvider to guarantee zero external dependency requirement.
    """
    selected = (provider_type or os.getenv("LLM_PROVIDER", "mock")).lower()
    if selected == "mock":
        return MockLLMProvider()
    elif selected == "openai":
        # Placeholder for OpenAIProvider when enabled in Phase 2
        return MockLLMProvider()
    elif selected == "anthropic":
        # Placeholder for AnthropicProvider when enabled in Phase 2
        return MockLLMProvider()
    return MockLLMProvider()


__all__ = ["BaseLLMProvider", "MockLLMProvider", "get_llm_provider"]
