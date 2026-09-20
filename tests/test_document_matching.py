from pathlib import Path

from docx import Document

from resume_matcher.hybrid_extractor import HybridSkillMention
from resume_matcher.matching_pipeline import MatchingPipeline
from resume_matcher.skills import Skill


def test_analyzes_txt_resume_and_docx_job(tmp_path: Path) -> None:
    # Use a small skill catalog so the test stays fast.
    python_skill = Skill(
        uri="test:python",
        preferred_label="Python",
        aliases=(),
        skill_type="knowledge",
    )
    machine_learning_skill = Skill(
        uri="test:machine-learning",
        preferred_label="machine learning",
        aliases=(),
        skill_type="knowledge",
    )

    # This test focuses on document loading and pipeline integration.
    # A predictable extractor avoids loading the embedding model.
    class FakeSkillExtractor:
        def extract(self, text: str) -> list[HybridSkillMention]:
            return [
                HybridSkillMention(
                    skill=skill,
                    matched_text=skill.preferred_label,
                    source="exact",
                    score=1.0,
                )
                for skill in (python_skill, machine_learning_skill)
                if skill.preferred_label in text
            ]

    # Create an actual TXT résumé in pytest's temporary directory.
    resume_path = tmp_path / "resume.txt"
    resume_path.write_text(
        "Experience with Python.",
        encoding="utf-8",
    )

    # Create an actual DOCX job description.
    job_path = tmp_path / "job.docx"
    document = Document()
    document.add_paragraph(
        "Experience with Python and machine learning."
    )
    document.save(job_path)

    # Read both documents and generate the matching report.
    pipeline = MatchingPipeline(
        skill_extractor=FakeSkillExtractor(),
    )
    report = pipeline.analyze_documents(resume_path, job_path)

    # Python appears in both; machine learning appears only in the job.
    assert report.skill_gap.matched_skills == (python_skill,)
    assert report.skill_gap.missing_skills == (
        machine_learning_skill,
    )
    assert report.skill_gap.additional_skills == ()
    assert report.skill_gap.match_percentage == 50.0

    # The documents share words but are not identical.
    assert 0.0 < report.tfidf_similarity < 1.0