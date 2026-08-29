from dataclasses import dataclass

from resume_matcher.hybrid_extractor import (
    HybridSkillExtractor,
    HybridSkillMention,
)
from resume_matcher.skill_gap import (
    SkillGapReport,
    compare_skills,
)
from resume_matcher.tfidf import (
    tfidf_similarity as calculate_tfidf_similarity,
)

@dataclass(frozen=True)
class ResumeJobMatchReport:
    """Complete analysis of a résumé and job description."""

    # Skills detected in the résumé.
    resume_mentions: tuple[HybridSkillMention, ...]

    # Skills detected in the job description.
    job_mentions: tuple[HybridSkillMention, ...]

    # Matched, missing and additional skills.
    skill_gap: SkillGapReport

    # Overall word-importance similarity from 0.0 to 1.0.
    tfidf_similarity: float

class MatchingPipeline:
    """Run the complete résumé-to-job text analysis."""

    def __init__(
        self,
        skill_extractor: HybridSkillExtractor,
    ) -> None:
        # Reuse one initialized hybrid extractor for both documents.
        self.skill_extractor = skill_extractor

    def analyze(
        self,
        resume_text: str,
        job_text: str,
    ) -> ResumeJobMatchReport:
        """Analyze a résumé against a job description."""

        resume_text = resume_text.strip()
        job_text = job_text.strip()

        # Both documents are required for a meaningful comparison.
        if not resume_text:
            raise ValueError("Resume text must not be empty.")

        if not job_text:
            raise ValueError(
                "Job description must not be empty."
            )

        # Extract canonical ESCO skills from the résumé.
        resume_mentions = tuple(
            self.skill_extractor.extract(resume_text)
        )

        # Extract canonical ESCO skills from the job description.
        job_mentions = tuple(
            self.skill_extractor.extract(job_text)
        )

        # Compare skills using their canonical ESCO URIs.
        skill_gap = compare_skills(
            resume_skills=[
                mention.skill
                for mention in resume_mentions
            ],
            job_skills=[
                mention.skill
                for mention in job_mentions
            ],
        )

        # Calculate the original TF-IDF document similarity.
        document_similarity = calculate_tfidf_similarity(
            resume_text,
            job_text,
        )

        # Package every result into one report.
        return ResumeJobMatchReport(
            resume_mentions=resume_mentions,
            job_mentions=job_mentions,
            skill_gap=skill_gap,
            tfidf_similarity=document_similarity,
        )