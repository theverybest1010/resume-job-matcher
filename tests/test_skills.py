from resume_matcher.skills import Skill, load_esco_skills


def test_load_esco_skills_parses_aliases_and_removes_duplicates(tmp_path):
    csv_path = tmp_path / "skills.csv"

    csv_path.write_text(
        "conceptUri,preferredLabel,altLabels,skillType\n"
        'skill-1,Data Analysis,"Data Analytics\nAnalyzing Data",skill/competence\n'
        'skill-1,Data Analysis,"Data Analytics\nAnalyzing Data",skill/competence\n',
        encoding="utf-8",
    )

    skills = load_esco_skills(csv_path)

    assert skills == [
        Skill(
            uri="skill-1",
            preferred_label="Data Analysis",
            aliases=("Data Analytics", "Analyzing Data"),
            skill_type="skill/competence",
        )
    ]

    assert skills[0].labels == (
        "Data Analysis",
        "Data Analytics",
        "Analyzing Data",
    )