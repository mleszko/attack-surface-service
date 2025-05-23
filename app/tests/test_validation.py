import pytest
from models import CloudEnvironment, ValidationError


def test_missing_vms_key():
    with pytest.raises(ValidationError, match="Missing 'vms' or 'fw_rules'"):
        CloudEnvironment.from_dict({"fw_rules": []})


def test_missing_fw_rules_key():
    with pytest.raises(ValidationError, match="Missing 'vms' or 'fw_rules'"):
        CloudEnvironment.from_dict({"vms": []})


def test_vm_missing_fields():
    bad_data = {
        "vms": [{"vm_id": "vm-1", "tags": ["web"]}],  # missing "name"
        "fw_rules": []
    }
    with pytest.raises(ValidationError, match="VM missing required fields"):
        CloudEnvironment.from_dict(bad_data)


def test_fw_rule_missing_fields():
    bad_data = {
        "vms": [{"vm_id": "vm-1", "name": "test", "tags": ["web"]}],
        "fw_rules": [{"fw_id": "fw-1", "source_tag": "web"}]  # missing "dest_tag"
    }
    with pytest.raises(ValidationError, match="Firewall rule missing required fields"):
        CloudEnvironment.from_dict(bad_data)


def test_duplicate_vm_ids():
    bad_data = {
        "vms": [
            {"vm_id": "vm-1", "name": "one", "tags": ["a"]},
            {"vm_id": "vm-1", "name": "duplicate", "tags": ["b"]}
        ],
        "fw_rules": []
    }
    with pytest.raises(ValidationError, match="Duplicate VM ID found"):
        CloudEnvironment.from_dict(bad_data)


def test_duplicate_fw_ids():
    bad_data = {
        "vms": [{"vm_id": "vm-1", "name": "one", "tags": ["a"]}],
        "fw_rules": [
            {"fw_id": "fw-1", "source_tag": "a", "dest_tag": "b"},
            {"fw_id": "fw-1", "source_tag": "x", "dest_tag": "y"}
        ]
    }
    with pytest.raises(ValidationError, match="Duplicate firewall rule ID found"):
        CloudEnvironment.from_dict(bad_data)
