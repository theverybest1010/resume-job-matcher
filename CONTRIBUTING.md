# Contributing

Start with the [README](README.md), [architecture](docs/architecture.md), and
[scoring contract](docs/scoring.md). Discuss changes that redefine coverage or
user-review behavior before implementing them.

## Make a focused change

1. Create a branch from the current main branch.
2. Reproduce the problem using a synthetic or anonymized fixture. Never attach
   an applicant's résumé, contact details, tokens, or private job content.
3. Change the smallest responsible component; keep data corrections in the
   catalog/rule CSVs when appropriate.
4. Add a meaningful regression test for the behavior and a nearby negative case.
   A model-generated suggestion should not silently become verified evidence.
5. Run Python and JavaScript checks in [development](docs/development.md), inspect
   `git diff --check`, and update the relevant documentation.
6. Describe the problem, behavior change, validation, and limitations in the PR.

## Contracts to preserve

- Skill identity uses URIs, not display labels; aliases do not create extra points.
- Default exact/grammatical confirmation is not proof of proficiency.
- TF-IDF, confirmed coverage, and reviewed coverage remain separately named.
- During pair review the denominator stays fixed; duplicate approvals earn no
  extra credit; semantic similarity alone grants no automatic review credit.
- Decisions are scoped to the current comparison; do not introduce persistence
  or document retention without making that change explicit.

Follow existing Python/JavaScript conventions. There is no mandatory formatter
configuration in this snapshot. Prefer clear names and rationale over comments
that merely repeat a statement. If changing the API, update its field table and
controlled web tests. If changing aliases/models, preserve positive controls
alongside false-positive regressions.

Maintainers have not selected a project license in this snapshot. Resolve the
license before relying on a contribution or redistribution policy; this document
does not grant one on their behalf.
