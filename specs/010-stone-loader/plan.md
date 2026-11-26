# Implementation Plan: Stone loading path

**Branch**: `feat/stone-loader` | **Date**: 2026-11-22 | **Spec**: [spec.md](./spec.md)

## Summary

Show a loading path. The call, progress, and procedures screens already have a loading state. Each one draws the same path of five stones, with the middle stone active, and the words "Finding your footing…". The screen's own loading sentence stays available to assistive technology. Nothing is scored and the model is not called.

## Technical Context

**Language/Version**: TypeScript 6, React 19
**Primary Dependencies**: Tailwind 4, the shared stone symbol
**Storage**: N/A
**Testing**: Vitest and Testing Library
**Target Platform**: The existing web app
**Project Type**: Web application
**Performance Goals**: The path is drawn from the loading state that already exists. It adds no request.
**Constraints**: Presentation only. Do not restyle scored screens, do not touch the older My calls page, and honour reduced motion.
**Scale/Scope**: Three loading states and one shared path.

## Constitution Check

| Principle | How this plan complies |
|-----------|------------------------|
| I. One use case, end to end | Show a loading path is the only use case. |
| II. Domain at the centre | No domain rule changes. The path does not judge a step. |
| III. Use cases do not know their callers | The path is drawn by the view from a sentence it is already given. |
| IV. Frontend never scores | The path replaces the look of a loading sentence. It does not compute a score or a status. |
| V. Small, tested, reviewed | One shared path, tested on its own, wired into the three screens. |

## Project Structure

### Documentation (this feature)

```text
specs/010-stone-loader/
├── plan.md
├── spec.md
├── tasks.md
└── checklists/requirements.md
```

### Source Code (repository root)

```text
frontend/src/components/pieces.tsx
frontend/src/components/pieces.test.tsx
frontend/src/index.css
frontend/src/callDetail/CallDetailPage.tsx
frontend/src/progress/ProgressPage.tsx
frontend/src/procedures/ProceduresPage.tsx
```

**Structure Decision**: The path lives next to the stone the app already draws. The three screens only swap their loading sentence for that path.

## Use Cases

### 1. Show a loading path

**Actor**: Agent
**Goal**: See the stepping-stone path while a screen is still loading.
**Input Port**: the loading sentence the screen already has
**Output Port**: a path of five stones, one active, the footing words, and the original sentence for assistive technology
**Flow**: The screen is loading, so it draws the shared path instead of a plain sentence. When the stored screen arrives, the path goes away. An error or an empty screen is unchanged.

## Complexity Tracking

No constitution violations.
