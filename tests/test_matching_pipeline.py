import pytest

from resume_matcher.hybrid_extractor import HybridSkillMention
from resume_matcher.matching_pipeline import MatchingPipeline
from resume_matcher.skills import Skill


class FakeHybridSkillExtractor:
    """Return predetermined skills without loading NLP models."""

    def __init__(
        self,
        results_by_text: dict[
            str,
            list[HybridSkillMention],
        ],
    ) -> None:
        self.results_by_text = results_by_text

    def extract(
        self,
        text: str,
    ) -> list[HybridSkillMention]:
        return self.results_by_text.get(text, [])


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


def make_mention(
    skill: Skill,
    matched_text: str,
) -> HybridSkillMention:
    return HybridSkillMention(
        skill=skill,
        matched_text=matched_text,
        source="exact",
        score=1.0,
    )


def test_analyze_creates_complete_match_report() -> None:
    python = make_skill("skill-python", "Python")
    java = make_skill("skill-java", "Java")
    machine_learning = make_skill(
        "skill-machine-learning",
        "machine learning",
    )

    resume_text = "Python and Java development"
    job_text = "Python and machine learning"

    resume_mentions = [
        make_mention(python, "Python"),
        make_mention(java, "Java"),
    ]

    job_mentions = [
        make_mention(python, "Python"),
        make_mention(
            machine_learning,
            "machine learning",
        ),
    ]

    skill_extractor = FakeHybridSkillExtractor(
        {
            resume_text: resume_mentions,
            job_text: job_mentions,
        }
    )

    pipeline = MatchingPipeline(skill_extractor)

    report = pipeline.analyze(
        resume_text,
        job_text,
    )

    assert report.resume_mentions == tuple(resume_mentions)
    assert report.job_mentions == tuple(job_mentions)

    assert report.skill_gap.matched_skills == (python,)
    assert report.skill_gap.missing_skills == (
        machine_learning,
    )
    assert report.skill_gap.additional_skills == (java,)
    assert report.skill_gap.match_percentage == 50.0

    assert 0.0 < report.tfidf_similarity <= 1.0


@pytest.mark.parametrize(
    ("resume_text", "job_text", "expected_message"),
    [
        (
            "",
            "Python developer",
            "Resume text must not be empty",
        ),
        (
            "Python developer",
            "   ",
            "Job description must not be empty",
        ),
    ],
)
def test_analyze_rejects_empty_documents(
    resume_text: str,
    job_text: str,
    expected_message: str,
) -> None:
    pipeline = MatchingPipeline(
        FakeHybridSkillExtractor({})
    )

    with pytest.raises(
        ValueError,
        match=expected_message,
    ):
        pipeline.analyze(
            resume_text,
            job_text,
        )