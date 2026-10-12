# Résumé Match

An explainable résumé-to-job comparison prototype built with Python, spaCy,
Sentence Transformers, and Flask. Upload a résumé PDF, paste a job description
or import a public job page, then inspect matched skills and review possible
semantic matches with evidence from both documents.

The project combines a lexical baseline, a shared skill catalog, and human review.
It uses pretrained models for inference. It does not train a model on uploaded
résumés. Scores describe detected skill coverage, not hiring probability or
verified proficiency.

## What it does

- Reads PDF résumés in the website; the Python library and CLI also read TXT/DOCX.
- Maps explicit skill names and aliases to stable ESCO or project-owned identifiers.
- Retrieves related skills from short phrases using sentence embeddings.
- Separates lexical/grammatical matches from unverified semantic suggestions.
- Shows résumé–job evidence pairs for user approval. Each job skill counts once.
- Reports TF-IDF text similarity separately from skill coverage.

## Quick start

Use Python **3.12** to match the development environment. Package metadata permits
Python >=3.11, but that is not a tested compatibility matrix. Node.js is needed
only for the JavaScript scoring test; there is no npm build step. No GPU is required:
the embedding matcher defaults to CPU. Allow disk space for Python dependencies
and downloaded model files; startup cost depends on the machine and network.

From a terminal:

```bash
git clone https://github.com/theverybest1010/resume-job-matcher.git
cd resume-job-matcher
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pip install -r requirements-web.txt
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` instead.
The spaCy English model is declared as a direct dependency in `pyproject.toml`.
The Sentence Transformer weights are downloaded when the matcher first starts.

### Add the skill catalog

Download the **English classification CSV** from the
[official ESCO download page](https://esco.ec.europa.eu/en/use-esco/download).
Extract `skills_en.csv` and place it at:

```text
data/raw/esco/skills_en.csv
```

Create the directory if necessary: `mkdir -p data/raw/esco` in Bash.
Development used ESCO v1.2.1. The full dataset is not included in this repository;
record the version you use when comparing results. See [data and models](docs/data-and-models.md)
for the loader contract and project-owned additions.

### Run the website

```bash
python web_app.py
```

Open `http://127.0.0.1:5000`. In Codespaces, use **Ports → 5000 → Open in Browser**;
keep the forwarded port private during development. Upload a text-based PDF and
paste a job description. The first comparison loads models and embeds the catalog;
later requests reuse that process's matcher. Stop with **Ctrl+C**.

This starts Flask's development server. Publishing source on GitHub does not
host the application. See [web/API and deployment scope](docs/web-interface.md).

## Understanding the result

| Result | Meaning |
| --- | --- |
| Reviewed skill coverage (website) | Matched distinct job skills divided by all detected distinct job skills, including model interpretations. |
| Equivalent button | Accepts a proposed résumé–job pair and counts that job skill as matched. |
| Not equivalent button | Gives that pair no credit. Other accepted evidence may still cover the same skill. |
| Confirmed coverage (CLI) | Overlap of exact/grammatical skill identifiers only; excludes semantic suggestions. |
| Text similarity | TF-IDF cosine similarity of the two full texts; does not change coverage. |

The website fixes its denominator before review. Accepting an additional pair
cannot lower coverage, and multiple accepted pairs cannot double-count one job
skill. Undoing an approval can lower it. Decisions live only in the current
browser comparison and reset on reload or a new comparison.

**The website and CLI intentionally report different coverage measures.**
Read [scoring and review](docs/scoring.md) before changing either implementation.

## Command-line comparison

Put personal documents in the ignored `data/local/` directory:

```bash
python scripts/match_documents.py data/local/resume.pdf data/local/job.txt --show-evidence
```

Use `--esco /path/to/skills_en.csv` to select another catalog. This CLI does not
include the browser's pair-approval workflow. For targeted extraction checks:

```bash
python scripts/evaluate_skill_extraction.py --esco data/raw/esco/skills_en.csv
python scripts/audit_skill_catalog.py data/raw/esco/skills_en.csv --terms "OOP" "HTML" "C"
```

## Tests

```bash
python -m pytest -q tests
node tests/test_review_coverage.cjs
```

The Python tests use fixtures and controlled model/network responses where
appropriate; some require the real installed spaCy pipeline. The targeted
`evaluate_skill_extraction.py` script additionally needs the full catalog and
real embedding model. Passing tests does not establish overall extraction
precision or recall. See [development and testing](docs/development.md).

## Engineering guide

| Document | Start here when you want to… |
| --- | --- |
| [Architecture](docs/architecture.md) | Follow the request lifecycle and locate a component. |
| [Scoring](docs/scoring.md) | Understand identifiers, thresholds, denominators, and approval state. |
| [Data and models](docs/data-and-models.md) | Set up ESCO or extend skills and aliases. |
| [Web/API](docs/web-interface.md) | Integrate the endpoint or understand operating limits. |
| [Development](docs/development.md) | Run checks, diagnose errors, and choose the right tests. |
| [Contributing](CONTRIBUTING.md) | Make a focused, reviewable change. |
| [Security and privacy](SECURITY.md) | Understand data handling and report vulnerabilities. |
| [Publication checklist](docs/publication.md) | Review the repository before publishing. |

## Limits and status

This is an English-language research/portfolio prototype, not a validated ATS.
Catalog coverage, PDF reading order, aliases, and phrase parsing can cause false
positives or missed skills. Related concepts are not necessarily equivalent;
manual approval is an interpretation, not independent verification. Years of
experience, credentials, seniority, negation, and job relevance are not reliably
validated. There is no OCR, account system, saved comparison history, or production
hosting configuration.

Built by **Hussein Alani and Abiral Pokharel**.
No project license file is included in this snapshot; maintainers should choose
one explicitly before presenting the project as licensed open-source software.
Third-party data, models, and dependencies retain their own terms.
