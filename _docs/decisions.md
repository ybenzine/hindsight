# Grooming decisions

Cross-cutting calls made by the PM role (`_docs/team/pm.md`) while grooming the
backlog, so they live in one place instead of being repeated in every issue.
Individual issues link back here instead of re-explaining the reasoning.

## App layout

One Django app per bounded area, matching `_docs/outdated/architecture.md`:
`apps/accounts`, `apps/projects`, `apps/cycles`, `apps/retro`, `apps/meetings`,
`apps/outcomes`, `apps/ai`, `apps/realtime`, `apps/common`. Business rules live
in a `services.py` per app, called from thin views, so the AI/meeting pipeline
is testable without HTTP.

## Tests

Mirror the app layout under `tests/`: `tests/<app>/test_*.py`. All tests run
against Postgres via `config/settings_test.py` (#2) — no SQLite anywhere,
because the schema uses Postgres-specific JSONB.

## Dependencies pre-approved by the architecture doc

`AGENTS.md` requires asking before adding a dependency. `_docs/outdated/architecture.md`
already named these as the stack, so grooming treats them as pre-approved and
calls them out per issue rather than re-litigating each one — flag at
implementation time if any should be reconsidered:

- `django-tasks` (#3) — database-backed queue, no Redis.
- `django-allauth` (#6) — auth flows.
- `anthropic` SDK (#25) — the only place the Claude API is called from.
- `openai` SDK (#28) — the only place Whisper is called from.
- `psycopg[binary]` and `django-environ` — already approved and shipped in #2.
- HTMX, Alpine.js, SortableJS — front-end JS, loaded as static assets, not a
  Python dependency at all.

Any dependency *not* on this list still needs to be asked about before adding.

## Owner matching (#30)

"Weak match" means a fuzzy-match ratio below **0.6** (e.g. `difflib.SequenceMatcher`
on normalized, lower-cased full name / email-local-part) against the project's
active members. Below the threshold, the action ships with no resolved owner
and a `needs_review` flag rather than guessing.

## Front-end assets

HTMX, Alpine.js, and SortableJS are vendored as static files under
`static/vendor/` (checked into the repo), not loaded from a CDN — keeps dev
and CI working offline and doesn't make every page load depend on a third
party being up.

## Realtime bus

`apps/realtime` ships an in-process pub/sub for the MVP (#14) — correct only
for a single web process, which is what the MVP deploys (#38). Swapping to
Postgres `LISTEN/NOTIFY` or Redis for multi-process scaling is deliberately
deferred: #40.

## Whisper's 25 MB limit (#28, #41)

#28 rejects an upload over the API's 25 MB limit with a clear `failed` status
and a user-facing message as its own first pass. #41 (automatic `ffmpeg`
segmentation so an oversized recording still transcribes) is **MVP scope**,
not deferred: `_docs/outdated/plan.md`'s core workflow explicitly includes
uploading *video*, and a realistic 20–30+ minute recording routinely exceeds
25 MB — without segmentation, "upload a meeting recording" fails outright for
a typical video export, not just an edge case. #41 was originally filed as a
fast-follow while grooming #28 and was promoted after a scope review.

## Accessibility

Every UI issue ships baseline accessibility as part of its own acceptance
criteria: semantic HTML, labeled form inputs, keyboard-operable controls. A
full WCAG 2.1 AA pass (screen-reader testing, automated axe-core checks,
contrast audit, SSE live-region announcements) across all screens is
deferred to one cross-cutting issue: #39.

## Issue labels

- `MVP` — in scope for the MVP defined in `_docs/outdated/plan.md`.
- `fast-follow` — real work, deliberately not part of the MVP. Never both.
- `groomed` — the PM role has rewritten the issue onto `_docs/task-template.md`
  and it is ready for an engineer to pick up.

## Fast-follow scope review

After grooming #3-#36, every fast-follow (#37-#42) was checked against
`_docs/outdated/plan.md`'s MVP definition and exclusions list. Five held up as
correctly deferred (#37 CI, #38 deployment, #39 accessibility audit, #40
realtime multi-process scaling, #42 invite-by-email for new users — none are
part of the "a team can..." MVP list or are explicitly deferred by the
architecture doc). #41 was promoted to MVP; see above.
