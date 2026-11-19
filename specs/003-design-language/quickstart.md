# Quickstart: Design Language

How to check the feature works. See [contracts/ui-pieces.md](contracts/ui-pieces.md)
for the pieces and [data-model.md](data-model.md) for the band table.

## 1. Tests and type-check

```bash
cd frontend
npm test        # includes the 59 / 60 / 84 / 85 band edges and every stone state
npm run lint    # strict type-check
```

Expected: all tests pass, no type errors.

## 2. Look at it

```bash
docker compose up -d
```

Open http://localhost:5173/calls/1 (the call detail placeholder):

- The ring shows a number "of 100" with its band label and dot, and the band
  legend below it.
- The stone legend shows Completed (with a check), Missed (cracked), Wrong
  (X) and Under review (dashed).

Open http://localhost:5173/procedures: the procedure stone is plain brand
colour, the only stone with no mark.

## 3. Without colour

In the browser dev tools, emulate "achromatopsia" (Rendering → Emulate vision
deficiencies). All five stones must still be told apart (SC-001).

## 4. Screen reader text

Inspect a stone and the ring: the stone reads its state name, the ring reads
"Score N of 100, <band>" (SC-003).

## 5. Pull request

Add a screenshot of the pieces next to the Figma Foundations / Stone states
frame, and name the one intended difference: the check on completed (SC-004).
