# Roadmap

This roadmap is focused on practical security engineering use cases.

## v0.2.x

- [x] Add `/healthz` and `/readyz` endpoints for easier orchestration checks.
- [x] Add structured JSON logging mode (toggle by environment variable).
- [x] Standardize error payloads with request IDs.
- [x] Add OpenAPI response examples for common errors.

## v0.3.x

- Add environment upload endpoint for ad hoc analysis (`POST /api/v1/environment`).
- Add optional persistence adapter (SQLite first, then pluggable backends).
- Introduce baseline query rate metrics for dashboards.

## v0.4.x

- Add policy mode: fail CI when risky reachability patterns are detected.
- Add a CLI wrapper for local/offline audits.
- [x] Provide Kubernetes deployment manifests.
- [ ] Add sample Helm chart values.
