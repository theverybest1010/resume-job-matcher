# Supplementary skills

The ESCO source CSV stays unchanged. `load_skill_catalog(esco_path)` loads ESCO
and then packaged `src/resume_matcher/data/supplemental_skills.csv`.
`load_esco_skills` still loads only ESCO. Use the combined loader when building
both ExactSkillExtractor and SemanticSkillMatcher.

This supplement adds HTML, data structures, and C (programming language), each
with a project-owned `urn:resume-job-matcher:skill:...` identifier. They are not
ESCO concepts. The supplied export has 13,939 unique ESCO concepts; combined
with these three, the catalog has 13,942.

To run the complete pipeline from the repository root:

```bash
python scripts/match_documents.py data/local/resume.pdf data/local/job.txt --show-evidence
```

## Editing the supplement

Each CSV row defines uri, preferredLabel, pipe-separated aliases, skillType,
pipe-separated contextualAliases and contextHeadings, semanticMatching (true or
false), optional replacesAliasFrom and replacesAlias, and a review reason.
New concepts may come from any profession. Review semantic equivalence before
adding an alias; a related concept is not necessarily the same skill.
`load_skill_catalog(esco_path, supplemental_path)` uses a custom supplement
instead of the bundled one. Duplicate identifiers are rejected.

For HTML, the specific `use HTML` alias is reassigned in memory from the broader
ESCO concept `use markup languages`. Other aliases (including `use XHTML`) and
the ESCO canonical label remain. The source CSV is never rewritten. A transfer
whose source URI is absent does nothing, allowing small catalogs and different
ESCO exports; review these rules when upgrading datasets.

## Conservative C policy

Qualified aliases such as `C programming` and `programming in C` match directly.
Bare C matches only as a whole comma, semicolon, slash, or pipe-separated item
on a line headed `Programming Languages:` or `Coding Languages:`. It does not
match `vitamin C`, `C++`, `C#`, or `Objective-C`. Unlabeled or wrapped lists may
be missed. This is a deliberately limited rule, not full language understanding.

C is excluded from semantic matching so embeddings cannot bypass its evidence
requirement. HTML and data structures are available to both matchers. Similarity
scores are not probabilities; semantic false positives remain possible. No
negation or proficiency inference is introduced. Match percentages describe
coverage of detected skills, not suitability for hiring.

The previous Business Administration -> office administration semantic mapping
is not corrected by this change. Inspect real-document evidence after installing.
