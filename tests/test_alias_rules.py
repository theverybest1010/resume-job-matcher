import pytest

from resume_matcher.alias_rules import load_alias_rules
from resume_matcher.skill_extractor import ExactSkillExtractor
from resume_matcher.skills import Skill


def test_custom_csv_rules_apply_to_the_requested_concept(tmp_path):
    path = tmp_path / "rules.csv"
    path.write_text(
        "preferredLabel,alias,action,reason\n"
        "prepare financial statements,financial reporting,add,Reviewed wording\n",
        encoding="utf-8-sig",
    )
    skill = Skill("test:finance", "prepare financial statements", (), "skill/competence")
    extractor = ExactSkillExtractor([skill], alias_rules=load_alias_rules(path))
    assert [m.skill for m in extractor.extract("financial reporting")] == [skill]


@pytest.mark.parametrize("contents", [
    "preferredLabel,alias\nlabel,alias\n",
    "preferredLabel,alias,action,reason\nlabel,alias,unknown,reason\n",
])
def test_invalid_rule_files_fail_explicitly(tmp_path, contents):
    path = tmp_path / "rules.csv"
    path.write_text(contents, encoding="utf-8")
    with pytest.raises(ValueError):
        load_alias_rules(path)
