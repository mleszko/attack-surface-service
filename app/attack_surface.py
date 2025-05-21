import json
import time
import os
import sys
import logging
import asyncio
from typing import Any, Callable
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import JSONResponse

from models import CloudEnvironment, ValidationError
from services import AttackSurfaceAnalyzer, StatsTracker
from async_worker import AttackWorker

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
worker = AttackWorker(analyzer)

@app.on_event("startup")
async def startup_event() -> None:
    """Load the cloud environment JSON file and initialize services on startup."""
    path = os.environ.get("ENV_PATH")
    if not path:
        logging.error("Missing ENV_PATH environment variable")
        sys.exit(1)

    try:
        with open(path) as f:
            data = json.load(f)
        env = CloudEnvironment.from_dict(data)
        analyzer.load_environment(env)
        await worker.start()
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
async def track_request_time(request: Request, call_next: Callable) -> JSONResponse:
    """Middleware to measure and log the duration of each HTTP request."""
    start_time = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start_time
    stats.record_request(duration)
    logging.info(f"{request.method} {request.url.path} completed in {duration:.4f} sec")
    return response

@app.get("/api/v1/attack")
async def get_attack(vm_id: str = Query(...)) -> JSONResponse:
    """Queue the attack surface request to be processed asynchronously."""
    result: dict[str, Any] = {}

    async def capture_result(payload: dict[str, Any], status: int = 200) -> None:
        nonlocal result
        result = payload
        if status != 200:
            raise HTTPException(status_code=status, detail=payload.get("error") or payload)

    await worker.submit(vm_id, capture_result)
    return JSONResponse(result)

@app.get("/api/v1/stats")
def get_stats() -> dict[str, Any]:
    """Return statistics about the number of VMs, total requests, and average request time."""
    result = stats.get_stats(analyzer.vm_count())
    logging.info("Stats endpoint called")
    return result
