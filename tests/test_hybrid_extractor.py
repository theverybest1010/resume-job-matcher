from collections.abc import Sequence
from dataclasses import dataclass

import pytest

from resume_matcher.hybrid_extractor import (
    HybridSkillExtractor,
    HybridSkillMention,
)
from resume_matcher.semantic_matcher import SemanticSkillMatch
from resume_matcher.skills import Skill


@dataclass(frozen=True)
class FakeExactMention:
    skill: Skill
    matched_text: str


class FakeExactExtractor:
    def __init__(
        self,
        mentions: list[FakeExactMention],
    ) -> None:
        self.mentions = mentions

    def extract(
        self,
        text: str,
    ) -> list[FakeExactMention]:
        return self.mentions


class FakeCandidateExtractor:
    def __init__(
        self,
        phrases: list[str],
    ) -> None:
        self.phrases = phrases

    def extract(
        self,
        text: str,
    ) -> list[str]:
        return self.phrases


class FakeSemanticMatcher:
    def __init__(
        self,
        results: list[list[SemanticSkillMatch]],
    ) -> None:
        self.results = results

    def match_many(
        self,
        phrases: Sequence[str],
        top_k: int,
        min_score: float,
    ) -> list[list[SemanticSkillMatch]]:
        return self.results


def make_skill(
    uri: str,
    label: str,
) -> Skill:
    return Skill(
        uri=uri,
        preferred_label=label,
        aliases=(),
        skill_type="skill/competence",
    )


def test_combines_exact_and_semantic_matches() -> None:
    python = make_skill("skill-python", "Python")
    patient_care = make_skill(
        "skill-patient-care",
        "patient care",
    )

    exact_extractor = FakeExactExtractor(
        mentions=[
            FakeExactMention(
                skill=python,
                matched_text="Python",
            )
        ]
    )

    candidate_extractor = FakeCandidateExtractor(
        phrases=[
            "developed Python applications",
            "provided medical care",
            "unrelated phrase",
        ]
    )

    semantic_matcher = FakeSemanticMatcher(
        results=[
            # This duplicates the exact Python match and should be ignored.
            [
                SemanticSkillMatch(
                    skill=python,
                    score=0.92,
                )
            ],
            # This new semantic skill should be included.
            [
                SemanticSkillMatch(
                    skill=patient_care,
                    score=0.84,
                )
            ],
            # This phrase did not pass the semantic threshold.
            [],
        ]
    )

    extractor = HybridSkillExtractor(
        exact_extractor=exact_extractor,
        candidate_extractor=candidate_extractor,
        semantic_matcher=semantic_matcher,
        min_semantic_score=0.75,
    )

    results = extractor.extract(
        "Experienced with Python and providing medical care."
    )

    assert results == [
        HybridSkillMention(
            skill=python,
            matched_text="Python",
            source="exact",
            score=1.0,
        ),
        HybridSkillMention(
            skill=patient_care,
            matched_text="provided medical care",
            source="semantic",
            score=0.84,
        ),
    ]


def test_rejects_invalid_semantic_threshold() -> None:
    with pytest.raises(
        ValueError,
        match="min_semantic_score must be between",
    ):
        HybridSkillExtractor(
            exact_extractor=FakeExactExtractor([]),
            candidate_extractor=FakeCandidateExtractor([]),
            semantic_matcher=FakeSemanticMatcher([]),
            min_semantic_score=1.1,
        )