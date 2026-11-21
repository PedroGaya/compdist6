# Streaming API Benchmark

CRUD API for a streaming service (Users, Playlists, Songs) in **Python** and
**Bun** over **REST, SOAP, GraphQL and gRPC** (8 services), load-tested with Locust.
Storage: a single shared **SQLite** file.

## Structure

```
streaming-api/
├── data/                  # streaming.db (generated, gitignored)
├── db/
│   ├── schema.sql         # shared schema
│   └── init.py            # create + seed the database
├── docs/contract.md       # operations, payloads, error semantics
├── proto/streaming.proto  # gRPC contract (shared)
├── schemas/
│   ├── streaming.wsdl     # SOAP contract (shared)
│   └── schema.graphql     # GraphQL contract (shared)
├── python/                # uv project
│   ├── common/db.py
│   └── rest/ soap/ graphql/ grpc/
├── bun/                   # bun project
│   ├── common/db.ts
│   └── rest/ soap/ graphql/ grpc/
└── loadtest/
    ├── common.py
    ├── locustfile_{rest,soap,graphql,grpc}.py
    └── results/
```

## Ports

| Protocol | Python | Bun  |
| -------- | ------ | ---- |
| REST     | 8001   | 8011 |
| SOAP     | 8002   | 8012 |
| GraphQL  | 8003   | 8013 |
| gRPC     | 8004   | 8014 |

## Setup

```powershell
cd python; uv sync; cd ..
cd bun; bun install; cd ..
uv run --project python python db/init.py
```

## Run (example)

```powershell
cd python; uv run uvicorn rest.main:app --port 8001
cd bun; bun run rest/index.ts

uv run --project python locust -f loadtest/locustfile_rest.py `
  --host http://localhost:8001 --headless -u 100 -r 10 -t 60s `
  --csv loadtest/results/py_rest
```

## Fairness rules

- Reset the DB with `db/init.py` before every test run.
- One service under test at a time.
- Every service implements `docs/contract.md` exactly.
