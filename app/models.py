from typing import List, Dict
from dataclasses import dataclass

class ValidationError(Exception):
    pass

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
        if "vms" not in data or "fw_rules" not in data:
            raise ValidationError("Missing 'vms' or 'fw_rules' in environment data")

        vms = []
        seen_vm_ids = set()
        for vm in data["vms"]:
            if "vm_id" not in vm or "name" not in vm or "tags" not in vm:
                raise ValidationError(f"VM missing required fields: {vm}")
            if vm["vm_id"] in seen_vm_ids:
                raise ValidationError(f"Duplicate VM ID found: {vm['vm_id']}")
            seen_vm_ids.add(vm["vm_id"])
            vms.append(VirtualMachine(**vm))

        fw_rules = []
        seen_fw_ids = set()
        for fw in data["fw_rules"]:
            if "fw_id" not in fw or "source_tag" not in fw or "dest_tag" not in fw:
                raise ValidationError(f"Firewall rule missing required fields: {fw}")
            if fw["fw_id"] in seen_fw_ids:
                raise ValidationError(f"Duplicate firewall rule ID found: {fw['fw_id']}")
            seen_fw_ids.add(fw["fw_id"])
            fw_rules.append(FirewallRule(**fw))

        return CloudEnvironment(vms=vms, fw_rules=fw_rules)
