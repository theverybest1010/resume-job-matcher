# Development and testing

[Documentation home](../README.md#engineering-guide)

## Development loop

Work from the repository root in a virtual environment. Install with
`python -m pip install -e ".[dev]"` and
`python -m pip install -r requirements-web.txt`.
Editable installation makes the `src` package importable without manual path hacks.
Keep personal documents and archives under ignored `data/local/`.

```bash
python -m pytest -q tests
node tests/test_review_coverage.cjs
git diff --check
```

Specifying `tests` avoids collecting old tests in an unpacked backup directory.
The Node test is not discovered by pytest; both commands matter. No npm install
is required for that test. A recent Node runtime with `node:assert/strict` support
is sufficient.

## What the tests establish

| Area | Test files |
| --- | --- |
| Catalog/aliases/identity | `test_skills.py`, `test_skill_catalog.py`, `test_alias_rules.py` |
| Exact, phrase, hybrid extraction | `test_skill_extractor.py`, `test_candidate_phrases.py`, `test_hybrid_extractor.py` |
| Retrieval and confirmation | `test_semantic_matcher.py`, `test_match_confirmation.py` |
| Documents and comparison | `test_document_loader.py`, `test_document_matching.py`, `test_matching_pipeline.py`, `test_skill_gap.py` |
| Lexical baseline | `test_preprocessing.py`, `test_tfidf.py` |
| HTTP/import/pair review | `test_web_app.py`, `test_job_links.py`, `test_pair_review.py` |
| Browser scoring function | `test_review_coverage.cjs` |

Several tests inject controlled embedding models or mock network responses.
The installed NLP packages are still needed for imports, and phrase/confirmation
tests use `en_core_web_sm`. Test counts are intentionally not pinned in the README:
use the output from the revision/environment you actually ran.

## Real-model development evaluation

```bash
python scripts/evaluate_skill_extraction.py --esco data/raw/esco/skills_en.csv
```

Requires the actual catalog and embedding weights. Exit 0 means all annotated
checks passed, 1 means a check failed, and configuration/target-resolution errors
may exit 2. Catalog loading failures outside that handling can raise exceptions.
The eight hand-authored cases include review-only and partially graded predictions.
They are regression examples, not a held-out benchmark or an accuracy estimate.

When assessing a model/catalog change, retain an independent set of documents
across occupations and report false positives and misses, not just a higher
coverage score. Fix extraction before treating its output as ground truth.

## Manual browser check

1. Start Flask; upload a readable PDF and paste job text.
2. Inspect job skills and original excerpts, including incorrect inferences.
3. Approve an unmatched pair: matched count rises once and denominator stays fixed.
4. Reject an undecided pair: coverage stays unchanged. Undo an approval and verify
   the score changes only if no other accepted pair covers that requirement.
5. Reload or start a new comparison: decisions reset.
6. Check a narrow/mobile viewport and keyboard access to both review buttons.
7. Try an invalid PDF and an inaccessible job link; verify usable error messages.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| `No module named resume_matcher` or `pytest` | Activate `.venv`; reinstall `-e ".[dev]"` with the same `python`. |
| spaCy model missing | Reinstall project dependencies; verify `python -c "import spacy; spacy.load('en_core_web_sm')"`. |
| Matcher cannot start | Check ESCO path, required headers, model availability, and memory; the response hides internal errors. |
| HF unauthenticated warning | Downloads may work without a token; it is not a failed comparison. Keep any token out of Git. |
| Port already in use | Stop the existing Flask terminal with Ctrl+C or select `PORT=5001`. |
| UI still looks old | Restart Flask and hard-refresh the browser after changing frontend files. |
| Backup tests cause import errors | Run `pytest tests` and keep extracted backups outside the repository. |
| Scanned or encrypted PDF rejected | Supply a text-based, unencrypted export; OCR is not implemented. |
| URL import fails | Paste text; sites may require login, browser rendering, or block requests. |
| CLI and browser percentages differ | Read [scoring](scoring.md): the denominators intentionally differ. |

## Next engineering work (not implemented)

Useful follow-ups include a dependency lock and model revision pin, a cross-domain
held-out evaluation, invalid-requirement review, contextual/negation handling,
embedding cache versioning, and production resource controls. Add CI only after
choosing supported Python/Node versions and validating installation on a clean
runner. No CI workflow is included in this snapshot.
