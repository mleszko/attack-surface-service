# Cloud Attack Surface Analyzer

FastAPI service for computing **potential lateral movement paths** between virtual machines based on VM tags and firewall rules.

The project focuses on practical backend engineering concerns: deterministic behavior, startup validation, backpressure under load, and CI quality gates.

## Features

- Computes attacker VM IDs for a target VM (`/api/v1/attack`)
- Exposes runtime request metrics (`/api/v1/stats`)
- Provides probe endpoints for orchestration (`/healthz`, `/readyz`)
- Propagates `X-Request-ID` for tracing and debugging
- Standardizes error responses with `{error: {code, message, request_id}}`
- Supports structured logging with `LOG_FORMAT=json`
- Documents OpenAPI response examples for success and error paths
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

## Run with Docker Compose

```bash
docker compose up --build
```

The compose setup exposes the API on `http://localhost:8000`, enables JSON logs,
and uses `/healthz` for container health checks.

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

### `GET /healthz`
Liveness endpoint for platform health checks.

### `GET /readyz`
Readiness endpoint that verifies analyzer/worker startup state.

Response example:
```json
{
  "vm_count": 3,
  "request_count": 102,
  "average_request_time": 0.002
}
```

### Error contract
Error responses follow a single schema:

```json
{
  "error": {
    "code": "vm_not_found",
    "message": "VM not found",
    "request_id": "9cbc6eb4-069a-4f99-8a95-8e1bd3a5f767"
  }
}
```

### OpenAPI examples

The API docs include explicit examples for:

- success responses (`/api/v1/attack`, `/api/v1/stats`, `/healthz`, `/readyz`)
- common error responses (`404`, `422`, `429`, `503`)

See:
- `http://localhost:8000/docs`
- `http://localhost:8000/openapi.json`

## Runtime configuration

Environment variables:

- `ENV_PATH` (required): path to cloud environment JSON
- `LOG_FORMAT` (optional): `text` (default) or `json`

## Engineering notes

- Environment is loaded once during lifespan startup.
- Firewall relations are non-transitive.
- Self-attack is removed from response unless explicitly implied and distinct.
- Invalid startup input fails fast with clear runtime errors.

Detailed docs:
- [Architecture](docs/architecture.md)
- [Design decisions](docs/decisions.md)
- [Deployment](docs/deployment.md)
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

## Kubernetes

Baseline manifests are provided in `deploy/k8s`:

```bash
kubectl apply -k deploy/k8s
```

They include:
- deployment with `/healthz` and `/readyz` probes
- ClusterIP service
- kustomization entrypoint

## License

[MIT](LICENSE)
