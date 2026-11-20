# Contract: `GET /progress`

**Layer**: the route is the outer edge. It wires the use case for one request and returns the view model's body.

## Request

```text
GET /progress
GET /progress?agent_id=3
```

| Parameter | Required | Meaning |
| --- | --- | --- |
| `agent_id` | no | Count only this agent's calls. Left out: every agent's calls, as on `GET /calls`. |

The 8 weeks end with the week that contains "now". "Now" is `DEMO_TODAY` when the API was started with it, otherwise the real time.

## Response 200

Fields are in this order.

```json
{
  "demo_data": true,
  "weeks": [
    {"week_start": "2026-08-17", "steps_completed": 16, "steps_total": 25, "percent": 64, "is_current": false},
    {"week_start": "2026-10-05", "steps_completed": 53, "steps_total": 59, "percent": 90, "is_current": true}
  ],
  "this_week": {"steps_completed": 53, "steps_total": 59, "percent": 90},
  "first_week_percent": 64,
  "comparison": "Up from 64% in week 1",
  "call_types": [
    {"call_type": "check_balance", "name": "Check balance", "steps_completed": 42, "steps_total": 48, "percent": 88, "calls": 8}
  ],
  "steps": [
    {
      "step_key": "confirm_replacement",
      "name": "Confirm replacement",
      "call_type": "replace_card",
      "label": "Replace card",
      "results": ["completed", "missed", "completed", "missed", "missed"],
      "misses": 3,
      "window": 5,
      "summary": "Missed on 3 of your last 5 replace-card calls"
    },
    {
      "step_key": "offer_further_help",
      "name": "Offer further help",
      "call_type": null,
      "label": "All call types",
      "results": ["completed", "completed", "completed", "completed", "completed", "completed", "missed", "completed", "completed", "missed"],
      "misses": 2,
      "window": 10,
      "summary": "Missed on 2 of your last 10 calls"
    }
  ]
}
```

| Field | Notes |
| --- | --- |
| `demo_data` | `true` when any counted call was scored by the demo seed. |
| `weeks` | Always 8 items, oldest first. `week_start` is the Monday (UTC) as `YYYY-MM-DD`. `percent` is `null` when `steps_total` is 0. Exactly the last item has `is_current: true`. |
| `this_week` | The same shape and rule as `summary.this_week` on `GET /calls`. `null` when the current week has no scored call. |
| `first_week_percent` | The percent of the first of the 8 weeks that has a scored call. `null` when there is none. |
| `comparison` | This week against the first week, written by the server: `Up from N% in week 1`, `Down from N% in week 1` or `Same as N% in week 1`, where N is `first_week_percent`. `null` when `this_week` is `null`, its percent is `null`, or `first_week_percent` is `null`. |
| `call_types` | Only call types with scored calls. Highest percent first, then by name. |
| `steps` | Every step row, most misses first. `results` holds `completed`, `missed` or `wrong`, oldest first. `window` is the number of results. `call_type` is `null` and `label` is `"All call types"` for a shared step. |

`steps_total` means steps required: steps under review are not counted on either side.

With no scored call in the 8 weeks, the answer is 200 with 8 empty weeks, `this_week: null`, `first_week_percent: null`, `comparison: null`, empty `call_types` and `steps`, and `demo_data: false`.

## Errors

| Case | Status | Body |
| --- | --- | --- |
| `agent_id` is not a whole number | 422 | FastAPI's validation error |
| The shared rules file (`_common.json`) is missing | 503 | `{"detail": "missing rules file: <path> (set RULES_DIR)"}` |

## Unchanged

`GET /calls`, `POST /calls/{call_id}` and `GET /api/health` are not touched.
