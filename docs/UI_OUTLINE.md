# UI outline

> **Status: skeleton.** The pages below are a starting proposal based on the MVP features. Each page becomes an **epic ticket** on the Kanban board; its features become **sub-tickets** we assign. Fill in the `> ✏️` prompts.

## Who uses it
> ✏️ Primary user: the agent, reviewing their own calls after a shift. Secondary: a coach/QA lead. Do we build coach views in the MVP, or agent-only?

## Pages

### Page 1: Call list (`/`) — exists as a basic table
**Purpose:** the agent sees their recent calls and picks one to review.
| Feature | What it does | Status |
|---------|--------------|--------|
| Call table | Call ID, task type, date, score | basic version built (no score/date yet) |
| Score badge | Score coloured by band | |
| Filter by task type / agent | | |
> ✏️ Anything else? Sort order? Empty state?

### Page 2: Post-call summary (`/calls/:callId`) — exists as transcript only
**Purpose:** the main coaching screen. What did I do, what did I miss, what's my score?
| Feature | What it does | Status |
|---------|--------------|--------|
| Step checklist | Each required step from the template: completed / missed | |
| Score | completed ÷ required, e.g. 3/4 = 75% | |
| Flags | Plain-language note for each missed step | |
| Evidence | Click a completed step → highlight the turn that proved it | |
| Transcript | Agent and customer turns | basic version built |
| Logged fields | What the agent captured (`captured_by_agent`) | basic version built |
> ✏️ Layout: checklist on the left, transcript on the right? Score at the top?

### Page 3: Progress (`/agents/:agentId/progress`)
**Purpose:** is my step-completion rate improving?
| Feature | What it does | Status |
|---------|--------------|--------|
| Completion-rate chart | Rate per coaching week | |
| Most-missed steps | Which steps I skip most often | |
| Per-task-type breakdown | | |
> ✏️ HVB only covers ~4 real days. How do we label synthetic coaching weeks honestly?

### Page 4 (optional): Templates (`/templates`)
**Purpose:** show the required steps for each task type, so agents (and Genesys) see what's being checked.
> ✏️ Read-only for MVP? Editable later ("configurable quality expectations")?

## Colours and what they mean

Values live in `frontend/src/index.css` as CSS variables. Change them there only.

| Token | Placeholder | Means | Used on |
|-------|-------------|-------|---------|
| `--color-completed` | green `#1a7f37` | step done | checklist, score ≥ ___% |
| `--color-missed` | red `#cf222e` | required step missed | checklist, flags, score < ___% |
| `--color-partial` | amber `#b26b00` | e.g. logged but never said aloud | checklist |
| `--color-accent` | blue `#2f5bea` | links, agent turns, primary buttons | everywhere |
| `--color-muted` | grey `#6b7280` | secondary text | metadata |
> ✏️ Decide score bands (e.g. green ≥ 90%, amber 60–89%, red < 60%). Don't use colour alone: pair it with an icon or word (✓ Completed / ✗ Missed) for colour-blind users.

## Ticket structure (for the Kanban board)

```
EPIC: Post-call summary page
 ├── Backend: GET /api/conversations/{id}/result returns step results + score
 ├── Frontend: StepChecklist component
 ├── Frontend: ScoreBadge component (uses colour tokens)
 ├── Frontend: highlight evidence turn in Transcript
 └── Design: layout sketch
```

> ✏️ Make one epic per page above, plus non-page epics: "Templates + scoring engine" (backend) and "HVB data ingest".
