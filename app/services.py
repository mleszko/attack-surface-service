from typing import Set, Dict, Union
from collections import defaultdict
from threading import Lock
from models import CloudEnvironment, ValidationError
from fastapi import HTTPException  # added to catch and raise HTTP 404

class AttackSurfaceAnalyzer:
    """Analyzes the attack surface of a VM based on tags and firewall rules."""

    def __init__(self) -> None:
        self.vm_id_to_tags: Dict[str, frozenset[str]] = {}
        self.tag_to_vm_ids: Dict[str, Set[str]] = defaultdict(set)
        self.dest_tag_to_attacker_ids: Dict[str, Set[str]] = defaultdict(set)
        self.dest_vm_id_to_attacker_ids: Dict[str, Set[str]] = defaultdict(set)

    def load_environment(self, env: CloudEnvironment) -> None:
        """Load and preprocess VM and firewall rule relationships from environment."""
        self.vm_id_to_tags.clear()
        self.tag_to_vm_ids.clear()
        self.dest_tag_to_attacker_ids.clear()
        self.dest_vm_id_to_attacker_ids.clear()

        seen_vm_ids: Set[str] = set()

        for vm in env.vms:
            if not vm.vm_id or vm.vm_id in seen_vm_ids:
                raise ValidationError(f"Duplicate or missing vm_id: {vm.vm_id}")
            seen_vm_ids.add(vm.vm_id)

            if len(vm.name) > 64:
                raise ValidationError(f"VM name too long: {vm.name}")
            if any(len(tag) > 64 for tag in vm.tags):
                raise ValidationError(f"Tag too long in VM {vm.vm_id}")

            tags = frozenset(vm.tags)
            self.vm_id_to_tags[vm.vm_id] = tags
            for tag in tags:
                self.tag_to_vm_ids[tag].add(vm.vm_id)

        for rule in env.fw_rules:
            if not rule.source_tag or not rule.dest_tag:
                continue  # skip invalid rule
            source_ids = self.tag_to_vm_ids.get(rule.source_tag, set())
            self.dest_tag_to_attacker_ids[rule.dest_tag].update(source_ids)

        # Build dest_vm_id -> attacker_vm_ids index
        for vm_id, tags in self.vm_id_to_tags.items():
            attackers = set()
            for tag in tags:
                attackers.update(self.dest_tag_to_attacker_ids.get(tag, set()))
            self.dest_vm_id_to_attacker_ids[vm_id] = attackers

    async def get_attackers(self, vm_id: str) -> Set[str]:
        """Return the set of VM IDs that can attack the given VM."""
        if vm_id not in self.vm_id_to_tags:
            raise HTTPException(status_code=404, detail="VM not found")

        attackers = self.dest_vm_id_to_attacker_ids.get(vm_id, set()).copy()
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
