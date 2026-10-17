# UI outline

> **Status: draft.** The pages below come from our Figma file ([Stepping Stones — UI Mockup](https://www.figma.com/design/tgQYPY631Tg5njDsoBYGNJ/Stepping-Stones-%E2%80%94-UI-Mockup?node-id=12-99)). Each page becomes an **Epic** on the board, each section of the page a **Feature**, and each piece of work a **Task** (see "From outline to tickets" at the bottom). Fill in the `> ✏️` prompts.

## Who uses it
The **agent**, reviewing their own calls after a shift. Every page has the same left nav: **My calls · Progress · Procedures**, with the agent's name at the bottom.
> ✏️ Do coaches/QA get their own views in the MVP, or agent-only? How do we pick the agent without a login (dropdown? `?agent=` in the URL?)

## Pages

### 1. Home / Your week — Figma `129:332` (older version: `13:56`)
**Purpose:** the landing page. How am I doing this week, and what is the one thing to fix?
| Feature | What it does |
|---------|--------------|
| Weekly score card | Average call score this week (ring, out of 100), band, change from last week, calls reviewed |
| Tip card | The single highest-value fix ("This one step is worth 55 points…") with a link to its procedure |
| Your next steps | Steps missed most in the last 20 calls: stone history row, "Missed 3 of 6 calls", a tip |
| What you're doing well | Steps done consistently, streaks |
| Recent calls | Date, task type, score, band, one-line summary, link to Call review |
> ✏️ Owner: ______ · Which features are MVP vs later? Do we keep filters from the older `13:56` version (call type, has missed steps)?

### 2. Call review — Figma `62:76` (loading state: `20:316`)
**Purpose:** the core coaching screen for one call. What did I do, what did I miss, what's my score?
| Feature | What it does |
|---------|--------------|
| Header + score summary | Task type, call id, score ring (segments per step), "6 of 7 steps done right", points lost, plain-language summary |
| Transcript | Every turn with timestamp; evidence turns tinted green and labelled; wrong turns red with the reason |
| Required steps path | One stone per template step with its status |
| Step detail | Description, points by part, evidence quote, field check (caller asked vs logged), "Next time, say something like…" |
| Flags | One card per failed step with points lost |
| "I did do this" | Agent disputes a flag → step becomes Under review |
| Loading state | "Reviewing your call" animation |
> ✏️ Owner: ______ · MVP statuses: Completed/Missed only, or also Wrong / Under review?

### 3. Procedures — Figma `71:147` (older version: `13:334`)
**Purpose:** show the required steps for each call type, how many points each is worth, and what to say.
| Feature | What it does |
|---------|--------------|
| Procedure list | All 8 HVB task types with step counts (only transfer money is written so far) |
| How a call is scored | Explains the 100-point model and severity bands |
| Procedure steps | Step number, name, points chip, description, "Say something like", logged-field chips, parts |
> ✏️ Owner: ______ · Read-only for MVP? Do we show personal stats per step (from `13:334`)?

### 4. Progress — Figma `44:464`
**Purpose:** is my step-completion rate improving?
| Feature | What it does |
|---------|--------------|
| Step completion chart | % per week (synthetic weeks, labelled "Demo data") |
| By call type | Completion % per task type |
| Steps you skip most | One stone per call, oldest to newest, with a summary |
> ✏️ Owner: ______ · How do we label synthetic coaching weeks honestly?

### 5. Foundations (shared) — Figma `20:274`, `12:98`
**Purpose:** the shared design language every page uses.
| Feature | What it does |
|---------|--------------|
| App layout + nav | Left nav, page header, cards |
| Stone states | Completed (solid), Missed (cracked), Wrong (✕), Under review (dashed), Procedure step (brand teal). Shape carries the meaning, not just colour |
| Score bands | On track 85–100 · Getting there 60–84 · Focus here under 60 |
| Colour tokens | Exact values from Figma, stored in `frontend/src/index.css` |
> ✏️ Owner: ______

## Colours and what they mean
| Colour | Means | Used on |
|--------|-------|---------|
| Teal (brand) | Navigation, procedure steps, primary actions | Nav, Procedures |
| Green | Step completed · score "On track" | Stones, evidence turns, score chips |
| Amber / yellow | Tips · score "Getting there" | Tip card, score chips |
| Red | Step missed or wrong · score "Focus here" | Stones, flags, wrong turns |
| Grey dashed | Under review | Stones |
> ✏️ Copy the exact hex values from Figma.

## From outline to tickets
> ✏️ To be decided with the team (see the board guide, issue #17). Starting proposal:

```
EPIC      one per page above, plus system epics (Templates & data, Scoring, README, Board setup)
 └─ FEATURE   one per row in that page's feature table
     └─ TASK      one PR, one owner, 1–3 days (e.g. "Build StepStone component", "GET /api/conversations/{id}/result")
```
Use GitHub sub-issues to nest them, and labels `type: epic` / `type: feature` / `type: task` plus an area label (`frontend`, `backend`, `design`, `docs`).
