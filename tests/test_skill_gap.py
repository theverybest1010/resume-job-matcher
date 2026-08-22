import pytest

from resume_matcher.skill_gap import compare_skills
from resume_matcher.skills import Skill


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


def test_compare_skills_creates_skill_gap_report() -> None:
    python = make_skill("skill-python", "Python")
    machine_learning = make_skill(
        "skill-machine-learning",
        "machine learning",
    )
    project_management = make_skill(
        "skill-project-management",
        "project management",
    )
    java = make_skill("skill-java", "Java")

    # Python is included twice to verify that duplicates only count once.
    resume_skills = [
        python,
        python,
        project_management,
        java,
    ]

    job_skills = [
        python,
        machine_learning,
        project_management,
    ]

    report = compare_skills(
        resume_skills,
        job_skills,
    )

    assert report.matched_skills == (
        python,
        project_management,
    )

    assert report.missing_skills == (
        machine_learning,
    )

    assert report.additional_skills == (
        java,
    )

    assert report.match_percentage == pytest.approx(
        66.6667,
        rel=1e-4,
    )


def test_compare_skills_handles_no_job_skills() -> None:
    python = make_skill("skill-python", "Python")

    report = compare_skills(
        resume_skills=[python],
        job_skills=[],
    )

    assert report.matched_skills == ()
    assert report.missing_skills == ()
    assert report.additional_skills == (python,)
    assert report.match_percentage == 0.0