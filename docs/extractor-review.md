> Historical investigation: examples and validation notes reflect the work at that time, not an overall accuracy benchmark. See [current architecture](architecture.md).

# Skill extractor review and replacement files

This bundle contains complete replacement files based on the uploaded
`code-review.zip`. Apply it from the root of `resume-job-matcher` on your current
`feature/document-matching` branch. Your document-loading integration was included
in the test run.

## Apply the files

Download `extractor-fixes.zip` and upload it to `data/local` in your Codespace.
That folder is already ignored by your repository. Then run:

```bash
python -m zipfile -c data/local/before-extractor-fixes.zip src/resume_matcher tests pyproject.toml
unzip -o data/local/extractor-fixes.zip -d .
python -m pip install -e ".[dev]"
python -m pytest -q
git diff --check
git status --short
```

The first command makes a local backup before replacing files. The new package
configuration includes the alias CSV in built distributions. The dependency
requirements are the same as in your uploaded project. Expected test count: 46.

## Changes and reasons

1. Semantic candidates require two content words by default. Isolated terms such
   as `Machines`, `Management`, `systems`, and `Technologies` are withheld from
   semantic search. Exact matching continues to accept short labels and aliases.
   This is a conservative precision/recall tradeoff: an unfamiliar one-word skill
   can now be missed by semantic extraction. `min_content_tokens=1` restores the
   old length policy for an evaluation run.
2. Field labels immediately followed by a colon, such as `Programming Languages:`,
   are skipped as semantic candidates. Generic phrases such as `apply technical
   skills` are also skipped, while specific phrases such as `communication skills`
   remain eligible. The generic-word sets are English linguistic heuristics, not
   a trained skill-recognition model.
3. Pipes and semicolons separate grammar analysis for list entries. Newlines stay
   in the input so wrapped phrases such as `Provided medical care to\nhospital
   patients` retain their context. Bullet punctuation is removed from candidate
   evidence. Candidates remain case-insensitively deduplicated across segments.
4. `src/resume_matcher/data/alias_rules.csv` holds reviewed project corrections.
   `Design` no longer acts as an alias for `think creatively`. `OOP` and the two
   spellings of `object-oriented programming` resolve to the existing skill
   `use object-oriented programming`, when that skill exists in the loaded catalog.
   `Object Oriented Design` and `object-oriented modelling` are not merged with
   programming: related concepts are not automatically equivalent.
5. If a term still maps to multiple concepts after preferred-label precedence,
   exact extraction abstains instead of counting every interpretation. Aliases
   remain dictionary matches and can still be contextually ambiguous.
6. A complete candidate phrase already resolved exactly is not semantically
   reinterpreted. Longer action phrases that contain an exact skill remain
   eligible. When multiple semantic phrases retrieve one skill, the report keeps
   the phrase with the highest score; exact evidence retains priority.

## Extending the alias corrections

The CSV columns are `preferredLabel`, `alias`, `action`, and `reason`. Actions are
`add` or `block`; blocks apply only to aliases for the named concept. A preferred
label remains available. A rule target that identifies several distinct URIs is
rejected instead of applying the correction to all of them. A target absent from
the catalog is not created automatically.

These are local project corrections; they do not modify the ESCO CSV, the `Skill`
objects loaded from it, or their canonical URIs. Rules may target any field.
Tests demonstrate custom healthcare and finance aliases as well as programming.
Use a separate CSV or append reviewed rows as evaluation identifies further gaps:

```python
from resume_matcher.alias_rules import load_alias_rules
from resume_matcher.skill_extractor import ExactSkillExtractor

rules = load_alias_rules("path/to/your_alias_rules.csv")
extractor = ExactSkillExtractor(skills, alias_rules=rules)
```

A supplied rule collection replaces the defaults. Pass `alias_rules=[]` to
compare with the unmodified aliases.

## Check the missing catalog terms

The uploaded ZIP did not contain `data/raw/esco/skills_en.csv`. To establish
whether a missed term has a preferred label or alias in your actual export, run:

```bash
python scripts/audit_skill_catalog.py data/raw/esco/skills_en.csv
```

The script checks OOP, object-oriented programming, data structures, HTML, C, and
Design. It prints raw label hits, existing URIs, and active exact matches after
the corrections. Longer labels are printed as candidates to inspect, not assumed
equivalents. No embedding model is needed for this audit.

`data structures` remains a valid candidate phrase in the regression tests.
Whether the full catalog contains an equivalent concept, and whether semantic
retrieval ranks it appropriately, still needs this check. Do not map it to an
unrelated skill simply to increase the coverage percentage.

## Verification and limits

- Uploaded baseline: 28 tests passed locally.
- Updated implementation: 46 tests passed locally (the existing 28 plus 18 new
  regression checks).
- Tested with Python 3.12.13, spaCy 3.8.15, en_core_web_sm 3.8.0,
  sentence-transformers 5.7.0, scikit-learn 1.9.0, pytest 9.1.1,
  PyTorch 2.14.0+cpu, pypdf 6.17.0, and python-docx 1.2.0.
- The English parser is real. Semantic model outputs in unit tests are controlled
  test doubles, as in the original suite. These tests verify pipeline behavior;
  they do not measure semantic accuracy on a representative résumé dataset.
- A wheel built successfully, and it includes the alias CSV.
- Your complete PDF and ESCO catalog were absent from the upload, so the original
  42.9% coverage result has not been rerun here. Run the document-matching example
  again after installation and inspect the evidence.

These corrections address several observed errors, not all contextual ambiguity.
For example, `Business Administration` can still retrieve `office administration`;
course titles, negation, proficiency, and unrelated specialties require further
evaluation and context handling. OOP is a reviewed programming abbreviation, but
abbreviations can still have other meanings in another domain.

Exact score 1.0 is a method marker. Semantic scores are cosine similarities. The
0.75 threshold is unchanged and has not been calibrated on labeled documents.
Coverage counts shared detected ESCO concepts; it is not a hiring probability or
proof that a person lacks a skill. A useful next evaluation should cover several
fields and measure both incorrect detections and missed skills.

This service uses the ESCO classification of the European Commission. The alias
corrections in this bundle are project-specific adaptations.
