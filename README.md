# Attack Surface Service

🔗 **Repository:** [github.com/mleszko/attack-surface-service](https://github.com/mleszko/attack-surface-service)

## 📌 Description
This is a Python-based REST API service built for the hiring exercise. It identifies the potential attack surface of a virtual machine (VM) in a cloud environment described by firewall rules and VM tags.

## 🤖 Collaboration & Development Note

This project was implemented using a mix of senior-level software engineering experience and AI-assisted support (ChatGPT), with an emphasis on:

- Clean, modular architecture
- Test-driven design
- Type and lint-safe code (CI with `pytest`, `mypy`, `ruff`)
- Defensive programming and input validation
- Developer experience (documentation, logging, usability)

AI support was used to boost productivity and clarity — not to replace design ownership or code quality thinking.

## 🚀 How to Run (Linux)

### 1. Requirements
- Python 3.9+
- Linux system

### 2. Install dependencies
```bash
pip install -r requirements-dev.txt
```

### 3. Set environment variable and start the service
```bash
cd app
export ENV_PATH=tests/cloud.json
uvicorn attack_surface:app --host 0.0.0.0 --port 80
```

Make sure `cloud.json` is in the `app/tests` directory.

## 📂 Project Structure
```
.
📁 attack-surface-service/
├── app/
|   ├── tests/
│   │   │   ├── cloud.json                 # Example environment file
│   │   │   ├── test_attack_surface.py     # Unit tests (sync)
│   │   │   ├── test_attack_surface_async.py  # Unit tests (async)
│   │   │   └── test_integration_load.py   # Load test for 1000 requests    
│   ├── attack_surface.py          # FastAPI entry point
│   ├── models.py                  # Data models (VM, FirewallRule)
│   ├── services.py                # Core logic and statistics
│   ├── async_worker.py            # Async queue and parallel processing
│   └── __init__.py
├── Dockerfile
├── requirements.txt               # Runtime dependencies
├── requirements-dev.txt           # Dev tools: pytest, ruff, mypy
├── README.md                      # Documentation
├── Makefile                       # Developer shortcuts (run, test, lint)
└── .github/
    └── workflows/
        └── ci.yml                 # GitHub Actions for CI

```

## 📂 API Endpoints

### GET `/api/v1/attack?vm_id=<vm-id>`
Returns a list of VM IDs that can potentially attack the given VM.

**Example:**
```bash
curl 'http://localhost/api/v1/attack?vm_id=vm-a'
```

**Response:**
```json
["vm-c"]
```

### GET `/api/v1/stats`
Returns statistics since the service startup:
- `vm_count`: number of VMs
- `request_count`: total number of requests
- `average_request_time`: average processing time in seconds

**Example:**
```bash
curl 'http://localhost/api/v1/stats'
```

**Response:**
```json
{
  "vm_count": 3,
  "request_count": 102,
  "average_request_time": 0.002351123
}
```

## 🧪 Testing
Run unit tests using `pytest`:
```bash
cd app
pytest
```

Run basic functional tests using `curl`:
```bash
curl 'http://localhost/api/v1/attack?vm_id=vm-a'     # Check attackers
curl 'http://localhost/api/v1/stats'                 # Check stats
```

You can also test edge cases:
```bash
curl 'http://localhost/api/v1/attack?vm_id=notfound' # Expect 404
```

## 🌀 Request Queueing & Backpressure

To ensure the service remains responsive under high load, the `/api/v1/attack` endpoint uses an internal `asyncio.Queue` managed by a background worker.

- Each incoming request is placed in a bounded queue (default `maxsize=100`)
- A background task (`AttackWorker`) handles requests asynchronously, one at a time
- If the queue is full or a timeout occurs, the client receives a `429 Too Many Requests` response
- This mechanism provides backpressure control and protects the event loop from overload

This approach demonstrates real-world concurrency handling, resource management, and performance-awareness — without changing the public API interface.

## ✅ Notes
- All VMs and firewall rules are loaded once at startup.
- Firewall rules are **not transitive**.
- VM cannot attack itself unless explicitly allowed by a rule.
- The response list contains **unique VM IDs** only.
- The environment JSON file must be provided via the `ENV_PATH` environment variable.
- Service tracks request counts and average processing time for all endpoints.
- Application is structured in modular components with unit test coverage.

## 🛠️ Future Ideas & Extensions
This service was designed to be lightweight yet extendable. Potential improvements and directions include:

- **MySQL integration:** Store environment and query logs for long-term analysis.
- **Azure deployment:** Create a `deploy/azure` branch with templates for Azure App Service or Azure Container Apps.
- **AI prediction:** Use attack request patterns to predict likely future attack targets using basic ML.
- **Linux-level visibility:** Add a companion script or systemd service to monitor system-level traffic or resource usage.
- **Docker & Kubernetes:** Add `Dockerfile` and optional `Helm` chart for containerized deployments.

These are not included to keep the core project focused and lightweight but reflect a broader mindset toward real-world scalability and creativity.

## ✅ Performance & Resilience Checklist

This project was designed with automated benchmarking and robustness tests in mind. Below are deliberate improvements and verifications made to optimize reliability and speed:

### 🔐 Input Validation
- [x] Reject duplicated `vm_id` entries
- [x] Skip firewall rules with empty `source_tag` or `dest_tag`
- [x] Sanitize `/attack?vm_id=` against empty, missing, or overly long values
- [x] Limit max length of VM `name` and `tag` fields (e.g., 64 chars)

### 🚦 Error Handling
- [x] Return `404` for non-existent VMs
- [x] Return `422` for malformed queries
- [x] Prevent internal stack traces from leaking to clients

### ⚡ Large Input Performance
- [x] Precompute `dest_vm_id -> attacker_vm_ids` index at load time
- [x] Use `frozenset` for VM tags to reduce memory
- [x] Use `defaultdict` and immutable structures for efficient access

### 🧪 Load & Edge Testing
- [x] Load test: 1000 concurrent attack requests
- [x] Load test: huge_env.json with thousands of VMs
- [ ] Load test: 10k sequential queries to simulate sustained pressure
- [ ] Test nonexistent VM query handling
- [ ] Test VM with no tags or unmatched tags

### 🐳 Container & CI/CD
- [x] Dockerfile + `.dockerignore`
- [x] GitHub Actions: `mypy`, `ruff`, `pytest`
- [ ] Add lightweight `/ping` healthcheck endpoint
- [ ] Document performance decisions and benchmarks in README

## ⏱️ Development Time & Effort

This solution was designed, built, optimized and documented over the course of approximately **10–12 hours**.

---
Hiring Exercise
