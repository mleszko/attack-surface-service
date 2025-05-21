import asyncio
from typing import Dict, Callable, Any

class AttackWorker:
    """Asynchronous worker that handles incoming attack requests from a queue."""

    def __init__(self, analyzer, max_queue_size: int = 100):
        self.queue = asyncio.Queue(maxsize=max_queue_size)
        self.analyzer = analyzer
        self.task = None

    async def start(self):
        """Start the background task that processes the attack queue."""
        self.task = asyncio.create_task(self.run())

    async def run(self):
        """Continuously process queued attack requests one by one."""
        while True:
            item = await self.queue.get()
            vm_id, responder = item["vm_id"], item["responder"]
            try:
                attackers = self.analyzer.get_attackers(vm_id)
                await responder({"attackers": list(attackers)})
            except ValueError as e:
                await responder({"error": str(e)}, status=404)
            except Exception as e:
                await responder({"error": f"Unexpected: {e}"}, status=500)
            finally:
                self.queue.task_done()

    async def submit(self, vm_id: str, responder: Callable[[Any], Any], timeout: float = 1.0):
        """Submit a new attack request to the queue, or reject if queue is full."""
        try:
            await asyncio.wait_for(self.queue.put({"vm_id": vm_id, "responder": responder}), timeout=timeout)
        except asyncio.TimeoutError:
            await responder({"error": "Server too busy. Try again later."}, status=429)
