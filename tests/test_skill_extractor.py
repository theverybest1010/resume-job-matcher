from resume_matcher.skill_extractor import ExactSkillExtractor
from resume_matcher.skills import Skill
from resume_matcher.alias_rules import AliasRule
import pytest


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


def test_reviewed_aliases_connect_oop_without_changing_the_catalog():
    skill = Skill("test:oop", "use object-oriented programming", (), "skill/competence")
    text = "OOP; object oriented programming; object-oriented programming."
    mentions = ExactSkillExtractor([skill]).extract(text)
    assert [m.matched_text for m in mentions] == [
        "OOP", "object oriented programming", "object-oriented programming",
    ]
    assert all(m.skill == skill for m in mentions)
    assert all(text[m.start_char:m.end_char] == m.matched_text for m in mentions)
    assert skill.aliases == ()


def test_blocks_only_the_reviewed_ambiguous_alias():
    creativity = Skill(
        "test:creativity", "think creatively", ("design", "creative thinking"), "skill/competence",
    )
    extractor = ExactSkillExtractor([creativity])
    assert extractor.extract("Object Oriented Design") == []
    assert [m.skill for m in extractor.extract("creative thinking")] == [creativity]
    assert [m.skill for m in extractor.extract("think creatively")] == [creativity]

    # A genuine preferred label for another concept is unaffected.
    design = Skill("test:design", "design", (), "knowledge")
    mentions = ExactSkillExtractor([creativity, design]).extract("Design")
    assert [m.skill for m in mentions] == [design]


def test_alias_rules_support_other_domains_and_can_be_disabled():
    skill = Skill("test:cpr", "perform cardiopulmonary resuscitation", (), "skill/competence")
    rule = AliasRule(skill.preferred_label, "CPR", "add", "Reviewed abbreviation.")
    assert [m.skill for m in ExactSkillExtractor([skill], alias_rules=[rule]).extract("CPR")] == [skill]
    assert ExactSkillExtractor([skill], alias_rules=[]).extract("CPR") == []


def test_abstains_when_an_alias_has_multiple_unresolved_meanings():
    health = Skill("test:health", "medical screening", ("screening",), "skill/competence")
    film = Skill("test:film", "screen films", ("screening",), "skill/competence")
    assert ExactSkillExtractor([health, film]).extract("screening") == []


def test_rejects_alias_rule_target_with_multiple_concept_uris():
    skills = [Skill(uri, "shared label", (), "knowledge") for uri in ("test:a", "test:b")]
    with pytest.raises(ValueError, match="target is ambiguous"):
        ExactSkillExtractor(skills, alias_rules=[AliasRule("shared label", "short name", "add")])
