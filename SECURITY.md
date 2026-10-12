# Security and privacy

This repository is a development prototype. There is no published security audit
or production hardening guarantee.

## Data flow

Uploaded PDFs are written to temporary files and removed after extraction,
before model analysis. The project has no database, saved upload history, analytics,
or browser local storage. Document text and reports exist in process/browser
memory. The grammatical verifier has a bounded LRU cache keyed by phrases, so
some text-derived keys can remain until eviction or process exit. Do not promise
immediate memory erasure after a request.

Model downloads contact upstream services; inference runs on the server. A job
URL causes the server to contact that site, but the résumé is not sent to it.
Infrastructure logs, proxies, OS caches, and hosting-provider retention are outside
the application's current controls and must be considered before public hosting.

## Existing controls and limits

`web_app.py` bounds request/file/text sizes, disables debug in its development
entry point, returns generic comparison errors, and adds no-store, nosniff,
referrer-policy, and content-security-policy headers. `job_links.py` validates
public destinations including redirects and bounds downloads. These are useful
controls, not a complete security boundary.

There is no authentication, per-user rate limiter, distributed concurrency control,
or hardened document-processing sandbox. PDF parsing and URL fetching happen
before the model lock. Review resource exhaustion, network egress, and dependency
updates before exposing the service publicly. Browser approvals are editable
client-side state and must not be treated as trusted recruiting records.

## Reporting

Do not post credentials, résumés, exploit payloads containing personal data, or
sensitive reproduction details in a public issue. Use GitHub's private vulnerability
reporting feature if the repository has it enabled. Otherwise request a private
reporting channel from the maintainers before sharing sensitive details. No
security email address or response-time commitment is configured here.

For ordinary reproducible defects, use a synthetic fixture and a public issue.
Maintainers should configure a private reporting channel before a public launch.
