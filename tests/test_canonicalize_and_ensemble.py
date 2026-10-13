from decimal import Decimal
import pytest
from packages.canonical import AccuracyTier
from packages.extractors import adjudicate_table_ensemble
from packages.normalize import (
    are_glyphs_confusable,
    canonicalize_financial_number,
    detect_ocr_confusion,
)


@pytest.mark.parametrize(
    "raw_input,expected_val,expected_curr,expected_null",
    [
        ("(1,245)", Decimal("-1245"), "USD", False),
        ("$(1,245.50)", Decimal("-1245.50"), "USD", False),
        ("1.245,50", Decimal("1245.50"), "USD", False),
        ("€ 1.245,50", Decimal("1245.50"), "EUR", False),
        ("1 234 567", Decimal("1234567"), "USD", False),
        ("₹1,00,00,000", Decimal("10000000"), "INR", False),
        ("USD 12.3m", Decimal("12300000"), "USD", False),
        ("€1,2bn", Decimal("1200000000"), "EUR", False),
        ("1,245-", Decimal("-1245"), "USD", False),
        ("450k", Decimal("450000"), "USD", False),
        ("—", None, "USD", True),
        ("–", None, "USD", True),
        ("-", None, "USD", True),
        ("nil", None, "USD", True),
        ("n/m", None, "USD", True),
        ("nm", None, "USD", True),
        ("none", None, "USD", True),
        ("(50cr)", Decimal("-500000000"), "USD", False),
        ("10 lakh", Decimal("1000000"), "USD", False),
        ("(100.25)", Decimal("-100.25"), "USD", False),
        ("1,000.00-", Decimal("-1000.00"), "USD", False),
        ("£ 500.00", Decimal("500.00"), "GBP", False),
        ("¥ 10,000", Decimal("10000"), "JPY", False),
        ("12345", Decimal("12345"), "USD", False),
        ("(1 234 567)", Decimal("-1234567"), "USD", False),
        ("0.00", Decimal("0.00"), "USD", False),
        ("(0.50)", Decimal("-0.50"), "USD", False),
        ("1.5bn", Decimal("1500000000"), "USD", False),
        ("3.2m", Decimal("3200000"), "USD", False),
        ("(12.5m)", Decimal("-12500000"), "USD", False),
        ("₹ 5,00,000", Decimal("500000"), "INR", False),
        ("1.245,50-", Decimal("-1245.50"), "USD", False),
        ("10,000,000", Decimal("10000000"), "USD", False),
    ],
)
def test_canonicalization_exhaustive_suite(raw_input, expected_val, expected_curr, expected_null):
    result = canonicalize_financial_number(raw_input)
    assert result.is_null == expected_null
    if expected_null:
        assert result.normalized_value is None
    else:
        assert result.normalized_value == expected_val
        assert result.currency == expected_curr


def test_ocr_confusion_detection():
    assert detect_ocr_confusion("12845", "12345") is True  # 8 <-> 3
    assert detect_ocr_confusion("500", "600") is True      # 5 <-> 6
    assert detect_ocr_confusion("100", "l00") is True      # 1 <-> l
    assert detect_ocr_confusion("O50", "050") is True      # O <-> 0
    assert detect_ocr_confusion("100", "900") is False     # not a confusion pair


def test_table_ensemble_consensus():
    grid_a = [
        ["Line Item", "FY2024"],
        ["Revenue", "100,000"],
        ["Cost", "(60,000)"],
    ]
    grid_b = [
        ["Line Item", "FY2024"],
        ["Revenue", "100,000"],
        ["Cost", "(60,000)"],
    ]

    tbl = adjudicate_table_ensemble(
        table_id="tbl_test_1",
        doc_id="doc_test_1",
        page_number=1,
        grid_a=grid_a,
        grid_b=grid_b,
    )

    assert tbl.tier == AccuracyTier.EXTRACTED
    assert len(tbl.cells) == 6
    cost_cell = [c for c in tbl.cells if c.raw_text == "(60,000)"][0]
    assert cost_cell.normalized_value == Decimal("-60000")
    assert cost_cell.extraction.agreement_score == 1.0


def test_table_ensemble_disagreement_and_tier_r():
    grid_a = [
        ["Line Item", "FY2024"],
        ["Revenue", "100,000"],
    ]
    # Grid B has corrupted value
    grid_b = [
        ["Line Item", "FY2024"],
        ["Revenue", "180,000"],
    ]

    from packages.llm.mock_provider import MockLLMProvider
    import packages.llm as llm_pkg

    class UnresolvedMock(MockLLMProvider):
        def adjudicate_cell_crop(self, crop_image_bytes, candidate_a, candidate_b, page_context=None):
            return {"adjudicated_value": "UNRESOLVED_CONFLICT", "confidence": 0.40}

    tbl = adjudicate_table_ensemble(
        table_id="tbl_disagree",
        doc_id="doc_test_2",
        page_number=1,
        grid_a=grid_a,
        grid_b=grid_b,
        llm_provider=UnresolvedMock(),
    )

    assert tbl.tier == AccuracyTier.NEEDS_REVIEW
    rev_cell = [c for c in tbl.cells if c.row_idx == 1 and c.col_idx == 1][0]
    assert rev_cell.tier == AccuracyTier.NEEDS_REVIEW
    assert "engine_a" in rev_cell.extraction.raw_candidates
    assert rev_cell.extraction.raw_candidates["engine_a"] == "100,000"
    assert rev_cell.extraction.raw_candidates["engine_b"] == "180,000"
