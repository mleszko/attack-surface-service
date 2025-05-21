from typing import Set, Dict, Callable, Any, Union
from collections import defaultdict
from threading import Lock
from models import CloudEnvironment

class AttackSurfaceAnalyzer:
    """Analyzes the attack surface of a VM based on tags and firewall rules."""

    def __init__(self) -> None:
        self.vm_id_to_tags: Dict[str, Set[str]] = {}
        self.tag_to_vm_ids: Dict[str, Set[str]] = defaultdict(set)
        self.dest_tag_to_attacker_ids: Dict[str, Set[str]] = defaultdict(set)

    def load_environment(self, env: CloudEnvironment) -> None:
        """Load and preprocess VM and firewall rule relationships from environment."""
        self.vm_id_to_tags.clear()
        self.tag_to_vm_ids.clear()
        self.dest_tag_to_attacker_ids.clear()

        for vm in env.vms:
            self.vm_id_to_tags[vm.vm_id] = set(vm.tags)
            for tag in vm.tags:
                self.tag_to_vm_ids[tag].add(vm.vm_id)

        for rule in env.fw_rules:
            source_ids = self.tag_to_vm_ids.get(rule.source_tag, set())
            self.dest_tag_to_attacker_ids[rule.dest_tag].update(source_ids)

    def get_attackers(self, vm_id: str) -> Set[str]:
        """Return the set of VM IDs that can attack the given VM."""
        if vm_id not in self.vm_id_to_tags:
            raise ValueError("VM not found")

        target_tags = self.vm_id_to_tags[vm_id]
        attackers = set()

        for dest_tag in target_tags:
            attackers.update(self.dest_tag_to_attacker_ids.get(dest_tag, set()))

        attackers.discard(vm_id)
        return attackers

    def vm_count(self) -> int:
        """Return the total number of VMs loaded into the analyzer."""
        return len(self.vm_id_to_tags)

class StatsTracker:
    """Tracks API request statistics: count and average processing time."""

    def __init__(self) -> None:
        self.request_count: int = 0
        self.total_time: float = 0.0
        self.lock: Lock = Lock()

    def record_request(self, duration: float) -> None:
        """Record the duration of a handled HTTP request."""
        with self.lock:
            self.request_count += 1
            self.total_time += duration

    def get_stats(self, vm_count: int) -> Dict[str, Union[float, int]]:
        """Return statistics including VM count, request count, and average request time."""
        with self.lock:
            avg_time = self.total_time / self.request_count if self.request_count else 0.0
            return {
                "vm_count": vm_count,
                "request_count": self.request_count,
                "average_request_time": round(avg_time, 9)
            }
