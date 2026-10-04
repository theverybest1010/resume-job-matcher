# Flask website: local development

This interface adds PDF résumé upload (drag-and-drop or file picker), a pasted
job description or public job-page link, and an explainable comparison report.
It calls the existing MatchingPipeline; the underlying NLP code is unchanged.

## Start in Codespaces

From the repository root, with your existing virtual environment active:

```bash
python -m pip install -r requirements-web.txt
python -m pytest -q
python web_app.py
```

Open port 5000 from the Codespaces Ports panel using **Open in Browser**. Keep
port visibility Private while testing. Use a browser tab rather than an embedded
preview. Stop the server with Ctrl+C. The first comparison initializes the
models; later comparisons reuse them. Only one model comparison runs at a time.

The default dataset path is `data/raw/esco/skills_en.csv`, relative to web_app.py.
Set ESCO_PATH to use another path. Set PORT to change the default port of 5000.
The existing editable package installation, spaCy model, and semantic model
setup are still required. There is no browser-side model or mock response in
the application.

## Input and results

- Résumé: one readable PDF, maximum 5 MiB; scanned PDFs need OCR elsewhere.
- Job: paste text (up to 50,000 characters), or use a public HTTP(S) webpage.
- Job links: no credentials, cookies, sign-in, or JavaScript browser execution.
  Some job sites block automated requests. The interface offers pasting text
  when access fails. Imported HTML can contain navigation and unrelated text;
  inspect the evidence. This is not a guaranteed LinkedIn/Indeed integration.
- Results show confirmed coverage with matched and required counts, missing and
  additional skills, unreviewed suggestions, and supporting excerpts.
- Unreviewed suggestions are excluded from both sides of confirmed coverage.
  No confirmed job skills produces N/A, not a misleading percentage.
- Feedback prompts users to add truthful evidence of skills they actually have.
  The application does not invent résumé achievements or predict hiring outcomes.

## Data handling

Uploads are read through temporary files and removed before comparison. There
is no database, saved résumé, comparison history, analytics, or browser storage.
Text is processed on the server in memory. The job site receives a request from
the server when a URL is supplied; the résumé is not sent to that site. Model
initialization may download pretrained files, but document text is processed by
the local pipeline rather than sent to a hosted language model.

Public-link requests validate resolved addresses, connect to a validated IP,
retain TLS hostname checks, and repeat validation for redirects. Downloads and
input lengths are bounded. These controls do not replace deployment-level
resource isolation and rate limits.

## Validation and hosting scope

The included 23 web tests use actual PDF parsing and controlled matcher/network
responses, so they do not download model weights or need the full catalog.
They cover form validation, serialization, temp-file removal, model reuse,
public URL rules, redirects, and error handling. Run the entire repository test
suite in your Codespace, then compare real documents through the browser.

This first version uses Flask's development server. Before public hosting,
choose a production WSGI server, CPU/RAM budget, worker/request limits, and a
managed model/catalog startup process. This package does not deploy the app.

Framework references:
- https://flask.palletsprojects.com/en/stable/web-security/
- https://urllib3.readthedocs.io/en/stable/advanced-usage.html
