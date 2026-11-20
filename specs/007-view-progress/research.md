# Research: View Progress

Every Technical Context item was known. These decisions record the choices.

## R1. All nine CSC207 parts on the frontend

- **Decision**: all nine apply. They live in `frontend/src/progress/`, one per file. Boundaries and the data access interface are TypeScript `interface`s. The others are classes.
- **Rationale**: the product owner asked for the same parts as the backend, where they apply. A screen that loads data has a natural controller (open the page), interactor (load), presenter (shape for display) and view model (what the page draws).
- **Alternatives considered**: the shell's style, with one `resolveShellView` function and fetching inside `App.tsx`. It has no boundaries, and the component decides what to load and what to show.

## R2. The view model is a small observable store

- **Decision**: `ProgressViewModel` is a class holding one immutable `state`, with `setState(state)` and `subscribe(listener)`. The page reads it with React's `useSyncExternalStore`.
- **Rationale**: the presenter can update the view model without knowing React, and the page re-renders with a built-in hook. No state library is added.
- **Alternatives considered**:
  - The presenter calling a React `setState` passed into it: ties the presenter's lifetime to a component.
  - Redux or Zustand: a new dependency.

## R3. The typed gateway sits on the shell's `ApiGateway`

- **Decision**: `ProgressApi` in `progress/api.ts` implements `ProgressDataAccess`. It calls `gateway.get<ProgressDto>("/progress" or "/progress?agent_id=N")` and maps the snake_case DTO to camelCase entities. The DTO types are declared in `api.ts` and used nowhere else.
- **Rationale**: the shell already owns the base URL, sample mode and error text. Mapping in one file keeps transport names out of the presenter and the components (Principle VII).
- **Alternatives considered**: calling `fetch` directly, which would duplicate the shell's gateway and skip sample mode.

## R4. "Show all" is page state over two lists the presenter prepared

- **Decision**: the ready state carries `firstSteps` (the first `FIRST_STEP_ROWS` rows), `allSteps`, `showAllLabel` (for example "Show all 26 steps", or `null` when there is nothing more) and `showFewerLabel`. `ProgressPage` keeps one boolean (`expanded`) and renders one list or the other.
- **Rationale**: expanding a list is a display toggle with no data to load, so it needs no trip through the interactor. The component still does no slicing or counting: both lists and both labels come from the presenter.
- **Alternatives considered**: a second use case for the toggle (breaks the one-use-case rule for no gain), or slicing in the component (shaping in a component).

## R5. A badge without a new dependency

- **Decision**: add `components/ui/badge.tsx` in the shadcn/ui pattern (a `span` with `data-slot="badge"`, classes merged with `cn`), with one look.
- **Rationale**: shadcn's stock badge imports `class-variance-authority`, which is not installed. One look needs no variants, and a new package would need a constitution amendment (Principle V).
- **Alternatives considered**: installing `class-variance-authority`; styling a bare `span` inside the page (not a shared component).

## R6. Bars are plain elements

- **Decision**: each week bar is a `div` in a fixed-height column with `style={{ height: "64%" }}`. Each call type bar is a `div` with `style={{ width: "88%" }}`. The percent is also printed as text. The current week has the brand colour and the words "This week"; other weeks use the soft brand colour.
- **Rationale**: 8 bars and 8 rows need no chart library. Text beside every bar keeps the numbers readable without the graphic.
- **Alternatives considered**: Recharts or Chart.js (new dependency); SVG (more code for the same result).

## R7. Dates and wording in the presenter

- **Decision**: the presenter turns `"2026-08-17"` into `"Aug 17"` by splitting the string and using a fixed list of month names. It builds `"90%"` or `"–"`, `"53 of 59 required steps completed"` or `"No analysed calls this week"`, and `"42 of 48 steps"`. The comparison line and each summary line are passed through unchanged.
- **Rationale**: splitting the string avoids the browser's time zone moving a Monday to a Sunday. The sentences that carry judgment come from the server (feature 006).
- **Alternatives considered**: `Date` with `toLocaleDateString`, which depends on the viewer's time zone and locale.

## R8. Sample mode and the agent setting

- **Decision**: `gateway.ts` gets a sample answer for `/progress` and looks samples up by the path without its query string. `App.tsx` reads `VITE_AGENT_ID` and passes it to `createProgressScreen`. `.env.example` documents it.
- **Rationale**: the spec asks for sample mode and for the same agent setting as the calls page. Ignoring the query string lets `/progress?agent_id=3` use the sample.
- **Alternatives considered**: reading the setting inside `api.ts`, which would break the shell's rule that only `App.tsx` reads the environment.
