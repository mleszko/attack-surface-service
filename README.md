# Cloud Attack Surface Analyzer

FastAPI service for computing **potential lateral movement paths** between virtual machines based on VM tags and firewall rules.

The project focuses on practical backend engineering concerns: deterministic behavior, startup validation, backpressure under load, and CI quality gates.

## Features

- Computes attacker VM IDs for a target VM (`/api/v1/attack`)
- Exposes runtime request metrics (`/api/v1/stats`)
- Validates and indexes environment data at startup for fast lookups
- Uses bounded async queue + worker pool for backpressure handling
- Includes unit, integration, and startup-failure test coverage
- Enforces quality with CI (`ruff`, `mypy`, `pytest`, coverage threshold)

## Quickstart (local)

Prerequisites:
- Python 3.11+

From repository root:

```bash
pip install -r requirements-dev.txt
cd app
export ENV_PATH=tests/cloud.json
uvicorn attack_surface:app --host 0.0.0.0 --port 8000
```

Try it:

```bash
curl "http://localhost:8000/api/v1/attack?vm_id=vm-a"
curl "http://localhost:8000/api/v1/stats"
```

Interactive API docs:
- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

## Run with Docker

```bash
docker build -t attack-surface-service .
docker run --rm -p 8000:80 -e ENV_PATH=tests/cloud.json attack-surface-service
```

## API

### `GET /api/v1/attack?vm_id=<vm-id>`
Returns unique VM IDs that can attack the target VM.

Response example:
```json
["vm-c"]
```

### `GET /api/v1/stats`
Returns:
- `vm_count`
- `request_count`
- `average_request_time`

Response example:
```json
{
  "vm_count": 3,
  "request_count": 102,
  "average_request_time": 0.002
}
```

## Engineering notes

- Environment is loaded once during lifespan startup.
- Firewall relations are non-transitive.
- Self-attack is removed from response unless explicitly implied and distinct.
- Invalid startup input fails fast with clear runtime errors.

Detailed docs:
- [Architecture](docs/architecture.md)
- [Design decisions](docs/decisions.md)
- [Roadmap](docs/roadmap.md)
- [Changelog](CHANGELOG.md)

## Quality and testing

From `app/`:

```bash
ruff check .
mypy .
pytest --cov=. --cov-report=term-missing
```

Current pipeline includes:
- lint + typecheck job
- Python matrix tests (3.11, 3.12) with coverage gate
- Docker build validation

## CI/CD

- CI workflow: `.github/workflows/ci.yml`
- Release workflow (tag-triggered image artifact build): `.github/workflows/release.yml`

## License

[MIT](LICENSE)
