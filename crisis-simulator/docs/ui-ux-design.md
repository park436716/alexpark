# AI Crisis Simulator — UI/UX Design

This is the screen-by-screen and interaction design for the product, built
on top of the backend in `../backend` and prototyped in `../demo.html`.

## 1. Design goals

1. **Pressure, not clutter.** A real crisis room feels tense and
   time-boxed. The UI should communicate urgency (countdown, rising
   media-pressure bar) without becoming noisy or game-like.
2. **Decisions are the product.** Every screen should funnel toward one
   action: "what do you do next." Scores and stakeholder reactions are
   *consequences*, shown after the decision, never before — otherwise
   users optimize for the scoreboard instead of judgment.
3. **Numbers need an instant read.** A user must understand "good" vs
   "bad" within 200ms — color and direction of the bar, not just digits.
4. **Debrief is the retention hook.** The "aha" moment is the post-game
   report comparing the user's path to the real historical case. This
   screen should be the most polished, shareable one.

## 2. User flow (screen map)

```
[Landing / Scenario Picker]
        │ select scenario + role
        ▼
[Briefing Screen]  ── one-time, sets context & stakes
        │ "Start"
        ▼
[Crisis Room] ◄────────────────────┐
   ├─ Situation panel               │
   ├─ Score board                   │
   ├─ Decision panel (options/free) │
   │     │ submit                   │
   │     ▼                          │
   ├─ Feedback panel (modal/inline) │
   │     │ "Next phase" ────────────┘  (loops until last phase)
   ▼
[Debrief Report]
   ├─ Score timeline chart
   ├─ Decision history
   ├─ Real-case comparison
   └─ Share / Restart / Try another scenario
```

State only moves forward (no back button inside a run) — this mirrors
real crises, where you can't undo a public statement. A visible "Restart"
always exits to the picker.

## 3. Screen specs

### 3.1 Scenario Picker (landing)

**Purpose:** low-friction entry, sets expectations on difficulty/role.

Layout: a grid of scenario cards, not a dropdown (the current `demo.html`
uses a `<select>` — fine for a dev prototype, but the real UI should use
cards so users can scan industry/difficulty/crisis type at a glance).

Each card:
```
┌─────────────────────────────┐
│ [industry icon]   [difficulty dot] │
│ Viral Passenger Removal Crisis      │
│ Airline · Customer Abuse            │
│ "A passenger removal video is...    │
│  spreading on social media."        │
│ Reference: United Airlines 2017     │
│ [ Start as: PR Lead ▾ ]             │
└─────────────────────────────┘
```
- Difficulty dot: green (easy) → amber (medium) → red (hard/expert).
- Role selector lets the same scenario be played as CEO / PR / Legal / IR
  (changes which decision options are offered — Level 1 of the roadmap).
- Clicking the card (not just the button) opens a brief detail
  drawer before committing, so users aren't surprised mid-crisis.

### 3.2 Briefing Screen

**Purpose:** one beat of stakes-setting before the clock starts. Prevents
the jarring feeling of being dropped into scores with no context.

```
┌──────────────────────────────────────────┐
│  PHASE 0 · T+0:00                         │
│                                            │
│  You are the Crisis Response Lead.        │
│                                            │
│  A passenger removal video is spreading   │
│  rapidly on X and TikTok. 4.5M views in   │
│  two hours. The passenger is injured.     │
│  The CEO has not yet been briefed.         │
│  Reporters are requesting comment.         │
│                                            │
│  Your decisions will be evaluated on:     │
│  speed · empathy · legal prudence ·       │
│  stakeholder trust · long-term reputation │
│                                            │
│              [ Begin Response ]            │
└──────────────────────────────────────────┘
```
A subtle pulsing dot or "LIVE" badge near the timestamp signals that the
clock is about to start — this is the only screen allowed to feel calm.

### 3.3 Crisis Room (core loop screen)

This is where 90% of time is spent. Three-zone layout (desktop):

```
┌─────────────────────────────┬───────────────┐
│ SITUATION (left, 60%)        │ SCORE BOARD   │
│                               │ (right, 40%)  │
│ Phase badge + elapsed time    │ 6 score tiles │
│ Context text                  │ stacked       │
│ Case-similarity tags          │               │
│                               ├───────────────┤
├───────────────────────────────┤ STAKEHOLDER   │
│ DECISION PANEL (full width)   │ PULSE (mini)  │
│ Option A/B/C/D buttons        │ 5 small rows  │
│ — or — free-text box          │ updated after │
│ [Submit Response]             │ each decision │
└───────────────────────────────┴───────────────┘
```

Mobile: stack vertically in this order — phase badge → context →
score board (collapsed to a horizontal strip of 6 mini-gauges, tap to
expand) → decision panel.

**Phase badge:** `Phase 2/6 · 6h Media Escalation` plus a thin progress
bar across the top of the screen (not a countdown timer — there's no real
time pressure in the MVP, but the bar communicates "you are this far into
the crisis").

**Decision panel interaction states:**
1. Default: 4 option buttons + free-text textarea, both enabled.
2. On submit: panel disables, shows a 1-2s "Evaluating response..."
   skeleton/spinner state (this is where the real OpenAI call happens —
   never let it look frozen with no feedback).
3. Replaced by Feedback panel.

Decision is **never both** option-click and free-text simultaneously —
clicking an option immediately submits (it's a complete decision);
free-text requires the explicit submit button. This avoids accidental
double-submits.

### 3.4 Feedback Panel

Appears in place of the decision panel (not a blocking modal — keep the
score board visible so the user sees numbers move in real time).

```
┌──────────────────────────────────────────┐
│  72 /100  decision quality                │
│                                            │
│  ✓ Strengths                               │
│    • Acknowledged personal harm            │
│    • Committed to a follow-up timeline     │
│                                            │
│  ✗ Weaknesses                              │
│    • No concrete compensation principle    │
│    • Internal accountability unclear       │
│                                            │
│  Stakeholder reactions                     │
│    Media      "Apology lacks specifics"    │
│    Customers  "Unclear victim protection"  │
│    Employees  "Frontline guidance unclear" │
│    Regulators "Likely to request a report" │
│    Investors  "Limited near-term concern"  │
│                                            │
│  → Recommended next move:                  │
│    Issue a victim-centered holding         │
│    statement within one hour.              │
│                                            │
│              [ Continue to Phase 3 ]        │
└──────────────────────────────────────────┘
```
- Score deltas animate **on the score board**, not here: each tile briefly
  shows `+8` / `-12` in red/green next to the number, then the bar slides
  to the new width. This is the single most important micro-interaction in
  the product — it's the "did I do well" payoff.
- Strengths in green check, weaknesses in red cross — never more than 3
  bullets each, or it reads as a wall of text under pressure.

### 3.5 Debrief Report (end screen)

**Purpose:** the shareable summary; also the natural place to introduce
real-case RAG comparisons (Phase 2 of the roadmap).

```
┌──────────────────────────────────────────┐
│  Crisis Resolved · Avg quality: 74/100     │
│                                            │
│  [ Score timeline — line chart, 6 lines,   │
│    one per metric, x-axis = phases ]       │
│                                            │
│  Your path vs. United Airlines (2017):     │
│  ───────────────────────────────────────   │
│  You apologized 40min faster than the      │
│  real case, but the real case eventually   │
│  offered compensation — you did not.       │
│                                            │
│  Decision log                              │
│  Phase 1  (88) "Apologized directly..."   │
│  Phase 2  (61) "Issued a holding..."      │
│  ...                                       │
│                                            │
│  [ Share report ]  [ Replay scenario ]     │
│  [ Try another scenario ]                  │
└──────────────────────────────────────────┘
```
"Share report" exports a static image/PDF card (score + one-line verdict)
— this is the growth loop, so it deserves its own visual template
separate from the in-app debrief.

## 4. Visual design system

Carried over from `demo.html` (dark, "crisis room" aesthetic — feels like
a NOC/SOC dashboard, not a consumer app):

| Token | Value | Use |
|---|---|---|
| `--bg` | `#0f1115` | App background |
| `--card` | `#1a1d24` | Panel background |
| `--border` | `#2a2e37` | Card borders, dividers |
| `--text` | `#e8e9ec` | Primary text |
| `--muted` | `#9aa0ab` | Labels, secondary text |
| `--good` | `#1a8a3d` | Improving metric, strength |
| `--bad` | `#d92626` | Worsening metric, weakness |
| accent | `#3b6ef0` | Primary CTA buttons |

Typography: system UI font stack (no custom font load — speed matters
more than brand polish at MVP stage). Score values at 22-32px bold;
everything else 12-14px. Generous line-height (1.5-1.7) on context text
since users are reading under simulated pressure and need it scannable.

**Score tile color logic** (already implemented in `demo.html`'s
`renderScoreboard`): metrics where high = good (`reputation`,
`employee_trust`) turn green above 50, red below; risk metrics
(`legal_risk`, `media_pressure`, `regulatory_risk`, `financial_risk`)
invert — green when *low*. Never use a single fixed color scale across
all six tiles, or users will misread risk tiles as "good when full."

## 5. Key interaction principles

- **No premature scoring.** Score deltas only appear after a decision is
  submitted — never show a live preview of "this choice will cost you 8
  reputation points," or the game becomes a min-max puzzle instead of a
  judgment exercise.
- **Irreversibility.** No back button mid-run. Decisions are appended to
  history and shown in the debrief, mistakes included — that's the
  learning point.
- **Latency honesty.** The LLM call takes 1-3s. Always show a
  state-aware loading affordance scoped to the decision panel, never a
  full-page spinner that hides the score board.
- **Stakeholder reactions as quotes, not stats.** Five short quoted lines
  read faster than five more numeric gauges, and reinforce that this is
  about people's reactions, not just a meter.
- **Accessibility:** color is never the only signal — pair every
  delta/red/green with a `+`/`-` sign and an up/down arrow glyph, and
  ensure all text meets 4.5:1 contrast against `--bg`/`--card`.

## 6. Responsive breakpoints

| Breakpoint | Layout |
|---|---|
| `>= 1024px` | 3-zone grid described in 3.3 |
| `640–1023px` | Situation full width on top, score board as 2-column grid below, decision panel below that |
| `< 640px` | Single column; score board collapses to a horizontal scroll strip of 6 compact gauges; feedback panel stakeholder quotes become a swipeable carousel |

## 7. Components to build (maps to `frontend/components/`)

| Component | Notes |
|---|---|
| `ScenarioCard.tsx` | Picker grid item — industry icon, difficulty dot, role selector |
| `BriefingScreen.tsx` | One-shot intro, "Begin Response" CTA |
| `CrisisScoreBoard.tsx` | Already scaffolded — extend with delta-flash animation |
| `DecisionPanel.tsx` | Option buttons + free-text, disabled/loading state machine |
| `FeedbackPanel.tsx` | Strengths/weaknesses, stakeholder quote rows, recommended action |
| `StakeholderFeed.tsx` | Reusable quote-row list (used in feedback + debrief) |
| `DebriefReport.tsx` | Score timeline chart, decision log, real-case diff, share card |
| `PhaseProgressBar.tsx` | Thin top-of-screen progress indicator |

## 8. Out of scope for MVP UI

Multiplayer role views (CEO/PR/Legal/IR seeing different panels
simultaneously), live news ticker, voice briefing, and the global-case RAG
comparison UI (beyond the one-line debrief diff) are deferred — see
`README.md`'s MVP scope section.
