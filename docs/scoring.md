# Scoring and user review

[Documentation home](../README.md#engineering-guide)

## Three distinct numbers

### 1. Confirmed coverage: package and CLI

A mention is confirmed when its source is `exact` or `grammatical`.
Let R and J be the sets of confirmed résumé and job skill URIs.
Confirmed coverage is `100 × |R ∩ J| / |J|`.

`compare_skills` returns 0.0 for an empty J as a low-level convention. The CLI
prints N/A and the web baseline serializes null when there are no confirmed job
skills. Do not treat the low-level zero as evidence of a poor match.

### 2. Reviewed coverage: website

Let J_all contain every distinct detected job skill URI, including semantic
interpretations. Let M contain automatically matched requirements (confirmed
on both documents) and job URIs with at least one user-accepted pair.
Reviewed coverage is `100 × |M| / |J_all|`, rounded to one decimal place.

The denominator is fixed when the comparison is generated. An empty J_all
produces null and the UI displays a dash. There is no partial-credit weighting.
A semantic similarity value does not itself earn coverage points.

Example: six detected job skills, two automatically matched. Initial coverage is
33.3%. Accepting one new job skill makes it 50.0%. Approving another pair for that
same skill leaves it 50.0%. Rejecting a pending pair leaves it unchanged. Undoing
its only approval returns coverage to 33.3%.

The website includes inferred job skills in its denominator; the CLI excludes
them. Their percentages can differ even before a user clicks anything.

### 3. TF-IDF similarity

`tfidf_similarity` fits a vectorizer to the two input documents, uses the custom
tokenizer and English stop words, then computes cosine similarity. The API
multiplies by 100 for display. This is a wording comparison, never blended into
coverage. Nonempty inputs that leave an empty vocabulary can still fail.

## Where suggestions come from

Two retrieval stages use different thresholds:

| Stage | Compared texts | Default | Effect |
| --- | --- | --- | --- |
| Catalog extraction | Candidate phrase → canonical preferred skill label | 0.75, top-1 | Produces an extracted semantic/grammatical mention. |
| Pair review | Extracted job phrase → extracted résumé phrase | 0.65 | Proposes a pair; does not award credit. |

Pair review also includes same-URI candidates even below the pair similarity
cutoff. Candidates are deduplicated by résumé URI and phrase, ranked with
same-catalog matches first and then similarity, and limited to three per unmatched
job skill. Already automatically matched requirements need no suggestions.
Only extracted mentions are compared; arbitrary résumé sentences are not searched.

The 0.65 and 0.75 values are implementation defaults, not calibrated probabilities.
Exact score 1.0 records the matching method, not certainty. Do not describe a
cosine score of 0.8 as an 80% chance that two skills are equivalent.

## Decision semantics

- **Equivalent:** user judges the shown résumé evidence sufficient for the shown
  job skill; that job URI joins the matched set.
- **Not equivalent:** this pair earns no credit. It does not erase an automatic
  match or another accepted pair.
- Selecting the active button again undoes that decision.
- A reload or new comparison clears decisions. Nothing is written back to ESCO,
  a shared alias list, or a model. This is human review, not online learning.

`static/review.js` is the authoritative displayed calculation. Decisions are keyed
by JSON-encoded `[job URI, candidate index]` within the current report only.
The API's top-level `coverage`, `matched`, and `missing` remain the confirmed-only
baseline. API consumers must not assume those fields equal the reviewed UI state.
The UI's additional-skills list remains the baseline list; approvals do not
reconcile it, so an approved related skill can still appear as additional.

## Interpretation limits

An inferred job skill may be wrong but still enter J_all. There is currently no
remove-invalid-requirement control. Accepting every proposal does not guarantee
100%: some requirements have no candidates. Users may over-approve weak matches;
reviewed coverage is not comparable across reviewers without a shared protocol.
The score does not assess years of experience, skill depth, recency, essential
versus optional requirements, or legal/professional qualifications.
