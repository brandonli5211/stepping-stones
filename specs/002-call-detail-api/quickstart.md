# Quickstart: Call Detail API

**Feature**: [spec.md](spec.md) · **Contract**: [contracts/get-call-detail.md](contracts/get-call-detail.md)

How to check the feature once it is built. Uses the existing Docker Compose
stack and uv commands (constitution Principle V).

## 1. Run the unit tests

```bash
cd backend && uv run test
```

Expect the new tests to pass:

- `tests/test_domain_call_detail.py`: score 45, 6 of 7, 55 lost, 1 critical,
  the "Wrong" note on turn 9 (33.53 s), the three-row field table for
  `HVB-DEMO-06`; score 100, no flags, no "Wrong" notes, empty block for the
  check-balance call; provisional score when a step is under review.
- `tests/test_get_call_detail.py`: the use case returns a detail for a stored
  call and raises `CallNotFound` otherwise; it imports no framework.
- `tests/test_call_detail_route.py`: the route returns the typed body and
  turns `CallNotFound` into 404; it runs no SQL itself.
- `tests/test_call_detail_repository.py`: rows map to domain records.

## 2. Try it against the running stack

```bash
docker compose up -d
```

```bash
cd backend && uv run migrate
```

```bash
curl -s localhost:8000/calls?limit=1 | python3 -m json.tool
```

Take an `id` from that list, then:

```bash
curl -s localhost:8000/calls/1 | python3 -m json.tool
```

```bash
curl -s -o /dev/null -w "%{http_code}\n" localhost:8000/calls/999999
```

The second command prints `404`.

## 3. Check the catalogue

Open `http://localhost:8000/docs`: `GET /calls/{id}` is listed with the
`CallDetail` response schema.

## 4. Mock values

The full mock values need demo call `HVB-DEMO-06` in the database, which
depends on #33's seed being loaded into the #29 tables (research R1). Until
then the unit test fixture is the check for those values.
