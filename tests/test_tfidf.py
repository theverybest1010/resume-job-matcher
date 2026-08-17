import pytest

from resume_matcher.tfidf import tfidf_similarity


def test_tfidf_similarity_reflects_text_overlap():
    identical = tfidf_similarity("Python Git", "Python Git")
    partial = tfidf_similarity("Python Git", "Python SQL")
    unrelated = tfidf_similarity("Python Git", "Java SQL")

    assert identical == pytest.approx(1.0)
    assert 0.0 < partial < identical
    assert unrelated == pytest.approx(0.0)

def test_tfidf_similarity_rejects_empty_input():
    with pytest.raises(ValueError):
        tfidf_similarity("", "Python developer")

    with pytest.raises(ValueError):
        tfidf_similarity("Python developer", "   ")