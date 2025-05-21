from typing import Set, Dict
from collections import defaultdict
from threading import Lock
from models import CloudEnvironment

class AttackSurfaceAnalyzer:
    def __init__(self):
        self.vm_id_to_tags: Dict[str, Set[str]] = {}
        self.tag_to_vm_ids: Dict[str, Set[str]] = defaultdict(set)
        self.dest_tag_to_source_tags: Dict[str, Set[str]] = defaultdict(set)

    def load_environment(self, env: CloudEnvironment):
        self.vm_id_to_tags.clear()
        self.tag_to_vm_ids.clear()
        self.dest_tag_to_source_tags.clear()

        for vm in env.vms:
            self.vm_id_to_tags[vm.vm_id] = set(vm.tags)
            for tag in vm.tags:
                self.tag_to_vm_ids[tag].add(vm.vm_id)

        for rule in env.fw_rules:
            self.dest_tag_to_source_tags[rule.dest_tag].add(rule.source_tag)

    def get_attackers(self, vm_id: str) -> Set[str]:
        if vm_id not in self.vm_id_to_tags:
            raise ValueError("VM not found")

        target_tags = self.vm_id_to_tags[vm_id]
        attackers = set()

        for dest_tag in target_tags:
            source_tags = self.dest_tag_to_source_tags.get(dest_tag, set())
            for src_tag in source_tags:
                attackers.update(self.tag_to_vm_ids.get(src_tag, set()))

        attackers.discard(vm_id)
        return attackers

    def vm_count(self) -> int:
        return len(self.vm_id_to_tags)

class StatsTracker:
    def __init__(self):
        self.request_count = 0
        self.total_time = 0.0
        self.lock = Lock()

    def record_request(self, duration: float):
        with self.lock:
            self.request_count += 1
            self.total_time += duration

    def get_stats(self, vm_count: int):
        with self.lock:
            avg_time = self.total_time / self.request_count if self.request_count else 0.0
            return {
                "vm_count": vm_count,
                "request_count": self.request_count,
                "average_request_time": round(avg_time, 9)
            }
