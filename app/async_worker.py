import asyncio
from asyncio import Task
from typing import Dict, Any, Callable, List, Union


class AttackWorker:
    """Asynchronous worker that handles incoming attack requests from a queue."""

    def __init__(self, analyzer: Any, max_queue_size: int = 100, num_workers: int = 4) -> None:
        self.queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=max_queue_size)
        self.analyzer = analyzer
        self.tasks: List[Task] = []
        self.num_workers = num_workers

    async def start(self) -> None:
        """Start multiple background tasks to process the attack queue in parallel."""
        self.tasks = [asyncio.create_task(self.run()) for _ in range(self.num_workers)]

    async def run(self) -> None:
        """Continuously process queued attack requests one by one."""
        while True:
            item = await self.queue.get()
            vm_id: str = item["vm_id"]
            responder: Callable[[Union[Dict[str, Any], List[str]], int], Any] = item["responder"]
            try:
                attackers = await self.analyzer.get_attackers(vm_id)
                await responder(list(attackers), 200)
            except ValueError as e:
                await responder({"error": str(e)}, 404)
            except Exception as e:
                await responder({"error": f"Unexpected: {e}"}, 500)
            finally:
                self.queue.task_done()

    async def submit(self, vm_id: str, responder: Callable[[Dict[str, Any], int], Any], timeout: float = 1.0) -> None:
        """Submit a new attack request to the queue, or reject if queue is full."""
        try:
            await asyncio.wait_for(self.queue.put({"vm_id": vm_id, "responder": responder}), timeout=timeout)
        except asyncio.TimeoutError:
            await responder({"error": "Server too busy. Try again later."}, 429)
