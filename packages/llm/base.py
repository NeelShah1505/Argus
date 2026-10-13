from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseLLMProvider(ABC):
    """
    Abstract interface for LLM and Vision multimodal providers.
    Guarantees that all extraction, adjudication, and reasoning operations
    are fully decoupled from specific vendors (OpenAI, Anthropic, or local).
    """

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
    ) -> str:
        """Generate unstructured text response."""
        pass

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
    ) -> T:
        """Generate schema-constrained structured output."""
        pass

    @abstractmethod
    def adjudicate_cell_crop(
        self,
        crop_image_bytes: bytes,
        candidate_a: str,
        candidate_b: str,
        page_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Adjudicate extraction disagreement by inspecting the visual cell crop.
        Returns consensus string and confidence score.
        """
        pass
