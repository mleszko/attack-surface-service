# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by Keep a Changelog and follows semantic versioning intentions.

## [Unreleased]

### Added
- Modern FastAPI lifespan-based startup/shutdown lifecycle.
- Service state wiring through `app.state` for analyzer/stats/worker.
- Worker shutdown support and focused tests for queue/error behavior.
- Startup-failure tests covering missing ENV, missing file, and invalid payload.
- Coverage reporting and threshold enforcement in CI.
- Multi-job CI workflow with lint/type/test/docker stages.
- Release workflow triggered by version tags (`v*`).
- Portfolio-focused documentation:
  - Architecture notes
  - Design decisions
  - Roadmap
  - Environment example
  - License

### Changed
- Dependency split into runtime (`requirements.txt`) and development (`requirements-dev.txt`).
- Integration tests made path-robust and lifespan-aware.
- Docker run context aligned with current app module structure.
- Logging output now defaults to stdout for container/platform compatibility.

### Fixed
- Inconsistent environment fixture path for large integration test.
- CI working directory and install flow mismatches.
