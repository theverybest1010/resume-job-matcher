import pytest

from resume_matcher.candidate_phrases import CandidatePhraseExtractor


@pytest.fixture(scope="module")
def extractor() -> CandidatePhraseExtractor:
    """Load the English pipeline once for this test module."""

    return CandidatePhraseExtractor()


def test_extracts_action_oriented_candidate_phrases(
    extractor: CandidatePhraseExtractor,
) -> None:
    text = (
        "Developed predictive models and provided medical care "
        "to hospital patients. "
        "Managed financial reports for several clients."
    )

    assert extractor.extract(text) == [
        "Developed predictive models",
        "provided medical care to hospital patients",
        "Managed financial reports",
    ]


def test_preserves_recipient_context_at_sentence_start(
    extractor: CandidatePhraseExtractor,
) -> None:
    text = "Provided medical care to hospital patients."

    assert extractor.extract(text) == [
        "Provided medical care to hospital patients",
    ]


def test_empty_text_returns_no_candidates(
    extractor: CandidatePhraseExtractor,
) -> None:
    assert extractor.extract("   ") == []


def test_rejects_invalid_maximum_length() -> None:
    with pytest.raises(
        ValueError,
        match="max_tokens must be at least 1",
    ):
        CandidatePhraseExtractor(max_tokens=0)