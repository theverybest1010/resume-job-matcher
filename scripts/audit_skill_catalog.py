"""Inspect missing/ambiguous terms in the actual local ESCO catalog.

Run from the repository root after installing the package:
    python scripts/audit_skill_catalog.py data/raw/esco/skills_en.csv
"""

import argparse
from collections import defaultdict

from resume_matcher.alias_rules import load_alias_rules
from resume_matcher.preprocessing import tokenize
from resume_matcher.skill_extractor import ExactSkillExtractor
from resume_matcher.skills import load_esco_skills


def contains_term(label: str, term: str) -> bool:
    """Find whole token sequences while keeping C, C++, and C# distinct."""
    label_tokens = tokenize(label)
    term_tokens = tokenize(term)
    if not term_tokens:
        return False
    width = len(term_tokens)
    return any(
        label_tokens[start:start + width] == term_tokens
        for start in range(len(label_tokens) - width + 1)
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path")
    parser.add_argument(
        "--terms", nargs="+",
        default=["OOP", "object-oriented programming", "data structures", "HTML", "C", "Design"],
    )
    args = parser.parse_args()
    skills = load_esco_skills(args.csv_path)
    extractor = ExactSkillExtractor(skills)
    labels = defaultdict(list)
    canonical_labels = {skill.preferred_label.casefold() for skill in skills}
    for skill in skills:
        for label in set(skill.labels):
            labels[" ".join(label.casefold().split())].append((skill, label))

    print(f"Loaded {len(skills)} unique skills.")
    for target in sorted({rule.preferred_label for rule in load_alias_rules()}):
        print(f"Rule target {target!r}: {'present' if target.casefold() in canonical_labels else 'ABSENT'}")

    for term in args.terms:
        key = " ".join(term.casefold().split())
        print(f"\nTERM: {term!r}")
        raw_matches = labels.get(key, [])
        if raw_matches:
            for skill, label in raw_matches:
                print(f"  Raw label {label!r} -> {skill.preferred_label} | {skill.uri}")
        else:
            print("  No full preferred-label or alias match in this export.")
            nearby = [
                (skill, label) for label_key, entries in labels.items()
                if contains_term(label_key, term)
                for skill, label in entries
            ]
            for skill, label in nearby[:8]:
                print(f"  Longer label to inspect: {label!r} -> {skill.preferred_label}")
        mentions = extractor.extract(term)
        print("  Active exact matches:", [m.skill.preferred_label for m in mentions])


if __name__ == "__main__":
    main()
