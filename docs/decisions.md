# Design Decisions

## 1) Precomputed reachability index

**Decision:** Build `dest_vm_id -> attacker_vm_ids` during environment load, not per request.

**Why:**
- Keeps query latency stable under repeated access.
- Makes `/api/v1/attack` mostly a dictionary lookup plus response serialization.

**Trade-off:**
- Slightly higher startup cost and memory usage.

## 2) Bounded queue with async workers

**Decision:** Route attack queries through an internal bounded `asyncio.Queue`.

**Why:**
- Provides explicit backpressure during bursts.
- Prevents unbounded memory growth from request spikes.

**Trade-off:**
- Some requests receive `429` under sustained pressure.

## 3) Lifespan-driven resource lifecycle

**Decision:** Use FastAPI lifespan context for startup/shutdown handling.

**Why:**
- Modern FastAPI pattern.
- Clear lifecycle for loading environment and starting/stopping workers.

**Trade-off:**
- Slightly more setup code than global singleton initialization.

## 4) Runtime and dev dependency separation

**Decision:** Keep runtime dependencies in `requirements.txt` and all quality/test tooling in `requirements-dev.txt`.

**Why:**
- Smaller production footprint.
- Easier CI reproducibility.

**Trade-off:**
- Developers should use the dev requirements file for local work.

## 5) Explicit OpenAPI response examples

**Decision:** Add examples for success and common failure responses directly in route metadata.

**Why:**
- Improves consumer onboarding and integration speed.
- Keeps the runtime error contract and docs synchronized.

**Trade-off:**
- Requires maintaining examples when response shapes evolve.

## 6) Deployment manifests in-repo

**Decision:** Include baseline Docker Compose and Kubernetes manifests in source control.

**Why:**
- Makes local and cluster startup repeatable.
- Demonstrates operational readiness in a portfolio context.

**Trade-off:**
- Manifests remain intentionally minimal and may need environment-specific tuning.

## 5) Request ID propagation + unified error contract

**Decision:** Attach an `X-Request-ID` to each response and include `request_id` in all error payloads.

**Why:**
- Makes troubleshooting easier across API gateway, logs, and client reports.
- Keeps error handling consistent for frontend and integration consumers.

**Trade-off:**
- Slightly larger error payloads.

## 6) Log format toggle (`LOG_FORMAT`)

**Decision:** Support both text logs and JSON logs through an environment variable.

**Why:**
- Text output is friendly for local development.
- JSON output is easier to parse in centralized logging systems.

**Trade-off:**
- Logging path includes lightweight formatting logic.
