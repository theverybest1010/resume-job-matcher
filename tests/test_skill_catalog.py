import csv

import pytest

from resume_matcher.skill_catalog import load_skill_catalog
from resume_matcher.skills import load_esco_skills
from resume_matcher.skill_extractor import ExactSkillExtractor
from resume_matcher.semantic_matcher import SemanticSkillMatcher


@pytest.fixture
def catalog(tmp_path):
    path = tmp_path / 'esco.csv'
    with path.open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['conceptUri', 'preferredLabel', 'altLabels', 'skillType'])
        writer.writerow(['http://data.europa.eu/esco/skill/0af062de-eb43-41e9-9b96-249e2cd22d26',
                         'use markup languages', 'use HTML\nuse html\nuse XHTML', 'skill/competence'])
    return path, load_skill_catalog(path)


def test_supplement_adds_distinct_concepts_without_changing_esco(catalog):
    path, skills = catalog
    assert len(skills) == 4
    assert 'use HTML' in load_esco_skills(path)[0].aliases
    extractor = ExactSkillExtractor(skills)
    names = {m.skill.preferred_label for m in extractor.extract('HTML, data structures; use HTML')}
    assert names == {'HTML', 'data structures'}
    assert {m.skill.preferred_label for m in extractor.extract('use XHTML')} == {'use markup languages'}


@pytest.mark.parametrize('text', [
    'Programming Languages: Java, Python, C, C++, JavaScript',
    'C programming', 'Programming in C',
])
def test_c_requires_explicit_evidence(catalog, text):
    extractor = ExactSkillExtractor(catalog[1])
    assert any(m.skill.preferred_label == 'C (programming language)' for m in extractor.extract(text))


@pytest.mark.parametrize('text', [
    'vitamin C', 'Programming Languages: vitamin C, Java',
    'C++ and C#', 'Objective-C programming', 'Objective C programming',
    'Grade C', 'C shell', 'Programming Languages: Objective-C, C++, C#',
])
def test_c_rejects_ambiguous_or_other_language_evidence(catalog, text):
    assert not ExactSkillExtractor(catalog[1]).extract(text)


def test_semantic_matching_cannot_bypass_context(catalog, monkeypatch):
    import resume_matcher.semantic_matcher as module
    def forbidden(*args, **kwargs):
        raise AssertionError('No model should be loaded for an exact-only catalog')
    monkeypatch.setattr(module, 'SentenceTransformer', forbidden)
    c = catalog[1][-1]
    matcher = SemanticSkillMatcher([c])
    assert matcher.match_many(['vitamin C', 'C programming']) == [[], []]
    with pytest.raises(ValueError):
        matcher.match(' ')


def test_semantic_embedding_indices_follow_filtered_catalog(catalog, monkeypatch):
    import torch
    import resume_matcher.semantic_matcher as module
    class Encoder:
        def __init__(self, *args, **kwargs):
            pass
        def encode(self, texts, **kwargs):
            assert 'C (programming language)' not in texts
            return torch.tensor([[1.0, 0.0] for _ in texts])
    monkeypatch.setattr(module, 'SentenceTransformer', Encoder)
    html = catalog[1][-2]
    matcher = SemanticSkillMatcher([catalog[1][-1], html])
    assert matcher.match('HTML')[0].skill.uri == html.uri


def test_custom_catalog_supports_other_fields_and_rejects_duplicate_ids(catalog, tmp_path):
    from importlib.resources import files
    with files('resume_matcher').joinpath('data/supplemental_skills.csv').open() as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames
    custom = tmp_path / 'custom.csv'
    row = dict.fromkeys(fields, '')
    row.update(uri='urn:resume-job-matcher:skill:budget-planning',
               preferredLabel='budget planning', aliases='plan budgets',
               skillType='skill/competence', semanticMatching='true',
               reason='Example project-owned finance concept.')
    def write(rows):
        with custom.open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    write([row])
    skills = load_skill_catalog(catalog[0], custom)
    assert ExactSkillExtractor(skills).extract('plan budgets')[0].skill.uri == row['uri']
    write([row, row])
    with pytest.raises(ValueError, match='Duplicate skill URI'):
        load_skill_catalog(catalog[0], custom)
