# Local Setup

## Infrastructure

```powershell
docker compose -f infrastructure/docker/docker-compose.yml up -d postgres redis neo4j
```

## Python setup

```powershell
.venv\Scripts\python.exe -m pip install -e .[dev]
```

## API

```powershell
.venv\Scripts\python.exe apps/backend/serve.py
```

## Worker

```powershell
.venv\Scripts\python.exe apps/backend/worker/serve.py
```

## Frontend

```powershell
cd apps/frontend
npm install
npm run dev
```

## Tests

```powershell
.venv\Scripts\python.exe -m pytest apps/backend/tests
```

## Supported Phase 2 starter formats

- `pdf`
- `docx`
- `xlsx`
