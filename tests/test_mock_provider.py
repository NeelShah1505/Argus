from pydantic import BaseModel
from packages.llm import MockLLMProvider, get_llm_provider


class SyntheticReport(BaseModel):
    title: str
    risk_level: str
    items_count: int


def test_mock_provider_generate_text():
    provider = MockLLMProvider()
    response = provider.generate_text("Summarize operating income drivers")
    assert isinstance(response, str)
    assert len(response) > 0


def test_mock_provider_generate_structured():
    provider = MockLLMProvider()
    report = provider.generate_structured("Generate risk report", SyntheticReport)
    assert isinstance(report, SyntheticReport)
    assert report.title.startswith("mock_")
    assert report.items_count == 1


def test_mock_provider_cell_adjudication():
    provider = MockLLMProvider()
    crop_fake_bytes = b"\x89PNG\r\n\x1a\n"
    result = provider.adjudicate_cell_crop(
        crop_image_bytes=crop_fake_bytes,
        candidate_a="$(1,245.50)",
        candidate_b="$1,245.50",
    )
    assert result["adjudicated_value"] == "$(1,245.50)"
    assert result["confidence"] >= 0.95
    assert "rationale" in result


def test_get_llm_provider_default():
    provider = get_llm_provider()
    assert isinstance(provider, MockLLMProvider)
