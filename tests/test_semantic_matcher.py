import numpy as np
import pytest

from resume_matcher.semantic_matcher import SemanticSkillMatcher
from resume_matcher.skills import Skill


# A tiny fake embedding model used only during testing.
# This prevents pytest from downloading or running the real AI model.
class FakeModel:
    def __init__(
        self,
        *args: object,
        **kwargs: object,
    ) -> None:
        pass

    def encode(
        self,
        texts: list[str],
        **kwargs: object,
    ) -> np.ndarray:
        vectors = {
            "patient care": [1.0, 0.0],
            "software development": [0.0, 1.0],
            "caring for patients": [0.9, 0.1],
        }

        return np.array(
            [vectors[text] for text in texts],
            dtype=float,
        )


def make_skill(
    uri: str,
    label: str,
) -> Skill:
    """Create a small ESCO-style skill for testing."""

    return Skill(
        uri=uri,
        preferred_label=label,
        aliases=(),
        skill_type="skill/competence",
    )


def test_requires_at_least_one_skill() -> None:
    with pytest.raises(
        ValueError,
        match="At least one skill is required",
    ):
        SemanticSkillMatcher([])


def test_match_returns_closest_skill(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Replace the real model with the fast fake model.
    monkeypatch.setattr(
        "resume_matcher.semantic_matcher.SentenceTransformer",
        FakeModel,
    )

    patient_care = make_skill(
        "patient-care",
        "patient care",
    )

    software_development = make_skill(
        "software-development",
        "software development",
    )

    matcher = SemanticSkillMatcher(
        [
            patient_care,
            software_development,
        ]
    )

    matches = matcher.match(
        "caring for patients",
        top_k=2,
        min_score=0.8,
    )

    assert len(matches) == 1
    assert matches[0].skill == patient_care
    assert matches[0].score > 0.9


def test_match_many_preserves_phrase_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Replace the real model with the fast fake model.
    monkeypatch.setattr(
        "resume_matcher.semantic_matcher.SentenceTransformer",
        FakeModel,
    )

    patient_care = make_skill(
        "patient-care",
        "patient care",
    )

    software_development = make_skill(
        "software-development",
        "software development",
    )

    matcher = SemanticSkillMatcher(
        [
            patient_care,
            software_development,
        ]
    )

    # Match both phrases in one model batch.
    results = matcher.match_many(
        [
            "caring for patients",
            "software development",
        ],
        top_k=1,
        min_score=0.8,
    )

    # Each output position must correspond to the same input position.
    assert len(results) == 2
    assert results[0][0].skill == patient_care
    assert results[1][0].skill == software_development