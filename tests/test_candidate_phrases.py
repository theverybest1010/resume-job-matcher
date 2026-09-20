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


@pytest.mark.parametrize("text", [
    "Management. Systems. Machines. Technologies.",
    "apply technical skills",
    "Use my strong professional abilities.",
    "Programming Languages: Java, Python, C++. Tools & Technologies: Git, Linux.",
])
def test_rejects_fragments_and_generic_ability_claims(extractor, text):
    assert extractor.extract(text) == []


def test_preserves_specific_phrases_across_fields(extractor):
    assert extractor.extract(
        "Performed wound care. Prepared financial reports. Repaired hydraulic pumps."
    ) == [
        "Performed wound care",
        "Prepared financial reports",
        "Repaired hydraulic pumps",
    ]
    assert extractor.extract("communication skills") == ["communication skills"]
    assert extractor.extract("data structures") == ["data structures"]


def test_keeps_list_entries_separate_and_deduplicates(extractor):
    phrases = extractor.extract(
        "Object Oriented Design | Languages and Machines; object oriented design"
    )
    assert phrases == ["Object Oriented Design"]


def test_preserves_recipient_across_pdf_line_wrap(extractor):
    assert extractor.extract("Provided medical care to\nhospital patients.") == [
        "Provided medical care to\nhospital patients",
    ]
