# Architecture

## Overview

Attack Surface Service computes which virtual machines can reach a given target VM based on:

- VM tags
- firewall source tag -> destination tag rules

The API is optimized for low-latency queries by building lookup indexes once at startup.

## Request flow

1. **Startup / lifespan**
   - Load JSON environment file from `ENV_PATH`
   - Validate input data
   - Build analyzer indexes
   - Start async worker pool

2. **`GET /api/v1/attack?vm_id=...`**
   - Attach/propagate `X-Request-ID`
   - Validate query via FastAPI
   - Enqueue request into bounded queue
   - Worker resolves attacker set
   - Return list of attacker VM IDs
   - If queue is saturated, return `429`

3. **`GET /api/v1/stats`**
   - Return request count and average latency

4. **`GET /healthz` and `GET /readyz`**
   - `healthz`: process liveness
   - `readyz`: analyzer/worker readiness and queue metadata

5. **Error handling**
   - Validation and HTTP errors are normalized into a shared contract
   - Every error payload includes `request_id` for traceability

## Core components

- `models.py`
  - Domain and payload validation structures.
- `services.py`
  - `AttackSurfaceAnalyzer`: precomputes reachability index.
  - `StatsTracker`: thread-safe request metrics.
- `async_worker.py`
  - Bounded queue + worker pool for backpressure handling.
- `attack_surface.py`
  - FastAPI transport layer, lifespan wiring, request middleware, and error handlers.

## Design decisions

- **Precompute indexes**
  - Trade startup work for fast runtime lookups.
- **Bounded queue**
  - Protects process under bursty traffic.
- **Lifespan-based wiring**
  - Modern FastAPI startup/shutdown lifecycle.
- **Small dependency footprint**
  - Keep runtime lean and easy to deploy.
- **Operational observability**
  - Request IDs + optional JSON logs for easier platform diagnostics.
