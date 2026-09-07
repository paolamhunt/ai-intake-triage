"""Deterministic validation for evidence taken from an inquiry."""

import unicodedata


def normalize_evidence_text(value: str) -> str:
    """Normalize harmless text differences without changing meaning."""
    unicode_normalized = unicodedata.normalize("NFKC", value)
    case_normalized = unicode_normalized.casefold()
    return " ".join(case_normalized.split())


def evidence_is_traceable(
    inquiry_text: str,
    evidence: str,
) -> bool:
    """Return whether evidence is an exact normalized inquiry substring."""
    normalized_inquiry = normalize_evidence_text(inquiry_text)
    normalized_evidence = normalize_evidence_text(evidence)

    return bool(normalized_evidence and normalized_evidence in normalized_inquiry)
