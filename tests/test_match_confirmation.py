from types import SimpleNamespace

import pytest
import spacy

from resume_matcher.match_confirmation import GrammaticalMatchVerifier
from resume_matcher.hybrid_extractor import HybridSkillExtractor, HybridSkillMention
from resume_matcher.matching_pipeline import MatchingPipeline
from resume_matcher.semantic_matcher import SemanticSkillMatch
from resume_matcher.skills import Skill


@pytest.fixture(scope='module')
def nlp():
    return spacy.load('en_core_web_sm')


@pytest.mark.parametrize('phrase,label,expected', [
    ('maintained industrial equipment', 'maintain industrial equipment', True),
    ('Created financial reports', 'create a financial report', True),
    ('Repaired hydraulic pumps', 'operate hydraulic pumps', False),
    ('Business Administration', 'office administration', False),
    ('did not maintain industrial equipment', 'maintain industrial equipment', False),
    ('maintain no industrial equipment', 'maintain industrial equipment', False),
    ('maintain medical equipment', 'maintain industrial equipment', False),
    ('maintain industrial equipment safely', 'maintain industrial equipment', False),
])
def test_conservative_grammatical_equivalence(nlp, phrase, label, expected):
    assert GrammaticalMatchVerifier(nlp).confirms(phrase, label) is expected


def test_confirmed_evidence_beats_stronger_suggestion(nlp):
    skill = Skill('equipment', 'maintain industrial equipment', (), 'skill/competence')
    for phrases, scores in [
        (['repair industrial equipment', 'maintained industrial equipment'], [.99, .8]),
        (['maintained industrial equipment', 'repair industrial equipment'], [.8, .99]),
    ]:
        extractor = HybridSkillExtractor(
            SimpleNamespace(extract=lambda text: []),
            SimpleNamespace(nlp=nlp, extract=lambda text: phrases),
            SimpleNamespace(match_many=lambda *args, **kwargs: [
                [SemanticSkillMatch(skill, score)] for score in scores
            ]),
        )
        result = extractor.extract('example')
        assert len(result) == 1
        assert result[0].is_confirmed
        assert result[0].source == 'grammatical'
        assert result[0].matched_text == 'maintained industrial equipment'


def test_suggestions_do_not_inflate_numerator_or_denominator():
    skills = [Skill(str(i), name, (), 'knowledge') for i, name in enumerate(
        ['Python', 'SQL', 'office administration'])]
    def mention(i, source):
        return HybridSkillMention(skills[i], skills[i].preferred_label, source, .9)
    results = {
        'resume Python': [mention(0, 'exact'), mention(1, 'semantic'), mention(2, 'semantic')],
        'job Python SQL': [mention(0, 'exact'), mention(1, 'grammatical'), mention(2, 'semantic')],
        'job suggestions only': [mention(2, 'semantic')],
    }
    pipeline = MatchingPipeline(SimpleNamespace(extract=lambda text: results[text]))
    report = pipeline.analyze('resume Python', 'job Python SQL')
    assert report.skill_gap.match_percentage == 50
    assert report.skill_gap.matched_skills == (skills[0],)
    assert report.skill_gap.missing_skills == (skills[1],)
    assert len(report.resume_suggestions) == 2
    assert len(report.job_suggestions) == 1
    assert report.has_confirmed_job_skills
    empty = pipeline.analyze('resume Python', 'job suggestions only')
    assert not empty.has_confirmed_job_skills
    assert empty.skill_gap.matched_skills == ()
