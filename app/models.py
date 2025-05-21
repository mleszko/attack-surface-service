from typing import List, Dict
from dataclasses import dataclass

@dataclass
class VirtualMachine:
    vm_id: str
    name: str
    tags: List[str]

@dataclass
class FirewallRule:
    fw_id: str
    source_tag: str
    dest_tag: str

@dataclass
class CloudEnvironment:
    vms: List[VirtualMachine]
    fw_rules: List[FirewallRule]

    @staticmethod
    def from_dict(data: Dict) -> 'CloudEnvironment':
        vms = [VirtualMachine(**vm) for vm in data.get("vms", [])]
        fw_rules = [FirewallRule(**fw) for fw in data.get("fw_rules", [])]
        return CloudEnvironment(vms=vms, fw_rules=fw_rules)
