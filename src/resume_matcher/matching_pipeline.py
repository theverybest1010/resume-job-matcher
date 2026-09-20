from dataclasses import dataclass
from pathlib import Path

from resume_matcher.document_loader import extract_document_text
from resume_matcher.hybrid_extractor import (
    HybridSkillExtractor,
    HybridSkillMention,
)
from resume_matcher.skill_gap import SkillGapReport, compare_skills
from resume_matcher.tfidf import (
    tfidf_similarity as calculate_tfidf_similarity,
)


@dataclass(frozen=True)
class ResumeJobMatchReport:
    """Store the results of comparing a résumé with a job description."""

    resume_mentions: tuple[HybridSkillMention, ...]
    job_mentions: tuple[HybridSkillMention, ...]
    skill_gap: SkillGapReport
    tfidf_similarity: float


class MatchingPipeline:
    """Combine skill extraction, skill comparison, and text similarity."""

    def __init__(
        self,
        skill_extractor: HybridSkillExtractor,
    ) -> None:
        # Reuse the supplied extractor and its already-loaded models.
        self.skill_extractor = skill_extractor

    def analyze(
        self,
        resume_text: str,
        job_text: str,
    ) -> ResumeJobMatchReport:
        """Compare résumé and job description text."""

        # 1. Remove surrounding whitespace and reject empty input.
        resume_text = resume_text.strip()
        job_text = job_text.strip()

        if not resume_text:
            raise ValueError("Resume text must not be empty.")

        if not job_text:
            raise ValueError("Job description must not be empty.")

        # 2. Detect skills using exact and semantic matching.
        resume_mentions = tuple(
            self.skill_extractor.extract(resume_text)
        )
        job_mentions = tuple(
            self.skill_extractor.extract(job_text)
        )

        # 3. Compare the detected skills by their ESCO identifiers.
        #    This produces matched, missing, and additional skills.
        skill_gap = compare_skills(
            resume_skills=[
                mention.skill for mention in resume_mentions
            ],
            job_skills=[
                mention.skill for mention in job_mentions
            ],
        )

        # 4. Calculate TF-IDF similarity between the full texts.
        #    Keep this separate from detected skill coverage.
        document_similarity = calculate_tfidf_similarity(
            resume_text,
            job_text,
        )

        # 5. Package both sets of mentions and comparison results.
        return ResumeJobMatchReport(
            resume_mentions=resume_mentions,
            job_mentions=job_mentions,
            skill_gap=skill_gap,
            tfidf_similarity=document_similarity,
        )

    def analyze_documents(
        self,
        resume_path: str | Path,
        job_path: str | Path,
    ) -> ResumeJobMatchReport:
        """Read TXT, PDF, or DOCX documents and compare their text."""

        # 1. Extract readable text from each document.
        #    The document loader handles file validation and errors.
        resume_text = extract_document_text(resume_path)
        job_text = extract_document_text(job_path)

        # 2. Pass the extracted text through our existing analysis.
        return self.analyze(
            resume_text=resume_text,
            job_text=job_text,
        )