from typing import Dict, Set

CONFUSION_GROUPS: Set[frozenset] = {
    frozenset({"8", "3", "6", "B"}),
    frozenset({"5", "6", "S"}),
    frozenset({"1", "l", "I", "|", "/"}),
    frozenset({"0", "O", "D"}),
    frozenset({"7", "1", "/"}),
}


def are_glyphs_confusable(g1: str, g2: str) -> bool:
    if g1 == g2:
        return False
    for group in CONFUSION_GROUPS:
        if g1 in group and g2 in group:
            return True
    return False


def detect_ocr_confusion(cand_a: str, cand_b: str) -> bool:
    """
    Returns True if discrepancies between candidate_a and candidate_b
    fall into known OCR glyph confusion sets.
    """
    s_a = cand_a.strip()
    s_b = cand_b.strip()

    if s_a == s_b:
        return False

    if len(s_a) != len(s_b):
        return False

    has_confusion = False
    for c1, c2 in zip(s_a, s_b):
        if c1 != c2:
            if are_glyphs_confusable(c1, c2):
                has_confusion = True
            else:
                return False  # Discrepancy outside confusion sets
    return has_confusion
