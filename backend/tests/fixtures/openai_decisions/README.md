# OpenAI Decisions debug samples

These request/response JSON files are **test and debugging fixtures only**.
They are not SQL seed data and are never loaded into the application database.

The production adapter sends the same shape to OpenAI's Decisions endpoint. Do
not put API keys, customer transcripts, or other sensitive data in this folder.

Compound-step debug responses include combined `answers` and original
`responses` grouped by `step_observation`, `request`, and `read_back`.
Each group retains the provider's confidence values. Field facts below 0.70
leave their dependent checks under review. Turn observations use 0.80.
