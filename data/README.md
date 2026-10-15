# data/

Input data that gets loaded into Postgres by `backend/scripts/seed.py`.

| File | What it is |
|------|------------|
| `sample_calls.json` | Two tiny calls in the Genesys curated HarperValleyBank (HVB) shape, so everyone can run the app without downloading the full dataset. |

- `HVB-0001` is the trimmed sample call from our project context (replace card, scores 4/4).
- `DEMO-0002` is **hand-written for testing**, not a real HVB call. It is a transfer-money call where the agent logs the transfer but never confirms it out loud — useful later for testing the "missed step" flag.

## Fields we read

Only these fields are used by the loader. Do not add fields that are not in the real HVB curated files.

| JSON field | Goes into |
|------------|-----------|
| `id` | `conversations.id` |
| `agent_id` | `conversations.agent_id` |
| `source_fields.task_assigned[0]` | `conversations.task_type` |
| `customer_record.captured_by_agent` | `conversations.captured_by_agent` (JSONB) |
| `turns[].n`, `speaker`, `text`, `dialog_acts` | one row each in `turns` |

## Loading the full HVB dataset (next step, not done yet)

Source: <https://github.com/cricketclub/gridspace-stanford-harper-valley> (Wu et al. 2020, CC BY 4.0), or the curated files in the Genesys partner repo: <https://github.com/marcomarchesanogenesys/uoft-ftli-2026-genesys-docs>. Raw data files should **not** be committed if they're large — add them to `.gitignore` and document where to download them.
