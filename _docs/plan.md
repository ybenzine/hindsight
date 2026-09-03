# Weekly Project Retro Tool — Scope

_Last updated: 2026-09-03_

## Summary

A shared web app for running a weekly, per-project retrospective in the
**Start / Stop / Continue** format. There is **one board per project**, accessed
by a **shareable link** where people just enter a name to join. The board walks a
team through collecting feedback privately, revealing it all at once, clustering
and voting on topics, discussing them live, and recording the resulting decisions
and action items.

## Core decisions

- **Feedback flow:** Team → project. Each team member contributes to the project's weekly retro.
- **Format:** Start / Stop / Continue cards.
- **Board unit:** One board per project. Cards, votes, and history are scoped to that project.
- **Access:** Shareable link. People enter a name to join — no signup or login.
- **Anonymity:** Names appear by default; a contributor can mark any card anonymous.
- **Discussion:** Live meeting, using the board as the agenda.
- **Outcome captured:** Decisions and action items from the discussion (recorded only — see out-of-scope).

## The weekly flow

1. **Collect** — Each participant adds Start / Stop / Continue cards. Before the
   reveal, each person sees only their own cards. Name shows by default; any card
   can be marked anonymous.
2. **Reveal** — The facilitator triggers a reveal and all cards appear at the same time.
3. **Cluster** — The team groups related cards into topics.
4. **Vote** — Each person gets 3 votes to spend across topics, and may stack
   multiple votes on a single topic.
5. **Discuss** — Live meeting, working through topics in vote order.
6. **Record** — The team captures decisions and action items on the board.
   Recorded only: no owners, due dates, tracking, or carry-over.
7. **Attach (optional)** — After the meeting, the facilitator can upload audio,
   video, or a transcript. It is stored on the board as-is, with no processing.

## Roles

- **Facilitator** — Creates the board, shares the link, controls the reveal,
  guides clustering/voting/discussion, records decisions and action items, and
  can attach post-meeting media.
- **Participant** — Joins via link, adds cards (optionally anonymous), votes, and
  takes part in the discussion.

## Explicitly out of scope for v1

- Action-item tracking, ownership, due dates, or carry-over of open items to next week.
- Built-in recording (upload only; no in-app capture).
- AI summarization or transcription of uploaded media.
- Integrations (Asana / Jira / Linear / Slack, etc.).
- Accounts, SSO, or enforced identity.
- Cross-project dashboards, trends, or reporting.

## Open tensions to resolve before locking

- **Anonymity vs. link access.** With "enter a name to join," anonymous cards rely
  on the honor system — anyone with the link can join under any name. Fine for a
  trusting team, but anonymity is not enforced.
- **"Just record" decisions.** Recording action items with no owner or carry-over
  means nothing pulls last week's open items into this week. It's the lightest
  build, but action-item follow-through is the feature retros most often grow into.
  Straightforward to add later since history is stored per project.

## Likely next topics

- Data model (boards, cards, clusters, votes, decisions, action items, attachments).
- The facilitator's screen and the phase controls (collect → reveal → cluster → vote → discuss).
- How board state stays in sync across participants in real time.
