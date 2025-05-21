import json
import time
import os
import sys
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import JSONResponse
from threading import Lock
from typing import Set

from models import CloudEnvironment
from services import AttackSurfaceAnalyzer, StatsTracker

app = FastAPI()

# Global services
analyzer = AttackSurfaceAnalyzer()
stats = StatsTracker()

@app.on_event("startup")
def startup_event():
    path = os.environ.get("ENV_PATH")
    if not path:
        print("Missing ENV_PATH environment variable", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        data = json.load(f)
    env = CloudEnvironment.from_dict(data)
    analyzer.load_environment(env)

@app.middleware("http")
async def track_request_time(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start_time
    stats.record_request(duration)
    return response

@app.get("/api/v1/attack")
def get_attack(vm_id: str = Query(...)):
    try:
        result = analyzer.get_attackers(vm_id)
        return JSONResponse(list(result))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/v1/stats")
def get_stats():
    return stats.get_stats(analyzer.vm_count())
