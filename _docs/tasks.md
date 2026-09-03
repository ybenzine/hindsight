# Backlog — Hindsight

Tasks are sized for a single session. Each is written to be picked up without
reading the others; shared context lives in [`plan.md`](./plan.md) and
[`architecture.md`](./architecture.md). Later tasks assume the models and apps
from earlier ones exist, but each description states what it needs.

---

## 1. Scaffold Django project with a passing test
Goal: An empty, runnable Django project with one green test.
Description: Create the `config/` project and a `pytest` (or Django test runner) setup with a single trivial test that asserts the app imports and the home URL returns 200. Add `requirements.txt`/`pyproject.toml`, a `.gitignore` for Python, and a README section on how to run the server and the tests. No apps or models yet.

## 2. Settings split, environment config, and local infrastructure
Goal: Environment-driven settings plus a one-command Postgres stack.
Description: Split `config/settings.py` into `base.py`/`dev.py`/`prod.py`, load values with `django-environ` from `DATABASE_URL`, `SECRET_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `TRANSCRIBER`, and email vars, and commit a `.env.example`. Add a `docker-compose.yml` with a Postgres service whose port and credentials match `.env.example`, and document up/down. Confirm `manage.py migrate` and the existing test run against the containerised Postgres under `dev` settings.

## 3. Background task queue
Goal: A database-backed job queue with a worker process and no extra services.
Description: Add `django-tasks` with its database backend, register the `manage.py db_worker` process in the docs, and configure tasks to run synchronously under tests. Include one example `@task` plus a test that enqueues and runs it. This queue is what every later async job (clustering, transcription, extraction) uses; no domain tasks yet.

## 4. Base templates and common app helpers
Goal: A shared layout with HTMX/Alpine loaded and reusable base-model helpers.
Description: Create `templates/base.html` with blocks for title, content, and scripts, a minimal CSS reset, and a static-files setup, and load HTMX and Alpine.js with a tiny fragment-swap demo that proves the wiring. In the same pass add `apps/common/` with an abstract `TimeStampedModel` (created/updated) plus any shared view mixins or template tags, tested via a throwaway concrete model. No domain models.

## 5. Custom User model
Goal: An email-keyed `User` model in place before any migrations depend on it.
Description: Add `apps/accounts/` with a custom `User` model that uses email as the login field and drops username, along with its manager, admin registration, and factory/fixtures for tests. Set `AUTH_USER_MODEL` and generate the initial migration. No auth views yet — that is the next task.

## 6. Authentication flows with allauth
Goal: Users can sign up, log in, log out, and reset their password.
Description: Configure `django-allauth` for email/password signup, login, logout, and password reset, and style the auth templates with the base layout. Add a post-login landing redirect and a nav auth menu. Cover signup, login, and logout with tests. Assumes the custom `User` model from task 5 exists.

## 7. Projects and membership models
Goal: Data model for projects and who belongs to them.
Description: Create `apps/projects/` with `Project` and `Membership` (User × Project, `role` of `member` or `facilitator`, `is_active`). Add model methods for "is this user a facilitator of this project" and a manager method to list a user's active projects. Include migrations and model tests; no views.

## 8. Project creation and member management UI
Goal: A user can create a project and add, re-role, or deactivate members.
Description: Add views and templates to create a project (creator becomes facilitator), list its members, add a member by email, change a member's role, and deactivate a member, with member management restricted to facilitators via a queryset/permission check. Keep each action a small focused view. Assumes `Project` and `Membership` from the projects app exist.

## 9. Project page shell
Goal: The main project screen with placeholder sections.
Description: Build the project detail page with clearly separated regions for current feedback cycle, submission status, active/upcoming retrospective, previous retrospectives, and open action items — each rendered as an empty-state placeholder for now. Wire routing and a project switcher in the nav. Later tasks fill each region.

## 10. Feedback cycle and card models
Goal: Data model for a weekly cycle and its Start/Stop/Continue cards.
Description: Create `apps/cycles/` with `FeedbackCycle` (Project, `status` of `collecting`/`revealed`/`closed`, facilitator, opened_at) and `FeedbackCard` (Cycle, `column` of `start`/`stop`/`continue`, text, created_at). Add a constraint that a project has at most one non-closed cycle. Include migrations and model tests; no author link yet (see task 11).

## 11. Anonymity data structure
Goal: Attribution that is structurally absent for anonymous cards.
Description: Add `FeedbackCardAuthor` (FeedbackCard 1:1 → User) so an attributed card has a row and an anonymous card has none, plus a hashed `card_edit_token` on `FeedbackCard` for anonymous authors to edit their own card before reveal. Provide helper methods `card.author` (returns None when anonymous) and `card.can_be_edited_by(user, token)`. Cover both attributed and anonymous paths with tests.

## 12. Feedback form UI
Goal: Team members submit multiple Start/Stop/Continue cards with an anonymous option.
Description: Build the three-column feedback form where each column lets a user add several short cards via HTMX, each with an "anonymous" checkbox, and edit or delete their own cards. On submit, create the `FeedbackCard` and, unless anonymous, a `FeedbackCardAuthor` row. Assumes the cycles app and the anonymity structure exist.

## 13. Pre-reveal visibility enforcement
Goal: Before reveal, a contributor sees only their own feedback.
Description: Add `FeedbackCard.objects.visible_to(user, cycle)` returning only the user's own cards while the cycle is `collecting` and all cards once `revealed`, and route every feedback view through it. Add a guard so editing cards is closed once the cycle leaves `collecting`. Test the boundary in both cycle states.

## 14. SSE endpoint and event bus
Goal: A live event stream per retrospective.
Description: Create `apps/realtime/` with a `GET /events/retro/<id>` view that returns `text/event-stream`, checks membership, emits JSON `{type, ...ids}` events, and sends a heartbeat comment periodically. Back it with a simple in-process publish/subscribe bus and a documented seam for swapping to Postgres `LISTEN/NOTIFY` (or Redis) later. Test that a published event reaches a connected consumer.

## 15. Client-side SSE wiring
Goal: Browser reacts to server events by refetching the right fragment.
Description: Add a small Alpine component that opens the SSE connection, maps each event `type` to an `hx-get` on the affected DOM fragment, and reconnects on drop. Include a demo page that flips a value server-side and shows every connected client updating. Assumes the SSE endpoint from task 14 exists.

## 16. Retrospective, cluster, and cluster-card models
Goal: Data model for the retrospective board.
Description: Create `apps/retro/` with `Retrospective` (Cycle 1:1, `mode` of `reveal`/`cluster`/`vote`/`discuss`/`summary`), `Cluster` (Retrospective, title, order), and `ClusterCard` (Cluster, FeedbackCard, order) where a card in no cluster is "ungrouped". Add helper queries for grouped and ungrouped cards. Include migrations and model tests; no views.

## 17. Reveal transition and mode state machine
Goal: The facilitator reveals feedback and moves the retrospective between modes.
Description: Add facilitator-only endpoints to start the retrospective (sets cycle to `revealed`, mode to `reveal`) and to advance/return between `reveal`, `cluster`, `vote`, `discuss`, and `summary`, validating allowed transitions. Broadcast a `retro.mode_changed` event on each change. Assumes the retro models and the realtime event bus exist.

## 18. Cluster board island with move endpoint
Goal: Drag cards between clusters on a live board.
Description: Build the cluster-mode board using SortableJS, with a minimal JSON endpoint that persists a card moving to a target cluster and position. After a successful move, publish a `board.changed` event so other clients refetch the affected columns. Assumes `Cluster`/`ClusterCard` models and the SSE wiring exist.

## 19. Cluster merge, split, and rename endpoints
Goal: Reshape clusters during the cluster phase.
Description: Add JSON endpoints to rename a cluster, merge two clusters into one (moving all cards), and split selected cards out into a new cluster. Each mutation publishes `board.changed` for the affected cluster ids. Assumes the cluster board and models from tasks 16 and 18 exist.

## 20. Vote model and stackable three-vote logic
Goal: Each member has three votes they can stack on clusters.
Description: Add `Vote` (Retrospective, User, Cluster, weight) with a service that upserts a user's votes and rejects any change that would push their total weight above three. Provide `cluster.vote_total()` and `retro.user_votes(user)`. Cover the over-limit and re-allocation cases with tests; no UI.

## 21. Voting UI with hidden totals and close conditions
Goal: Members vote without seeing totals until voting closes.
Description: Build the vote-mode screen where a member allocates up to three votes across clusters and sees only their own allocation. Close voting when every active member has voted or the facilitator ends it, then broadcast `vote.closed` so all clients load results. Assumes the vote logic from task 20 and the realtime wiring exist.

## 22. Discussion topic generation from votes
Goal: Turn ranked clusters into an ordered discussion agenda.
Description: Add `DiscussionTopic` (Retrospective, Cluster, rank, `status` of `pending`/`discussed`/`skipped`/`deferred`) and generate one topic per voted cluster, ranked by total vote weight, when voting closes. Re-running generation should be idempotent. Include tests for ranking and tie handling; no UI beyond a simple ordered list.

## 23. Discuss mode topic status transitions
Goal: The facilitator works through topics and marks each outcome.
Description: Build the discuss-mode view listing topics in rank order with facilitator-only controls to set each to discussed, skipped, or deferred, broadcasting `topic.changed` on each update. Show current status to all participants live. Assumes `DiscussionTopic` from task 22 and the realtime wiring exist.

## 24. In-meeting notes, decisions, and actions capture
Goal: Participants record notes, decisions, and action items during the meeting.
Description: Add a `Note` model (Retrospective, author, body, `kind` of `note`/`decision`/`action`, created_at) and a form on the discuss screen to add entries, optionally tied to the current topic. Broadcast `note.added` and append the entry live for all participants. These are manual entries, separate from the later AI extraction.

## 25. AI app with Claude client and Transcriber interface
Goal: A single place for model calls and a swappable transcription seam.
Description: Create `apps/ai/` with a thin Claude client wrapper (reads `ANTHROPIC_API_KEY`, one method that takes a prompt template plus context and returns validated JSON), a `prompts/` directory of versioned prompt files, and a `Transcriber` protocol with a `NullTranscriber` that echoes pasted text and raises for media (the real Whisper implementation lands in task 28). Only the Anthropic SDK is imported here. Unit-test the wrapper with the network mocked.

## 26. Clustering suggestion task
Goal: AI proposes an initial set of clusters for revealed feedback.
Description: Add a queued task that takes a cycle's revealed cards, calls Claude via the AI app to get `[{title, card_ids}]`, and creates draft `Cluster` and `ClusterCard` rows, leaving unmatched cards ungrouped. Trigger it on the reveal transition and make re-running safe. Assumes the AI app, the retro models, and the task queue are set up.

## 27. Meeting record model and upload UI
Goal: The facilitator submits a meeting recording or transcript.
Description: Create `apps/meetings/` with `MeetingRecord` (Retrospective, `upload_kind` of audio/video/transcript_file/pasted_text, raw_text, transcript_text, `status`) and a page to upload a file or paste text. An uploaded file is written to a temporary path for processing only and is never persisted to storage; pasted text goes straight into `raw_text`. Show current processing status. No transcription or extraction yet.

## 28. Transcription pipeline with OpenAI Whisper
Goal: An uploaded recording is transcribed, then the file is discarded.
Description: Add a queued job that moves `MeetingRecord.status` through `transcribing` and produces `transcript_text` — using pasted/file text directly, or a new `WhisperTranscriber` (OpenAI Whisper API, reads `OPENAI_API_KEY`) for audio/video — then deletes the temp file, marks the record ready, and broadcasts `meeting.ready`. Guard the 25 MB API limit and, on any failure, set status to `failed`. Assumes the meetings app, the `Transcriber` interface, the task queue, and the realtime bus exist.

## 29. Outcome extraction task
Goal: AI drafts decisions, action items, and a summary from the transcript.
Description: Add an `ExtractionDraft` (MeetingRecord 1:1, JSONB payload, confirmed_at) and a queued job that sends the transcript and the discussion topics to Claude and stores `{decisions[], actions[{description, owner_hint, due_date?}], summary}` in the payload. Nothing is published — the draft is for review only. Assumes the AI app and the meetings pipeline exist.

## 30. Owner matching for extracted action items
Goal: Map extracted owner hints to real project members.
Description: Add a service that fuzzy-matches each action's `owner_hint` against the project's members and attaches a resolved user id, or leaves it unresolved when the match is weak. Expose the match confidence in the draft payload so the review UI can flag uncertain ones. Cover exact, partial, and no-match cases with tests.

## 31. Extraction draft review UI
Goal: The facilitator edits AI suggestions before anything is saved.
Description: Build a review screen that renders the `ExtractionDraft` payload as editable rows for decisions and action items (text, owner, due date), with a per-row accept/edit/discard state and a visible flag on owner matches marked uncertain. Persist the reviewer's edits back onto the draft without promoting anything yet. Assumes the extraction draft and owner matching from tasks 29 and 30 exist.

## 32. Confirm and promote drafts into decisions and action items
Goal: Confirming a reviewed draft creates the real records.
Description: Add the confirm action that takes the accepted rows of an `ExtractionDraft` and creates `Decision` and `ActionItem` records with `confirmed_by`/`confirmed_at`, then marks the draft confirmed so it cannot be promoted twice. Handle the empty-selection and re-confirm cases. Assumes the review UI from task 31 and the outcomes models from task 33 exist.

## 33. Decision and action item models with owner updates
Goal: Persistent decisions and accountable action items.
Description: Create `apps/outcomes/` with `Decision` (Retrospective, text, confirmed_by/at) and `ActionItem` (Retrospective, description, owner, optional due_date, `status` of open/done, optional discussion_topic). Add a view for an owner to toggle their own action between open and done. Include migrations and tests; bulk creation happens via task 32.

## 34. Retrospective summary model and publish flow
Goal: Assemble, edit, and publish the final retrospective summary.
Description: Add `RetrospectiveSummary` (Retrospective 1:1, body, published_at) that is pre-filled from the top topics, confirmed decisions and actions, and the AI summary text, then edited by the facilitator and published. Publishing makes it visible to all members. Cover the pre-fill and publish steps with tests.

## 35. Retrospective summary screen
Goal: The read view of a completed retrospective.
Description: Build the summary page showing top discussion topics, key notes, confirmed decisions, confirmed action items, attendance and participation, and the original feedback cards. Link to it from the project page's previous-retrospectives list. Assumes the summary, outcomes, notes, and cycle data exist.

## 36. Project page rollups and participation stats
Goal: Fill the project page regions with live data.
Description: Replace the placeholders on the project page with the current cycle and submission count, the active or upcoming retrospective, previous retrospectives, and open action items across the project. Add a small participation calculation (share of invited members who submitted, share of retrospectives completed). Assumes cycles, retro, and outcomes data exist.
