# Confirmed matches and semantic suggestions

`HybridSkillExtractor.extract` still returns all retained mentions. Check
`mention.is_confirmed` before counting a mention as a confirmed match.

- `exact`: the existing label/alias rules accepted the match.
- `grammatical`: semantic retrieval found a canonical label whose ordered
  lemmas match the candidate phrase. Both phrases must begin with a verb.
  Tense/plural changes and omission of a/an/the are permitted. Negation,
  modifiers, prepositions, and other words are preserved during this comparison.
- `semantic`: related result above the threshold, available as a suggestion
  requiring review. It does not contribute to skill coverage.

This is conservative lexical evidence, not verification of a person's ability.
Exact aliases can still be too broad. Negation or context lost upstream during
candidate extraction cannot be recovered by this check. Genuine paraphrases
can remain suggestions. The semantic model and its threshold are unchanged.

Grammatical verification uses the candidate extractor's existing spaCy pipeline.
A custom candidate extractor without an `nlp` attribute produces suggestions
for semantic results, without grammatical confirmation.

For repeated mentions of one skill, exact evidence takes priority, followed by
grammatical evidence, then semantic similarity. Scores within the same evidence
class choose the retained mention. Semantic scores remain cosine similarities,
not confidence probabilities.

`MatchingPipeline` retains all mentions in its report, but passes only confirmed
ones to `compare_skills`. `resume_suggestions` and `job_suggestions` expose the
unconfirmed results. `has_confirmed_job_skills` indicates whether a coverage
percentage is meaningful. The existing numeric zero convention for an empty
job set remains in SkillGapReport; the CLI renders that case as N/A.

Run:

```bash
python -m pytest -q
python scripts/evaluate_skill_extraction.py
python scripts/match_documents.py data/local/resume.pdf data/local/job.txt --show-evidence
```

The evaluation script now grades its specified requirements against confirmed
matches. Incorrect semantic suggestions may still appear in its evidence.
A passing targeted case means only that its named constraints are met, not that
all output is correct. Review-only cases remain ungraded. These are development
examples, not a held-out accuracy benchmark.

Coverage now uses only confirmed job skills as its denominator. It can rise
because uncertain requirements were excluded; that is not evidence of improved
recall or job suitability. Always review the job suggestions alongside coverage.
No automatic user approval flow or persisted confirmation feature is included.
