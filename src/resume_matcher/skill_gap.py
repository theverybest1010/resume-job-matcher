from collections.abc import Sequence
from dataclasses import dataclass

from resume_matcher.skills import Skill


# Stores the result of comparing résumé skills with job-description skills.
@dataclass(frozen=True)
class SkillGapReport:
    # Job skills also found in the résumé.
    matched_skills: tuple[Skill, ...]

    # Job skills not found in the résumé.
    missing_skills: tuple[Skill, ...]

    # Résumé skills that were not detected in the job description.
    additional_skills: tuple[Skill, ...]

    # Percentage of job skills covered by the résumé.
    match_percentage: float


def _unique_skills(
    skills: Sequence[Skill],
) -> dict[str, Skill]:
    """Remove duplicate skills using their ESCO URI."""

    unique_skills: dict[str, Skill] = {}

    for skill in skills:
        # Keep the first occurrence of each ESCO skill.
        #
        # A skill may appear multiple times in a résumé or job description,
        # but it should only count once toward the final percentage.
        if skill.uri not in unique_skills:
            unique_skills[skill.uri] = skill

    return unique_skills


def compare_skills(
    resume_skills: Sequence[Skill],
    job_skills: Sequence[Skill],
) -> SkillGapReport:
    """Compare résumé skills with job-description skills."""

    # Remove duplicate mentions of the same ESCO skill.
    resume_by_uri = _unique_skills(resume_skills)
    job_by_uri = _unique_skills(job_skills)

    # Find job skills that are also present in the résumé.
    #
    # Skills are compared using their ESCO URI instead of their label.
    # This allows aliases for the same skill to be treated as one skill.
    matched_skills = tuple(
        skill
        for uri, skill in job_by_uri.items()
        if uri in resume_by_uri
    )

    # Find job skills that were not found in the résumé.
    # These are the candidate's skill gaps.
    missing_skills = tuple(
        skill
        for uri, skill in job_by_uri.items()
        if uri not in resume_by_uri
    )

    # Find résumé skills that were not detected in the job description.
    # These skills may still be useful, but they are not part of the
    # detected job requirements.
    additional_skills = tuple(
        skill
        for uri, skill in resume_by_uri.items()
        if uri not in job_by_uri
    )

    # Calculate the percentage of job skills covered by the résumé.
    #
    # Formula:
    # matched job skills / total job skills * 100
    #
    # If no job skills were detected, return 0% to avoid division by zero.
    if job_by_uri:
        match_percentage = (
            len(matched_skills) / len(job_by_uri)
        ) * 100
    else:
        match_percentage = 0.0

    # Package all comparison results into one immutable report.
    return SkillGapReport(
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        additional_skills=additional_skills,
        match_percentage=match_percentage,
    )