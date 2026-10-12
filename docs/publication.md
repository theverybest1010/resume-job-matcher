# GitHub publication checklist

[Documentation home](../README.md#engineering-guide)

This guide concerns publishing the repository. It does not deploy the Flask app.

## Included in this documentation update

- Expanded README and engineering guides for the actual uploaded source.
- Explicit distinction between confirmed and browser-reviewed coverage.
- Setup, catalog extension, API, testing, privacy, and contribution guidance.
- Historical labels on superseded design notes; application behavior unchanged.

## Before pushing

Run from your existing clone after applying the documentation files:

```bash
git status --short --branch
python -m pytest -q tests
node tests/test_review_coverage.cjs
git diff --check
git diff --stat
```

Review staged paths with `git diff --cached --name-only` before committing.
`data/raw/`, `data/local/`, `.env`, and virtual environments are already ignored.
Gitignore does not remove files already tracked or erase older commits.

The supplied ZIP contains source, tests, documentation, and a UI preview; it does
not include raw ESCO, uploaded résumés, `.env`, or model weights. A ZIP snapshot
cannot establish whether Git history ever contained private data. Review the
repository history separately before changing its visibility. Keep real résumés,
backup ZIPs, credentials, and model caches out of commits.

## Maintainer decisions

- Choose a project license intentionally; this update does not assign MIT,
  Apache, or another license on your behalf. Review third-party notices separately.
- Verify contributor names and attribution in the README.
- Configure a private vulnerability-reporting channel if desired.
- Add a truthful repository description, for example:
  “Explainable résumé–job matching with ESCO, sentence embeddings, and human-reviewed skill pairs.”
- Optional topics: `python`, `flask`, `nlp`, `spacy`, `sentence-transformers`,
  `resume-matching`, `explainable-ai`.
- Do not claim validated accuracy, production readiness, or ATS equivalence from
  passing unit tests. Keep example data synthetic and label screenshots accurately.

## Documentation-only commit

If only applying the documentation overlay supplied with this update:

```bash
git add README.md CONTRIBUTING.md SECURITY.md docs/
git diff --cached --check
git diff --cached --stat
git commit -m "Document setup, architecture, scoring, and contribution workflow"
```

Review `docs/` before staging if it contains your own unrelated work. Push the
current branch using your normal workflow; do not force-push or replace the
repository with an extracted ZIP. Preserve the existing Git history.

## Documentation review validation (2026-10-12)

The documentation update was checked against the uploaded source snapshot.
All local Markdown file links resolved; application/configuration/test source
was unchanged. Focused web, URL-import, and pair-review tests passed (27 Python
tests), along with 10 JavaScript scoring assertions. A limited credential-pattern
scan found no matching private keys or GitHub/Hugging Face token patterns in
the snapshot; this is not a full secrets or history audit.

The full NLP suite and a real-model/catalog comparison were not rerun during
this documentation pass: this review environment lacked Torch/Sentence
Transformers and the raw ESCO export. Run the complete checks in your configured
Codespace before publishing.
