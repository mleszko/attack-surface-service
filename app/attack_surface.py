import json
import time
import os
import sys
import logging
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import JSONResponse
from threading import Lock
from typing import Set

from models import CloudEnvironment, ValidationError
from services import AttackSurfaceAnalyzer, StatsTracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("service.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

app = FastAPI()

# Global services
analyzer = AttackSurfaceAnalyzer()
stats = StatsTracker()

@app.on_event("startup")
def startup_event():
    path = os.environ.get("ENV_PATH")
    if not path:
        logging.error("Missing ENV_PATH environment variable")
        sys.exit(1)

    try:
        with open(path) as f:
            data = json.load(f)
        env = CloudEnvironment.from_dict(data)
        analyzer.load_environment(env)
        logging.info(f"Loaded environment from {path} with {len(env.vms)} VMs and {len(env.fw_rules)} rules")
    except FileNotFoundError:
        logging.exception(f"File not found: {path}")
        sys.exit(1)
    except ValidationError as e:
        logging.error(f"Invalid environment configuration: {e}")
        sys.exit(1)
    except Exception:
        logging.exception("Unexpected error during startup")
        sys.exit(1)

@app.middleware("http")
async def track_request_time(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start_time
    stats.record_request(duration)
    logging.info(f"{request.method} {request.url.path} completed in {duration:.4f} sec")
    return response

@app.get("/api/v1/attack")
def get_attack(vm_id: str = Query(...)):
    try:
        result = analyzer.get_attackers(vm_id)
        logging.info(f"Attack surface requested for {vm_id}: {result}")
        return JSONResponse(list(result))
    except ValueError as e:
        logging.warning(f"Attack query failed for {vm_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/v1/stats")
def get_stats():
    result = stats.get_stats(analyzer.vm_count())
    logging.info("Stats endpoint called")
    return result
