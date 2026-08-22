import numpy as np
import pytest

from resume_matcher.semantic_matcher import SemanticSkillMatcher
from resume_matcher.skills import Skill


# A tiny fake embedding model used only during testing.
# This prevents pytest from downloading or running the real AI model.
class FakeModel:
    def __init__(self, *args: object, **kwargs: object) -> None:
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


def test_requires_at_least_one_skill() -> None:
    with pytest.raises(
        ValueError,
        match="At least one skill is required",
    ):
        SemanticSkillMatcher([])


def test_match_returns_closest_skill(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Replace the real model with our fast fake model.
    monkeypatch.setattr(
        "resume_matcher.semantic_matcher.SentenceTransformer",
        FakeModel,
    )

    skills = [
        Skill(
            uri="patient-care",
            preferred_label="patient care",
            aliases=(),
            skill_type="skill/competence",
        ),
        Skill(
            uri="software-development",
            preferred_label="software development",
            aliases=(),
            skill_type="skill/competence",
        ),
    ]

    matcher = SemanticSkillMatcher(skills)

    matches = matcher.match(
        "caring for patients",
        top_k=2,
        min_score=0.8,
    )

    assert len(matches) == 1
    assert matches[0].skill.preferred_label == "patient care"
    assert matches[0].score > 0.9