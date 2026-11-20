# Contract: App shell (UI)

What the shell exposes to people and to later screens.

## Addresses

| Address | Screen | Menu item marked | Content in this feature |
| --- | --- | --- | --- |
| `/` | My calls | My calls | Existing calls list, unchanged |
| `/calls/:callId` | Call detail | My calls | Placeholder naming the call id, back link to `/` |
| `/progress` | Progress | Progress | Placeholder |
| `/procedures` | Procedures | Procedures | Placeholder |
| anything else | My calls | My calls | Same as `/` |

## Menu

- Items in order: My calls, Progress, Procedures.
- The marked item has `aria-current="page"`.
- Footer shows `AgentProfile.name` and, if set, `role`.

## Shared pieces available to later screens

| Piece | Inputs | Guarantee |
| --- | --- | --- |
| `Stone` | `status`, optional `label`, `size`, `showLabel` | Distinct shape per status; text label always present (visible or screen-reader) |
| `StatusLegend` | none | The four call statuses with their stones and labels |
| `ScoreRing` | `value` (0–100 or null), `size` | Shows the given value; shows "–" for null; never computes |
| `PageHeader` | `title`, `subtitle?`, `back?` | Same layout on every screen |
| `Card` (shadcn) | children | Figma card style |
| `StateMessage` | `kind` (`"empty"` \| `"error"`), `title`, `message?` | Shared empty and error look; `kind="error"` has `role="alert"` |

## Configuration

| Setting | Default | Effect |
| --- | --- | --- |
| `VITE_API_URL` | `http://localhost:8000` | Base address for `createApiGateway` |
| `VITE_SAMPLE_DATA` | `false` | `true` → sample responses, no `fetch` |
| `VITE_AGENT_NAME` | (unset → "Agent") | Name in the menu |
| `VITE_AGENT_ROLE` | (unset → hidden) | Role in the menu |
