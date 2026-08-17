from resume_matcher.skill_extractor import ExactSkillExtractor
from resume_matcher.skills import Skill


def test_exact_skill_extractor_finds_aliases_and_positions():
    skills = [
        Skill(
            uri="skill-1",
            preferred_label="data analysis",
            aliases=("data analytics",),
            skill_type="skill/competence",
        ),
        Skill(
            uri="skill-2",
            preferred_label="patient care",
            aliases=("care for patients",),
            skill_type="skill/competence",
        ),
    ]

    extractor = ExactSkillExtractor(skills)
    text = "Used DATA ANALYTICS to improve patient care."

    mentions = extractor.extract(text)

    detected = {
        (mention.skill.uri, mention.matched_text)
        for mention in mentions
    }

    assert detected == {
        ("skill-1", "DATA ANALYTICS"),
        ("skill-2", "patient care"),
    }

    assert all(
        text[mention.start_char : mention.end_char]
        == mention.matched_text
        for mention in mentions
    )
def test_exact_skill_extractor_prefers_canonical_label():
    skills = [
        Skill(
            uri="skill-project-management",
            preferred_label="project management",
            aliases=(),
            skill_type="skill/competence",
        ),
        Skill(
            uri="skill-project-commissioning",
            preferred_label="project commissioning",
            aliases=("project management",),
            skill_type="skill/competence",
        ),
    ]

    extractor = ExactSkillExtractor(skills)
    mentions = extractor.extract("Experienced in project management.")

    assert len(mentions) == 1
    assert mentions[0].skill.uri == "skill-project-management"