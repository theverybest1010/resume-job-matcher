"""Targeted development checks, not an overall accuracy benchmark.

Run from the repository root:
    python scripts/evaluate_skill_extraction.py

Exit codes: 0 = all specified checks pass; 1 = a check fails;
2 = configuration/catalog error. Other predictions remain ungraded.
"""
import argparse
from dataclasses import dataclass


@dataclass(frozen=True)
class Case:
    name: str
    text: str
    required: tuple[str, ...] = ()
    forbidden: tuple[str, ...] = ()
    review_note: str = ""


CASES = (
    Case(
        "software",
        "Programming Languages: Python, C\n"
        "Experienced in data structures and object-oriented programming.",
        required=("Python (computer programming)", "C (programming language)",
                  "data structures", "use object-oriented programming"),
    ),
    Case(
        "healthcare-review",
        "Provided medical care to hospital patients.",
        review_note="Review specificity: the text does not establish general medical practice.",
    ),
    Case(
        "finance",
        "Created financial reports and prepared budgets.",
        required=("create a financial report",),
        review_note="Budget preparation versus budget management remains ungraded pending review.",
    ),
    Case(
        "maintenance",
        "Repaired hydraulic pumps and maintained industrial equipment.",
        required=("maintain industrial equipment",),
        forbidden=("operate hydraulic pumps",),
        review_note="Review pumps -> manufacturing plant equipment separately; repair is not operation.",
    ),
    Case(
        "vitamin-c",
        "Advised patients about vitamin C.",
        forbidden=("C (programming language)",),
    ),
    Case(
        "business-degree",
        "Bachelor's degree in Business Administration.",
        forbidden=("office administration",),
    ),
    Case(
        "business-short-phrase",
        "Business Administration",
        forbidden=("office administration",),
    ),
    Case(
        "pump-operation-positive-control",
        "operate hydraulic pumps",
        required=("operate hydraulic pumps",),
        review_note="Preserve valid operation matches when correcting repair false positives.",
    ),
)


def resolve_targets(skills, cases=CASES):
    """Resolve readable labels to unique catalog IDs; never silently skip a target."""
    by_label = {}
    for skill in skills:
        by_label.setdefault(skill.preferred_label, set()).add(skill.uri)
    targets = {label for case in cases for label in (*case.required, *case.forbidden)}
    result = {}
    for label in sorted(targets):
        uris = by_label.get(label, set())
        if len(uris) != 1:
            raise ValueError(f"Evaluation target {label!r} resolves to {len(uris)} IDs; review the catalog.")
        result[label] = next(iter(uris))
    return result


def check_case(case, mentions, targets):
    """Grade only explicitly annotated requirements, comparing skill IDs."""
    detected = {mention.skill.uri for mention in mentions if mention.is_confirmed}
    missing = [label for label in case.required if targets[label] not in detected]
    unwanted = [label for label in case.forbidden if targets[label] in detected]
    return missing, unwanted


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--esco', default='data/raw/esco/skills_en.csv')
    args = parser.parse_args()

    # Keep heavy imports here so reviewing/checking evaluation logic needs no model.
    from resume_matcher.skill_catalog import load_skill_catalog
    from resume_matcher.skill_extractor import ExactSkillExtractor
    from resume_matcher.candidate_phrases import CandidatePhraseExtractor
    from resume_matcher.semantic_matcher import SemanticSkillMatcher, DEFAULT_MODEL_NAME
    from resume_matcher.hybrid_extractor import HybridSkillExtractor

    skills = load_skill_catalog(args.esco)
    try:
        targets = resolve_targets(skills)
    except ValueError as error:
        parser.error(str(error))

    print('Catalog size:', len(skills))
    print('Model:', DEFAULT_MODEL_NAME)
    print('Minimum semantic score: 0.75')
    extractor = HybridSkillExtractor(
        exact_extractor=ExactSkillExtractor(skills),
        candidate_extractor=CandidatePhraseExtractor(),
        semantic_matcher=SemanticSkillMatcher(skills),
        min_semantic_score=0.75,
    )

    passed = failed = review_only = 0
    for case in CASES:
        mentions = extractor.extract(case.text)
        missing, unwanted = check_case(case, mentions, targets)
        if not case.required and not case.forbidden:
            status = 'REVIEW ONLY'
            review_only += 1
        elif missing or unwanted:
            status = 'FAIL'
            failed += 1
        else:
            status = 'PASS'
            passed += 1
        print(f'\n[{status}] {case.name}\nText: {case.text}')
        for mention in mentions:
            print(f'  {"CONFIRMED" if mention.is_confirmed else "SUGGESTION"} '
                  f'{mention.source} {mention.score:.3f} '
                  f'{mention.matched_text!r} -> {mention.skill.preferred_label}')
        if not mentions:
            print('  No skills detected.')
        for label in missing:
            print('  REQUIRED BUT MISSING:', label)
        for label in unwanted:
            print('  FORBIDDEN MATCH:', label)
        if case.review_note:
            print('  REVIEW:', case.review_note)

    print(f'\nTargeted cases: {passed} passed, {failed} failed; {review_only} review-only.')
    print('PASS covers listed confirmed-match requirements only; suggestions do not count.')
    print('Other predictions are ungraded. Suggestions may still be incorrect.')
    print('These development examples do not estimate overall precision or recall.')
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
