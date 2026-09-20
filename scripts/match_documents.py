"""Run from the repository root after installing the project in editable mode."""
import argparse

from resume_matcher.skill_catalog import load_skill_catalog
from resume_matcher.skill_extractor import ExactSkillExtractor
from resume_matcher.candidate_phrases import CandidatePhraseExtractor
from resume_matcher.semantic_matcher import SemanticSkillMatcher
from resume_matcher.hybrid_extractor import HybridSkillExtractor
from resume_matcher.matching_pipeline import MatchingPipeline


def main():
    parser = argparse.ArgumentParser(description='Compare resume and job documents.')
    parser.add_argument('resume')
    parser.add_argument('job')
    parser.add_argument('--esco', default='data/raw/esco/skills_en.csv')
    parser.add_argument('--show-evidence', action='store_true')
    args = parser.parse_args()
    skills = load_skill_catalog(args.esco)
    print('Loaded skills:', len(skills))
    extractor = HybridSkillExtractor(
        exact_extractor=ExactSkillExtractor(skills),
        candidate_extractor=CandidatePhraseExtractor(),
        semantic_matcher=SemanticSkillMatcher(skills),
        min_semantic_score=0.75,
    )
    report = MatchingPipeline(extractor).analyze_documents(args.resume, args.job)
    print(f'TF-IDF similarity: {report.tfidf_similarity:.1%}')
    if report.has_confirmed_job_skills:
        print(f'Confirmed skill coverage: {report.skill_gap.match_percentage:.1f}%')
    else:
        print('Confirmed skill coverage: N/A (no confirmed job skills)')
    print('Coverage excludes unreviewed semantic suggestions on both documents.')
    for heading, values in (
        ('Matched', report.skill_gap.matched_skills),
        ('Missing', report.skill_gap.missing_skills),
        ('Additional', report.skill_gap.additional_skills),
    ):
        print(f'\n{heading}:')
        for skill in values:
            print(' -', skill.preferred_label)
    for heading, mentions in (
        ('Resume suggestions - excluded from coverage', report.resume_suggestions),
        ('Job suggestions - excluded from coverage', report.job_suggestions),
    ):
        print(f'\n{heading}:')
        for mention in mentions:
            print(f' - {mention.matched_text!r} -> {mention.skill.preferred_label}'
                  f' ({mention.score:.3f})')
    if args.show_evidence:
        for heading, mentions in (('Resume', report.resume_mentions), ('Job', report.job_mentions)):
            print(f'\n{heading} evidence:')
            for mention in mentions:
                print('CONFIRMED' if mention.is_confirmed else 'SUGGESTION',
                      mention.source, f'{mention.score:.3f}', repr(mention.matched_text),
                      '->', mention.skill.preferred_label)


if __name__ == '__main__':
    main()
