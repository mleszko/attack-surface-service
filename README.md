# Attack Surface Service

🔗 **Repository:** [github.com/mleszko/attack-surface-service](https://github.com/mleszko/attack-surface-service)

## 📌 Description
This is a Python-based REST API service built for the hiring exercise. It identifies the potential attack surface of a virtual machine (VM) in a cloud environment described by firewall rules and VM tags.

## 🚀 How to Run (Linux)

### 1. Requirements
- Python 3.9+
- Linux system

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set environment variable and start the service
```bash
export ENV_PATH=cloud.json
uvicorn main:app --host 0.0.0.0 --port 80
```

Make sure `cloud.json` is in the same directory.

## 📂 Project Structure
```
.
├─── app 
    ├──main.py              # FastAPI entry point
    ├── models.py            # Data models (VM, FirewallRule)
    ├── services.py          # Core logic and statistics
    ├── test_attack_surface.py  # Unit tests using pytest
    ├── cloud.json           # Example environment file
├── requirements.txt     # Dependencies
└── README.md            # Documentation
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
pytest test_attack_surface.py
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

## ✅ Notes
- All VMs and firewall rules are loaded once at startup.
- Firewall rules are **not transitive**.
- VM cannot attack itself unless explicitly allowed by a rule.
- The response list contains **unique VM IDs** only.
- The environment JSON file must be provided via the `ENV_PATH` environment variable.
- Service tracks request counts and average processing time for all endpoints.
- Application is structured in modular components with unit test coverage.

---
Hiring Exercise
