# Orca Security - Attack Surface Service

## 📌 Description

This is a Python-based REST API service built for the hiring exercise. It identifies the potential attack surface of a virtual machine (VM) in a cloud environment described by firewall rules and VM tags.

## 🚀 How to Run

### 1. Requirements

* Python 3.9+

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the service

```bash
python attack_surface.py cloud.json
```

Make sure `cloud.json` is in the same directory.

## 📂 API Endpoints

### GET `/api/v1/attack?vm_id=<vm-id>`

Returns a list of VM IDs that can potentially attack the given VM.

**Example:**

```bash
curl 'http://localhost/api/v1/attack?vm_id=vm-a211de'
```

**Response:**

```json
["vm-c7bac01a07"]
```

### GET `/api/v1/stats`

Returns statistics since the service startup:

* `vm_count`: number of VMs
* `request_count`: total number of requests
* `average_request_time`: average processing time in seconds

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

## 📄 Files Included

* `main.py` — FastAPI application
* `cloud.json` — Sample cloud environment
* `requirements.txt` — Dependencies
* `README.md` — Documentation

## ✅ Notes

* All VMs and firewall rules are loaded once at startup.
* Firewall rules are **not transitive**.
* VM cannot attack itself unless explicitly allowed by a rule.
* The response list contains **unique VM IDs** only.

---

© Orca Security Hiring Exercise
