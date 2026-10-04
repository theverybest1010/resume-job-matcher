# Review resume–job pairs

Replaces the independent phrase-to-catalog approval buttons. Each pair shows
actual extracted job wording and actual extracted resume wording. The user
judges whether that resume evidence satisfies the job skill. No semantic pair
receives credit automatically.

The fixed denominator is all distinct detected job skill URIs, including semantic
interpretations. Initially matched means confirmed on both documents. An accepted
pair adds its job URI to the matched set. Duplicate approvals cannot add duplicate
credit; rejection adds nothing. Undo or switching a prior approval can remove its
credit. There is no score if there are no detected job skills.

This denominator differs from the earlier confirmed-only denominator, so initial
coverage may change. It is displayed for inspection. Model interpretations may
be wrong; this prototype does not verify experience or hiring suitability.

Candidate generation reuses the existing sentence-transformer model. Same-catalog
candidates are offered; otherwise original extracted phrases are compared using
cosine similarity with a 0.65 retrieval threshold. Up to three candidates per
unmatched job skill are shown. Retrieval similarity is not a correctness guarantee.
Unextracted resume evidence may be missed. No inference code or catalog rules change.

Decisions last for the current browser comparison only, not across reloads or new
comparisons. The API returns baseline evidence and review candidates. Browser
coverage is recomputed from the immutable requirement list plus local decisions.

Tests: python -m pytest -q; node tests/test_review_coverage.cjs.
Local verification: 17 Python web/pair tests, 10 JS assertions, browser accept,
reject, undo and mobile checks. Embedding retrieval tests use a controlled encoder;
real-model quality should be reviewed in the Codespace.
