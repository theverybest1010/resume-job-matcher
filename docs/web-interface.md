# Web interface and HTTP API

[Documentation home](../README.md#engineering-guide)

## Local operation

Install both the editable package/dev dependencies and `requirements-web.txt`
as shown in the README, supply ESCO, then run `python web_app.py`.
The server binds to `0.0.0.0` on port 5000 with debug disabled. Open it locally
at `http://127.0.0.1:5000`; use private port forwarding in Codespaces.
Stop with Ctrl+C. The terminal remains occupied while the server runs.

| Environment variable | Meaning |
| --- | --- |
| `PORT` | Development-server port; default `5000`. |
| `ESCO_PATH` | CSV path; default is `data/raw/esco/skills_en.csv` beneath the directory containing `web_app.py`. |

Example in Bash: `PORT=5001 python web_app.py`.
These values are read from the process environment; the project does not
explicitly load a `.env` file. `HF_TOKEN`, if supplied for upstream model downloads,
is handled by the model tooling, not application authentication. Never commit it.

## User workflow

Upload one PDF, choose pasted text or a public job link, and compare. Results show
reviewed coverage, matched/missing skills, baseline additional skills, evidence,
and possible résumé–job pairs. Equivalent/Not equivalent decisions are local to
the current browser report. [Scoring](scoring.md) defines the fixed denominator.

## HTTP contract

`GET /` returns the HTML page. Flask also serves `/static/*`.
`POST /api/compare` accepts `multipart/form-data`:

| Field | Requirement |
| --- | --- |
| `resume` | Required file with `.pdf` extension and readable PDF contents. |
| `job_text` | Nonempty text, mutually exclusive with `job_url`. |
| `job_url` | Public HTTP(S) job page, mutually exclusive with `job_text`. |

```bash
curl -X POST http://127.0.0.1:5000/api/compare \
  -F 'resume=@data/local/resume.pdf' \
  --form-string 'job_text=Seeking Python and SQL experience.'
```

Success is HTTP 200 with these JSON fields:

| Fields | Meaning |
| --- | --- |
| `coverage`, `matched_count`, `required_count` | Confirmed-only baseline; coverage is percentage or null. |
| `matched`, `missing`, `additional` | Baseline display-label arrays. |
| `text_similarity` | TF-IDF percentage. |
| `resume_evidence`, `job_evidence` | Confirmed entries: `uri`, `skill`, `text`, `source`. |
| `resume_suggestions`, `job_suggestions` | Semantic entries with the same shape; no user decisions. |
| `requirements` | Fixed web requirement rows, including inferred skills. |

Each requirement has `uri`, `skill`, `texts` (job excerpts), `confirmed`, `matched`
(automatic overlap), and `candidates`. Each candidate has `resume_uri`,
`resume_skill`, `resume_text`, `job_text`, `similarity` (number or null), and
`same_catalog_skill`. Similarity may be null when no model is supplied, as in
some tests. The normal web builder supplies its existing embedding model.

The displayed reviewed score is computed from `requirements` by
`static/review.js`, not the top-level baseline fields. There is no approval,
export, history, or authentication endpoint. Browser decisions are not returned
to the API or persisted.

Errors return `{"error": "human-readable message"}`:

| Status | Typical cause |
| --- | --- |
| 400 | Missing/invalid input, extraction failure, inaccessible URL, unusable text. |
| 413 | Request exceeds Flask's configured limits. |
| 503 | Matcher initialization failed or another comparison holds the model lock. |
| 500 | Unexpected comparison error. |

## Input limits and URL import

- PDF payload: at most 5 MiB; empty, encrypted, and image-only documents fail.
- Extracted résumé text and job text: at most 50,000 characters each.
- Flask request cap: 11 MiB, form-memory cap 256 KiB, at most 10 form parts.
- Job URL: at most 2,048 characters; ordinary HTTP port 80 or HTTPS port 443.
- Import attempts at most four HTTP fetches in its redirect loop; every target
  is validated. Only globally routable DNS results are allowed; the connection
  uses a validated IP and HTTPS preserves hostname verification.
- Remote body cap: 2 MiB; HTML/plain text only; compressed responses rejected.
  Connection/read timeouts are 5/10 seconds per request, not an end-to-end SLA.

The importer does not run JavaScript, sign in, or send browser cookies. HTML
extraction can retain navigation, boilerplate, or unrelated text. Paste the job
text when a site blocks access. This is not a LinkedIn/Indeed integration.

## Hosting boundary

Source publication and public hosting are different tasks. This checkout has
no production WSGI server dependency, deployment manifest, durable job queue,
rate limiting, or authentication. Do not expose the Flask development server
as the production service.

A future deployment should use a production server calling `web_app:create_app`,
TLS, resource/time limits, restricted outbound access, and a documented retention
policy. Benchmark model memory before increasing worker count: workers duplicate
models, and the lock is per process. Parsing and URL fetching happen before the
model lock, so it does not protect the entire request path from concurrent load.
These are deployment tasks, not claims about controls already implemented.
