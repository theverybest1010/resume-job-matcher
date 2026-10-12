# Data, models, and catalog extension

[Documentation home](../README.md#engineering-guide)

## External inputs

| Input | Source and local use |
| --- | --- |
| ESCO English skills CSV | [Official download](https://esco.ec.europa.eu/en/use-esco/download); default `data/raw/esco/skills_en.csv`. |
| spaCy English pipeline | `en_core_web_sm` 3.8.0 wheel declared in `pyproject.toml`; supplies parsing, POS tags, lemmas. |
| Sentence Transformer | [all-MiniLM-L6-v2 model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2); configured in `semantic_matcher.py`. |
| Project concepts/rules | Versioned CSVs in `src/resume_matcher/data/`. |

Consult upstream terms before redistributing third-party data/model files. They
are not covered by any future project license automatically. No raw ESCO export
or embedding weights are bundled here. Model inference runs locally on the server;
this project does not call a hosted LLM API to analyze documents.

Development used ESCO v1.2.1: 13,960 rows reduced to 13,939 unique skill URIs,
then three bundled supplemental concepts for 13,942 total. These are historical
observations, not runtime invariants; the export is absent from this snapshot.
Record ESCO version, CSV checksum, Python/dependency versions, and model revision
for reproducible evaluations. Dependencies have ranges rather than a lockfile,
and the embedding model revision is not pinned in the current implementation.

## Raw ESCO loader

Required headers: `conceptUri`, `preferredLabel`, `altLabels`, `skillType`.
Files use UTF-8 with optional BOM. Alternate labels are split on newlines.
Rows with empty URI/label are skipped; repeated URIs retain the first valid row.
The loader does not merge conflicting duplicates or filter status automatically.
Use an appropriate released export and audit duplicates when changing datasets.

```bash
python -c "from resume_matcher.skill_catalog import load_skill_catalog; print(len(load_skill_catalog('data/raw/esco/skills_en.csv')))"
```

`audit_skill_catalog.py` intentionally inspects the raw ESCO loader plus alias
rules, not the supplemental catalog. Use `load_skill_catalog` to inspect the
combined production catalog.

## Add an alias to an existing concept

Edit `src/resume_matcher/data/alias_rules.csv` with columns
`preferredLabel,alias,action,reason`. Actions are `add` or `block`.
Rules target a unique preferred label; they do not create a new concept. Blocks
remove aliases for that concept, not canonical preferred labels. Missing targets
are not necessarily runtime errors, so use the audit script after catalog changes.
An ambiguous preferred-label target raises an error.

Give every change a rationale and tests for a positive phrase and a nearby
negative/ambiguous phrase. Do not turn related actions (repair versus operate)
into synonyms solely to improve one résumé's score.

## Add a genuinely missing concept

Edit `src/resume_matcher/data/supplemental_skills.csv`. Required columns:

| Column | Meaning |
| --- | --- |
| `uri` | Unique stable `urn:resume-job-matcher:skill:...` identifier. |
| `preferredLabel`, `skillType` | Display label and knowledge/competence classification. |
| `aliases` | Pipe-separated explicit variants. |
| `contextualAliases`, `contextHeadings` | Pipe-separated ambiguous aliases and allowed labeled-list headings. |
| `semanticMatching` | `true` or `false`; contextual aliases require false. |
| `replacesAliasFrom`, `replacesAlias` | Optional pair identifying an alias transferred from a broader concept. |
| `reason` | Human-readable rationale for the addition. |

A custom `supplemental_path` replaces the bundled supplement; it is not appended
to it. Alias transfers alter in-memory objects, never the raw CSV. Stable URIs
must remain distinct even when display labels are similar.

The bundled additions are data structures, HTML, and C programming. Standalone
`C` needs an allowed labeled programming-language list; qualified phrases such
as `C programming` are also available. It is excluded from semantic retrieval.

## Model changes

Changing the Sentence Transformer affects both catalog retrieval and web pair
retrieval. Rebuild embeddings, retain negative examples, and assess both thresholds
on held-out examples across occupations. No training script or labeled benchmark
is included. Avoid reporting accuracy from a handful of handpicked demonstrations.
