# B2B Repositioning — Crisis Workshop Platform for Consulting Agencies

## 1. Who buys this

**ICP:** Boutique-to-mid-size crisis management / PR / corporate
communications consulting firms (e.g., agencies that currently run
in-person "crisis war room" tabletop exercises for corporate clients
using paper scripts, a whiteboard, and a facilitator with a stopwatch).

**Buyer:** Partner/Director at the consulting firm.
**User in the room:** The firm's own consultants acting as facilitator,
and the *client's* executives (CEO/PR/Legal/IR/HR) as participants.
**Not the buyer:** individual employees, students, or the corporate client
directly — they experience it, but the agency purchases and brands it.

## 2. Why this is a different product than the MVP

The current MVP is a **single-player learning toy**: one user clicks
through six phases solo against a scripted scenario, sees a score, done.
That's a portfolio demo, not something an agency can sell a $15-30K
workshop engagement around. Three things have to change:

| MVP today | What an agency needs |
|---|---|
| One user, one role | 4-6 simultaneous roles (CEO, PR, Legal, IR, HR) seeing different information and options, like a real war room |
| Generic seed scenarios | Agency uploads a **custom scenario** tailored to the specific client's industry/incident before the session |
| Demo-quality score screen | A **facilitator console** to run the live session, pause, inject curveballs, and a **branded PDF report** delivered to the client afterward as a deliverable |

The backend evaluator/scoring engine, the phase state machine, and the
case-reference logic do **not** change — they're the reusable core. What's
new is the session/role model and a facilitator layer on top.

## 3. Product structure (re-packaged)

```
Agency Admin Console          (new)
   ├── Client workspace management
   ├── Scenario builder/upload  (per-client custom crisis)
   ├── Branding (logo, report template)
   └── Usage/billing per workshop

Facilitator Console            (new)
   ├── Start/pause/inject events into a live multi-role session
   ├── See all roles' decisions in real time
   └── Trigger phase advance manually (not auto-timed)

Participant View               (extends current Crisis Room UI)
   ├── Role-scoped context: PR sees media questions, Legal sees liability framing, IR sees investor questions
   ├── Each role submits independently; evaluator scores the *combined* response
   └── Same score board, now shared/visible to whole room

Debrief Report                 (extends current Debrief screen)
   ├── White-labeled with agency + client logo
   ├── Per-role performance breakdown (not just one aggregate score)
   ├── Exportable PDF — this is the deliverable the agency hands the client
   └── Real-case benchmark comparison (existing feature, now framed as
       the agency's "expert analysis" value-add)
```

## 4. Required model/backend changes

`app/models/session.py` and `app/models/decision.py` already have
`role` and per-user fields started — extend rather than replace:

- `CrisisSession` gains `workshop_id`, `client_name`, `agency_id`,
  `roles: List[str]` (which roles are active in this run), and
  `decisions_by_phase: Dict[str, Dict[role, UserDecision]]` so the
  evaluator can score one phase only once all required roles have
  submitted (or facilitator forces advance).
- New `Scenario.custom` flag + an upload endpoint
  (`POST /api/scenarios/custom`) so agencies can submit their own
  YAML/JSON scenario instead of only picking from seed cases.
- New `Workshop`/`Agency` models for multi-tenant branding (logo URL,
  report template) and per-workshop billing metering.
- Evaluator prompt (`app/llm/prompts.py`) needs a role-aware variant:
  it should evaluate cross-role coherence too (e.g., did Legal's "no
  comment" contradict PR's public apology — that contradiction *is* the
  teaching moment in real workshops).

## 5. Packaging & pricing (recommended starting point)

| Tier | What | Price anchor |
|---|---|---|
| **Per-workshop license** | One custom scenario, one live multi-role session (up to 6 roles), one branded PDF report | $800–1,500 per session — agency resells to client at $5-15K as part of their engagement |
| **Agency seat license** | Unlimited workshops/month, scenario builder, white-label branding, usage dashboard | $1.5–3K/month per agency |
| **Enterprise (multi-consultant agencies)** | Multiple facilitators, client workspace isolation, SSO | Custom |

Anchor the per-workshop price *below* what the agency already charges per
in-person session (the value prop is "you 10x your delivery capacity, not
'we are cheaper than your time'").

## 6. Go-to-market wedge

Don't sell "AI crisis simulator" cold — sell **"run more workshops without
more facilitator hours."** A 2-person agency today can run maybe 2-3
in-person tabletop exercises a month, each requiring a senior consultant
in the room for 3-4 hours. This tool lets junior staff facilitate while
the AI does the scoring/feedback the senior consultant used to do
verbally — the senior consultant's judgment gets embedded in the
prompt/case library instead of re-explained live every time.

First wedge customers: agencies that *already* run tabletop exercises
manually (so no behavior change needed, just tooling) rather than
agencies that have never offered this service (longer sales cycle,
need to build the service line first).

## 7. What stays out of scope for v1 of the B2B pivot

- Public-facing self-serve signup (B2B sales-led, not PLG, at this stage)
- Real-time news monitoring / live social media ingestion
- The global crisis-case RAG layer (nice differentiator later, not
  needed to close the first 5-10 agency deals — the 5 seed cases plus
  custom scenario upload covers early sales conversations)

## 8. Immediate next build steps

1. Extend `CrisisSession` + `UserDecision` models for multi-role state
   (Section 4) — this is the one change that *must* happen before any
   agency pilot, since "I can only play one role" is the first thing a
   buyer will notice in a demo.
2. Add a custom scenario upload endpoint so the first pilot can use the
   agency's actual client scenario, not a US seed case.
3. Build a minimal facilitator console (even a single screen showing all
   roles' submission status + a manual "advance phase" button) — this is
   what makes it usable in a live room rather than solo.
4. Add PDF export of the debrief report with a logo placeholder — this is
   the deliverable the agency shows their own client as proof of value.
