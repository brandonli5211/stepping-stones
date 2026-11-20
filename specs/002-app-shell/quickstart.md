# Quickstart: App Shell and Shared Screen Pieces

Validation guide. Contracts: [contracts/ui-shell.md](contracts/ui-shell.md).
Types: [data-model.md](data-model.md).

## 1. Unit tests and lint

From `frontend/`:

```bash
npm install
npm test
npm run lint
```

Expected: every test passes; `npm run lint` (strict type-check) reports
no errors.

## 2. Full stack

From the repository root:

```bash
docker compose up --build
```

Expected: http://localhost:5173 shows My calls inside the shell;
http://localhost:8000/api/health returns `{"status":"ok","database":"connected"}`.

## 3. Navigation (User Story 1)

1. Click Progress, then Procedures, then My calls. Each time the matching
   menu item is marked.
2. Open http://localhost:5173/calls/7. Call detail shows "Call 7", My calls
   stays marked, and the back link returns to `/`.
3. Open http://localhost:5173/nowhere. My calls shows.
4. The menu footer shows the configured agent name and role ("Agent" when
   unset).

## 4. Stones (User Story 2)

On Progress and Procedures (placeholders) the legend shows Completed, Missed, Wrong and
Under review. Switch the browser to grayscale (DevTools → Rendering →
Emulate vision deficiencies → Achromatopsia): each stone is still
distinguishable by shape and label.

## 5. Sample data mode (User Story 3)

Covered by the `createApiGateway` unit tests: with `VITE_SAMPLE_DATA=true`
the gateway answers `/calls` from sample data and `fetch` is never called;
with it unset, `fetch` is called with `VITE_API_URL` + path.
