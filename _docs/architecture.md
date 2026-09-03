# Architecture — Hindsight (Django)

Companion to [`plan.md`](./plan.md). This describes *how* the MVP is built. No code yet.

## Stack decisions

| Layer | Choice | Notes |
|---|---|---|
| Language / framework | Python + Django (latest LTS-track 5.x) | Server-rendered templates as the default |
| Interactivity | HTMX + Alpine.js | Partial updates, no SPA |
| Live updates | Server-Sent Events (SSE) | One-way push for reveal, votes, mode changes, job status. No WebSockets, no Redis — an in-process bus while there is a single web process |
| Cluster board drag-and-drop | Small vanilla JS + [SortableJS](https://sortablejs.github.io/Sortable/) island | Posts moves to minimal JSON endpoints; board re-syncs via SSE |
| API style | Server-rendered + a handful of JSON endpoints | No Django REST Framework |
| Database | PostgreSQL | JSONB used for AI draft payloads |
| ORM / migrations | Django ORM + built-in migrations | |
| Auth | Django auth + `django-allauth` | Email/password + optional social later |
| Background jobs | `django-tasks`, database backend | Transcription and extraction are minutes-long; must be off the request path. Postgres is the queue — no Redis. A `db_worker` process drains it |
| Object storage | **None** | An uploaded recording is transcribed then discarded; only the transcript text is kept |
| Transcription | OpenAI Whisper API | Isolated behind a `Transcriber` interface (see [AI integration](#ai-integration)) |
| LLM | Claude API (`anthropic` SDK) | Clustering suggestions, extraction, summary |
| Config | `django-environ`, 12-factor env vars | No cloud-specific assumptions until deploy |
| Hosting | **Deferred** | Build cloud-agnostic: Postgres + one web process + one worker process. No Redis, no bucket |

### Why SSE over Channels for the MVP

The plan needs *broadcast* ("everyone sees the reveal", "vote totals appear when voting closes", "job finished"), not bidirectional low-latency sync. SSE over a plain HTTP endpoint covers all of it, runs on a normal WSGI/ASGI setup, and needs no broker. The MVP ships with no Redis at all. If we later scale to multiple web processes, the SSE view swaps its in-process event queue for Postgres `LISTEN/NOTIFY` or Redis pub/sub — the client contract does not change.

User actions (move card, cast vote, mark topic discussed) are ordinary HTMX `POST`s. The response updates the actor's own DOM; a broadcast event tells every other client to refetch the affected fragment.

## Django project layout

```
config/                  # settings/, urls, wsgi/asgi, task-queue config
  settings/base.py, dev.py, prod.py
apps/
  accounts/              # User (email login), profile
  projects/              # Project, Membership (role: member | facilitator)
  cycles/                # FeedbackCycle, FeedbackCard
  retro/                 # Retrospective, Cluster, ClusterCard, Vote, DiscussionTopic, Note
  meetings/              # MeetingRecord, uploads, transcript, extraction drafts
  outcomes/              # Decision, ActionItem
  ai/                    # Transcriber interface, Claude client, clustering + extraction services
  realtime/              # SSE endpoint, event bus, event types
  common/                # base models, permissions, mixins, templatetags
templates/
static/
```

Apps stay thin; business rules live in `services.py` modules per app, called from views. Keeps views small and the AI/meeting pipeline testable without HTTP.

## Data model (core entities)

```
User
Project
Membership        (User × Project, role, is_active)
FeedbackCycle     (Project, week/opened_at, status: collecting | revealed | closed, facilitator)
FeedbackCard      (Cycle, column: start|stop|continue, text, author_link, created_at)
Retrospective     (Cycle 1:1, mode: reveal|cluster|vote|discuss|summary, started_at, closed_at)
Cluster           (Retrospective, title, order)
ClusterCard       (Cluster, FeedbackCard, order)      # a card not in any cluster = ungrouped
Vote              (Retrospective, User, Cluster, weight 1..3)   # sum of weights per user ≤ 3
DiscussionTopic   (Retrospective, Cluster, rank, status: pending|discussed|skipped|deferred)
Note              (Retrospective, author, body, kind: note|decision|action, created_at)
MeetingRecord     (Retrospective, upload_kind: audio|video|transcript_file|pasted_text,
                   raw_text, transcript_text, status: pending|transcribing|extracting|ready|failed)
                   # no file field — an uploaded recording is written to a temp path,
                   # transcribed, then deleted; only transcript_text / raw_text is kept
ExtractionDraft   (MeetingRecord 1:1, payload JSONB, confirmed_at)   # AI suggestions pre-approval
Decision          (Retrospective, text, source_draft?, confirmed_by, confirmed_at)
ActionItem        (Retrospective, description, owner?, due_date?, status: open|done,
                   discussion_topic?, source_draft?, confirmed_by, confirmed_at)
RetrospectiveSummary (Retrospective 1:1, body, published_at)
```

### Anonymity — enforced at the data layer

`FeedbackCard` has **no direct `author` FK**. Instead:

- `FeedbackCardAuthor` (Card 1:1, User) — a *separate* row that is only created for attributed cards.
- Anonymous card → no `FeedbackCardAuthor` row exists at all. There is nothing to hide and nothing to leak, for facilitators or admins.
- "Contributors can edit only their own feedback before reveal" is still possible for anonymous cards within the same session/browser via a signed `card_edit_token` stored client-side and on the card (hashed). After reveal, editing is closed for everyone, so the token stops mattering.
- Django admin never exposes authorship for anonymous cards because the join simply returns nothing.

### Visibility before reveal

Enforced in querysets, not templates:

- `FeedbackCard.objects.visible_to(user, cycle)` returns *only* the user's own cards while `cycle.status == collecting`.
- After `revealed`, all cards in the cycle are visible to all members.
- A single `require_cycle_status` / `require_retro_mode` guard decorator on facilitator-only transitions.

## Request & event flows

### Collect feedback
HTMX form per column → `POST` creates a `FeedbackCard` (+ `FeedbackCardAuthor` unless anonymous) → returns the new card fragment. No broadcast (others must not see it).

### Reveal
Facilitator `POST /retro/<id>/reveal` → `cycle.status = revealed`, `retro.mode = reveal`, kicks off async clustering suggestion → broadcast `retro.mode_changed`. All clients swap to the reveal view.

### Cluster
Clustering job (queued task + Claude) creates draft `Cluster` + `ClusterCard` rows. Drag/merge/split/rename hit minimal JSON endpoints; each mutation broadcasts `board.changed` with the affected cluster id(s); other clients `hx-get` the fragment.

### Vote
`POST` upserts `Vote` rows for the user (validated: total weight ≤ 3). No totals in any response until `retro.mode` leaves `vote` OR all members have voted → then broadcast `vote.closed` and everyone loads the ranked agenda. `DiscussionTopic` rows are generated from cluster vote sums at close.

### Discuss
Facilitator marks each `DiscussionTopic` discussed/skipped/deferred → broadcast `topic.changed`. Any member adds `Note` rows (note/decision/action) → broadcast `note.added`.

### Meeting upload → extraction
`POST` to `meetings/` saves the `MeetingRecord` (pasted text into `raw_text`; an uploaded file to a temp path) → queued job chain:
1. `transcribe` (skipped if transcript/text provided) → `Transcriber.transcribe(path) -> transcript_text`, then the temp file is deleted
2. `extract` → Claude returns decisions / action items / owners / due dates / summary → stored in `ExtractionDraft.payload`
3. status → `ready`, broadcast `meeting.ready`
Facilitator reviews the draft in a form; confirming promotes rows into `Decision` / `ActionItem` / `RetrospectiveSummary` with `confirmed_by`.

### SSE endpoint
`GET /events/retro/<id>` — long-lived `text/event-stream`. Auth-checked, membership-checked. Emits JSON `{type, ...ids}`. Client (Alpine) maps `type` → an `hx-get` on the relevant fragment. Heartbeat comment every ~20s. In-process `asyncio.Queue` / simple pub-sub now; Postgres `LISTEN/NOTIFY` or Redis pub-sub swap-in later.

## AI integration

All model calls live in `apps/ai/` and are called only from queued jobs, never inline in a view.

- **`Transcriber` protocol** — `transcribe(source: Path | str) -> str`. Implementations: `NullTranscriber` (dev/tests — echoes pasted text, raises for media) and `WhisperTranscriber` (OpenAI Whisper API, reads `OPENAI_API_KEY`). Nothing else in the codebase imports the OpenAI SDK. The API caps upload at 25 MB, so `WhisperTranscriber` transcodes/segments long audio with `ffmpeg` before sending; Whisper has no speaker diarization, so owner attribution rests entirely on the extraction step.
- **Clustering** — `suggest_clusters(cards) -> list[{title, card_ids}]`. Claude, single call, low temperature, JSON output validated against a schema. Output is *draft* rows the team edits.
- **Extraction** — `extract_outcomes(transcript, topics) -> {decisions[], actions[{description, owner_hint, due_date?}], summary}`. Owner matching: fuzzy-match `owner_hint` to project members, leave unresolved if uncertain. Everything lands in `ExtractionDraft`, nothing auto-published (plan decision).
- Prompts stored as versioned template files under `apps/ai/prompts/`.
- Costs/latency: both calls run in queued jobs, retried with backoff, and their status surfaces to the user via SSE.

## Permissions

Two roles via `Membership.role`:

- **member**: submit/edit own feedback, participate in clustering, vote, view published summaries, update action items they own.
- **facilitator**: everything a member can do, plus cycle create/close, reveal, mode transitions, meeting upload, draft review, summary publish.

Guard with a `@facilitator_required(project)` decorator + queryset scoping by membership. No object-level permission library needed at MVP size.

## Config / environment

`django-environ` reads: `DATABASE_URL`, `SECRET_KEY`, `DJANGO_SETTINGS_MODULE`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `TRANSCRIBER` (`null` | `whisper`), `MEDIA_TMP_DIR` (optional; defaults to the system temp dir), email backend vars. No Redis or storage-bucket config.

Dev: SQLite is *not* used (JSONB + Postgres-specific behavior) — local Postgres via `docker-compose` (Postgres only). Uploads go to a temp file and are deleted after transcription.

## Deployment shape (host chosen later)

Cloud-agnostic target = 3 things any host can provide:

1. **web** process — `gunicorn`/`uvicorn` running the Django app
2. **worker** process — `manage.py db_worker` (`django-tasks`)
3. **Postgres** (managed)

No Redis, no object storage. The worker image needs `ffmpeg` on `PATH` for Whisper audio transcoding. No scheduled/cron tasks in the MVP.

## Build sequence

1. Project skeleton, settings split, docker-compose (Postgres), `django-tasks` queue, base templates + HTMX/Alpine, auth (allauth), `common` base models.
2. `projects` + `accounts`: create project, invite/add members, roles, project page shell.
3. `cycles`: create cycle, feedback form (3 columns, multi-card, anonymous checkbox), per-user visibility, edit-own.
4. `realtime`: SSE endpoint + event bus + client wiring. Prove it with `retro.mode_changed`.
5. `retro` reveal + cluster: reveal transition, SortableJS board island, JSON move/merge/split/rename endpoints, broadcast + fragment refetch.
6. `retro` vote: stackable 3-vote logic, hidden totals, close conditions, ranked `DiscussionTopic` generation.
7. `retro` discuss: topic status, notes/decisions/actions capture.
8. `ai` clustering: queued task + Claude `suggest_clusters`, wired into step 5 as draft rows.
9. `meetings`: upload/paste, `MeetingRecord`, queued transcription job with `NullTranscriber`, `ExtractionDraft`.
10. `ai` extraction: Claude `extract_outcomes`, owner matching, draft review UI, confirm → `outcomes`.
11. `RetrospectiveSummary`: assemble, edit, publish; retrospective summary screen.
12. Polish: project page rollups (open actions, past retros), participation/attendance stats, empty states.
13. Swap `NullTranscriber` for `WhisperTranscriber`, add `ffmpeg` segmentation for long/large audio, set `TRANSCRIBER=whisper`.
14. Pick host, add web + `db_worker` process config and env wiring, first deploy.
