import asyncio
from typing import Any

import pytest
from fastapi import HTTPException

from async_worker import AttackWorker


class FakeAnalyzer:
    def __init__(self, mode: str = "ok") -> None:
        self.mode = mode

    async def get_attackers(self, vm_id: str) -> set[str]:
        if self.mode == "http_exception":
            raise HTTPException(status_code=404, detail="VM not found")
        if self.mode == "value_error":
            raise ValueError("bad vm")
        if self.mode == "unexpected":
            raise RuntimeError("boom")
        return {f"attacker-for-{vm_id}"}


@pytest.mark.asyncio
async def test_worker_processes_successful_request() -> None:
    analyzer = FakeAnalyzer()
    worker = AttackWorker(analyzer, num_workers=1)
    await worker.start()

    captured: dict[str, Any] = {}

    async def responder(payload: Any, status: int) -> None:
        captured["payload"] = payload
        captured["status"] = status

    try:
        await worker.submit("vm-a", responder)
        await asyncio.wait_for(worker.queue.join(), timeout=1.0)
    finally:
        await worker.stop()

    assert captured["status"] == 200
    assert captured["payload"] == ["attacker-for-vm-a"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("mode", "expected_status", "expected_code"),
    [
        ("http_exception", 404, "vm_not_found"),
        ("value_error", 404, "invalid_vm"),
        ("unexpected", 500, "internal_error"),
    ],
)
async def test_worker_maps_failures_to_status_codes(
    mode: str, expected_status: int, expected_code: str
) -> None:
    analyzer = FakeAnalyzer(mode=mode)
    worker = AttackWorker(analyzer, num_workers=1)
    await worker.start()

    captured: dict[str, Any] = {}

    async def responder(payload: Any, status: int) -> None:
        captured["payload"] = payload
        captured["status"] = status

    try:
        await worker.submit("vm-x", responder)
        await asyncio.wait_for(worker.queue.join(), timeout=1.0)
    finally:
        await worker.stop()

    assert captured["status"] == expected_status
    assert captured["payload"]["code"] == expected_code
    assert "message" in captured["payload"]


@pytest.mark.asyncio
async def test_worker_returns_429_when_queue_is_full() -> None:
    analyzer = FakeAnalyzer()
    worker = AttackWorker(analyzer, max_queue_size=1, num_workers=0)

    # Fill the queue and do not start workers to simulate sustained pressure.
    await worker.queue.put({"vm_id": "vm-a", "responder": lambda *_: None})

    captured: dict[str, Any] = {}

    async def responder(payload: Any, status: int) -> None:
        captured["payload"] = payload
        captured["status"] = status

    await worker.submit("vm-b", responder, timeout=0.01)

    assert captured["status"] == 429
    assert captured["payload"]["code"] == "too_busy"
    assert captured["payload"]["message"] == "Server too busy. Try again later."
