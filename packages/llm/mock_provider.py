from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel
from .base import BaseLLMProvider

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic mock provider for CI, automated testing, and offline execution.
    Requires zero API keys and returns schema-compliant synthetic data.
    """

    def __init__(self, canned_responses: Optional[Dict[str, Any]] = None):
        self.canned_responses = canned_responses or {}

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
    ) -> str:
        for pattern, response in self.canned_responses.items():
            if pattern in prompt:
                return str(response)
        return "Argus Mock Response: Verified financial narrative grounded in tool data."

    def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
    ) -> T:
        # Check canned responses first
        for pattern, response in self.canned_responses.items():
            if pattern in prompt and isinstance(response, dict):
                return response_model.model_validate(response)

        # Build a synthetic instance from model fields
        synthetic_data: Dict[str, Any] = {}
        for field_name, field_info in response_model.model_fields.items():
            annotation = field_info.annotation
            if annotation == str:
                synthetic_data[field_name] = f"mock_{field_name}"
            elif annotation == int:
                synthetic_data[field_name] = 1
            elif annotation == float:
                synthetic_data[field_name] = 1.0
            elif annotation == bool:
                synthetic_data[field_name] = True
            elif hasattr(annotation, "__origin__") and annotation.__origin__ == list:
                synthetic_data[field_name] = []
            elif hasattr(annotation, "__origin__") and annotation.__origin__ == dict:
                synthetic_data[field_name] = {}
            else:
                synthetic_data[field_name] = None

        return response_model.model_validate(synthetic_data)

    def adjudicate_cell_crop(
        self,
        crop_image_bytes: bytes,
        candidate_a: str,
        candidate_b: str,
        page_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Adjudicate disagreement deterministically:
        Favors clean numeric candidate or returns candidate_a as consensus.
        """
        chosen = candidate_a if candidate_a.strip() else candidate_b
        return {
            "adjudicated_value": chosen,
            "confidence": 0.98,
            "engine_agreement": False,
            "rationale": "Visual inspection verified candidate against cell crop geometry.",
        }

    def extract_figure_visual(
        self,
        crop_image_bytes: bytes,
        figure_type: str = "chart",
        page_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Multimodal visual analysis of a cropped figure (chart, flowchart, organization hierarchy).
        """
        if figure_type == "diagram":
            return {
                "diagram_type": "process_flow",
                "nodes": [
                    {"id": "node_1", "text": "Customer Ingestion", "node_type": "input"},
                    {"id": "node_2", "text": "Verification Gate", "node_type": "process"},
                    {"id": "node_3", "text": "Audit Attestation", "node_type": "output"},
                ],
                "edges": [
                    {"from_node_id": "node_1", "to_node_id": "node_2", "label": "extracts"},
                    {"from_node_id": "node_2", "to_node_id": "node_3", "label": "verifies"},
                ],
            }
        else:
            # Default chart extraction
            return {
                "title": "Extracted Raster Chart",
                "series_name": "Revenue Highlights",
                "points": [
                    {"x_label": "Q1", "y_value": "120.5", "tolerance": "2.5"},
                    {"x_label": "Q2", "y_value": "135.0", "tolerance": "2.5"},
                    {"x_label": "Q3", "y_value": "150.2", "tolerance": "2.5"},
                ],
            }
