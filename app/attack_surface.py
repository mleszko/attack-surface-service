import json
import time
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from typing import List
import uvicorn
import sys
import os
from threading import Lock

app = FastAPI()

# Global data storage and state container
class AppState:
    def __init__(self):
        self.data = {}
        self.vm_id_to_tags = {}
        self.tag_to_vm_ids = {}
        self.dest_tag_to_source_tags = {}
        self.vm_count = 0
        self.request_count = 0
        self.cumulative_request_time = 0.0
        self.request_lock = Lock()

state = AppState()

def load_environment(file_path):
    with open(file_path, 'r') as f:
        state.data = json.load(f)

    state.vm_id_to_tags = {}
    state.tag_to_vm_ids = {}
    state.dest_tag_to_source_tags = {}

    for vm in state.data.get("vms", []):
        vm_id = vm["vm_id"]
        tags = vm.get("tags", [])
        state.vm_id_to_tags[vm_id] = tags
        for tag in tags:
            state.tag_to_vm_ids.setdefault(tag, set()).add(vm_id)

    for rule in state.data.get("fw_rules", []):
        src = rule["source_tag"]
        dst = rule["dest_tag"]
        state.dest_tag_to_source_tags.setdefault(dst, set()).add(src)

    state.vm_count = len(state.data.get("vms", []))

@app.on_event("startup")
def startup_event():
    path = os.environ.get("ENV_PATH")
    if not path:
        print("Missing ENV_PATH environment variable", file=sys.stderr)
        sys.exit(1)
    load_environment(path)

@app.middleware("http")
async def track_request_time(request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start_time

    with state.request_lock:
        state.request_count += 1
        state.cumulative_request_time += duration

    return response

@app.get("/api/v1/attack")
def get_attack(vm_id: str = Query(...)):
    if vm_id not in state.vm_id_to_tags:
        raise HTTPException(status_code=404, detail="VM not found")

    attackable_by = set()
    target_tags = state.vm_id_to_tags[vm_id]

    for dest_tag in target_tags:
        source_tags = state.dest_tag_to_source_tags.get(dest_tag, set())
        for src_tag in source_tags:
            attackers = state.tag_to_vm_ids.get(src_tag, set())
            attackable_by.update(attackers)

    attackable_by.discard(vm_id)
    return JSONResponse(list(attackable_by))

@app.get("/api/v1/stats")
def get_stats():
    with state.request_lock:
        avg_time = state.cumulative_request_time / state.request_count if state.request_count else 0.0
        return {
            "vm_count": state.vm_count,
            "request_count": state.request_count,
            "average_request_time": round(avg_time, 9)
        }

# No need for __main__ block; run with: uvicorn main:app --host 0.0.0.0 --port 80
