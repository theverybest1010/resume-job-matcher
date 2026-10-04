# Suggestion review

Applies to the original confirmed-skill website, before weighted coverage.
Each semantic suggestion has Not equivalent (left) and Equivalent (right).
Accepted interpretations add the suggested skill URI to that document's skill set.
Rejected and pending interpretations are excluded. Existing exact/grammatical
skills remain included, even if another suggestion for that skill is rejected.

Coverage = distinct shared included skill URIs / distinct included job skill URIs.
An accepted resume-only skill becomes additional, not a match. Accepting a job
suggestion can increase the denominator and lower coverage. Duplicate skills
count once. No job skills yields an undefined score, displayed as a dash.

Click a selected decision to undo; choosing the other button switches it.
Decisions are browser-memory only, scoped to one comparison. A new comparison
or page reload clears them. This does not train the model or change the catalog.
Accepted means user-reviewed interpretation, not verified proficiency.
The API continues to return the original model report; reviewed coverage is
computed in the browser and is not saved on the server.

Run python -m pytest -q and node tests/test_review_coverage.cjs.
Restart Flask and hard-refresh after installation.
