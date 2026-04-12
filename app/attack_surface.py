import asyncio
import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Callable

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.responses import Response

from async_worker import AttackWorker
from models import CloudEnvironment, ValidationError
from services import AttackSurfaceAnalyzer, StatsTracker

logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[logging.StreamHandler()])
logger = logging.getLogger("attack_surface")


def _emit_log(level: int, message: str, **fields: Any) -> None:
    """Emit text or JSON logs depending on LOG_FORMAT."""
    if os.getenv("LOG_FORMAT", "text").lower() == "json":
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": logging.getLevelName(level),
            "message": message,
        }
        payload.update(fields)
        logger.log(level, json.dumps(payload, sort_keys=True))
        return

    context = " ".join(f"{key}={value}" for key, value in fields.items())
    logger.log(level, f"{message} | {context}" if context else message)


def _error_payload(
    request: Request,
    code: str,
    message: str,
    *,
    details: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "request_id": getattr(request.state, "request_id", "unknown"),
        }
    }
    if details:
        payload["error"]["details"] = details
    return payload


def _status_code_to_error_code(status_code: int) -> str:
    mapping = {
        400: "bad_request",
        404: "not_found",
        422: "invalid_request",
        429: "too_busy",
        500: "internal_error",
        503: "service_not_ready",
    }
    return mapping.get(status_code, "request_error")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load environment state and start worker lifecycle."""
    analyzer = AttackSurfaceAnalyzer()
    stats = StatsTracker()
    worker = AttackWorker(analyzer)

    path = os.environ.get("ENV_PATH")
    if not path:
        _emit_log(logging.ERROR, "Missing ENV_PATH environment variable")
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
        _emit_log(
            logging.INFO,
            "Environment loaded",
            path=path,
            vm_count=len(env.vms),
            fw_rule_count=len(env.fw_rules),
        )
    except FileNotFoundError:
        _emit_log(logging.ERROR, "Environment file not found", path=path)
        raise RuntimeError(f"File not found: {path}")
    except ValidationError as e:
        _emit_log(logging.ERROR, "Invalid environment configuration", error=str(e))
        raise RuntimeError(f"Invalid environment configuration: {e}")
    except Exception:
        logger.exception("Unexpected error during startup")
        raise

    try:
        yield
    finally:
        await worker.stop()


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def attach_request_context(request: Request, call_next: Callable[[Request], Any]) -> Response:
    """Attach request IDs and track per-request metrics."""
    request_id = request.headers.get("X-Request-ID", "").strip() or str(uuid.uuid4())
    request.state.request_id = request_id
    start_time = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start_time

    stats = getattr(request.app.state, "stats", None)
    if stats is not None:
        stats.record_request(duration)

    response.headers["X-Request-ID"] = request_id
    _emit_log(
        logging.INFO,
        "Request completed",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round(duration * 1000, 2),
    )
    return response


@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    """Normalize HTTP errors into a consistent payload."""
    status_code = exc.status_code
    code = _status_code_to_error_code(status_code)
    message = str(exc.detail) if exc.detail is not None else "Request failed"
    if isinstance(exc.detail, dict):
        code = str(exc.detail.get("code") or code)
        message = str(exc.detail.get("message") or exc.detail.get("error") or message)

    return JSONResponse(status_code=status_code, content=_error_payload(request, code, message))


@app.exception_handler(RequestValidationError)
async def handle_validation_exception(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return validation issues in the shared error format."""
    details = [dict(item) for item in exc.errors()]
    return JSONResponse(
        status_code=422,
        content=_error_payload(
            request,
            "invalid_request",
            "Request validation failed",
            details=details,
        ),
    )


@app.exception_handler(Exception)
async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
    """Protect clients from unstructured internal exceptions."""
    _emit_log(logging.ERROR, "Unhandled request exception", error=str(exc))
    return JSONResponse(
        status_code=500,
        content=_error_payload(request, "internal_error", "Internal server error"),
    )


@app.get("/api/v1/attack")
async def get_attack(request: Request, vm_id: str = Query(..., min_length=1, max_length=64)) -> JSONResponse:
    """Queue the attack surface request to be processed asynchronously."""
    result: Any = []
    status_code = 200
    completed = asyncio.Event()
    worker = request.app.state.worker

    async def capture_result(payload: Any, status: int = 200) -> None:
        nonlocal result, status_code
        result = payload
        status_code = status
        completed.set()

    await worker.submit(vm_id, capture_result)
    try:
        await asyncio.wait_for(completed.wait(), timeout=2.0)
    except asyncio.TimeoutError as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "processing_timeout", "message": "Timed out while processing request"},
        ) from exc
    if status_code != 200:
        raise HTTPException(status_code=status_code, detail=result)
    return JSONResponse(result)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Simple liveness endpoint."""
    return {"status": "ok"}


@app.get("/readyz")
def readyz(request: Request) -> dict[str, Any]:
    """Readiness endpoint checking that runtime dependencies are initialized."""
    analyzer = getattr(request.app.state, "analyzer", None)
    worker = getattr(request.app.state, "worker", None)
    if analyzer is None or worker is None or not worker.tasks:
        raise HTTPException(
            status_code=503,
            detail={"code": "service_not_ready", "message": "Service is not ready"},
        )

    return {
        "status": "ready",
        "vm_count": analyzer.vm_count(),
        "workers": len(worker.tasks),
        "queue_depth": worker.queue.qsize(),
    }


@app.get("/api/v1/stats")
def get_stats(request: Request) -> dict[str, Any]:
    """Return runtime statistics for requests and loaded VM count."""
    stats = request.app.state.stats
    analyzer = request.app.state.analyzer
    result = stats.get_stats(analyzer.vm_count())
    _emit_log(logging.INFO, "Stats endpoint called", request_id=getattr(request.state, "request_id", "unknown"))
    return result
