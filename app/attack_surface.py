import json
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Callable

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from models import CloudEnvironment, ValidationError
from services import AttackSurfaceAnalyzer, StatsTracker
from async_worker import AttackWorker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load environment state and start worker lifecycle."""
    analyzer = AttackSurfaceAnalyzer()
    stats = StatsTracker()
    worker = AttackWorker(analyzer)

    path = os.environ.get("ENV_PATH")
    if not path:
        logging.error("Missing ENV_PATH environment variable")
        raise RuntimeError("Missing ENV_PATH environment variable")

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        env = CloudEnvironment.from_dict(data)
        analyzer.load_environment(env)
        await worker.start()
        app.state.analyzer = analyzer
        app.state.stats = stats
        app.state.worker = worker
        logging.info(f"Loaded environment from {path} with {len(env.vms)} VMs and {len(env.fw_rules)} rules")
    except FileNotFoundError:
        logging.exception(f"File not found: {path}")
        raise RuntimeError(f"File not found: {path}")
    except ValidationError as e:
        logging.error(f"Invalid environment configuration: {e}")
        raise RuntimeError(f"Invalid environment configuration: {e}")
    except Exception:
        logging.exception("Unexpected error during startup")
        raise
    try:
        yield
    finally:
        await worker.stop()


app = FastAPI(lifespan=lifespan)

@app.middleware("http")
async def track_request_time(request: Request, call_next: Callable) -> JSONResponse:
    """Middleware to measure and log the duration of each HTTP request."""
    start_time = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start_time
    stats = request.app.state.stats
    stats.record_request(duration)
    logging.info(f"{request.method} {request.url.path} completed in {duration:.4f} sec")
    return response

@app.get("/api/v1/attack")
async def get_attack(request: Request, vm_id: str = Query(..., min_length=1, max_length=64)) -> JSONResponse:
    """Queue the attack surface request to be processed asynchronously."""
    result: dict[str, Any] = {}
    worker = request.app.state.worker

    async def capture_result(payload: dict[str, Any], status: int = 200) -> None:
        nonlocal result
        result = payload
        if status != 200:
            raise HTTPException(status_code=status, detail=payload.get("error") or payload)

    await worker.submit(vm_id, capture_result)
    return JSONResponse(result)

@app.get("/api/v1/stats")
def get_stats(request: Request) -> dict[str, Any]:
    """Return statistics about the number of VMs, total requests, and average request time."""
    stats = request.app.state.stats
    analyzer = request.app.state.analyzer
    result = stats.get_stats(analyzer.vm_count())
    logging.info("Stats endpoint called")
    return result
