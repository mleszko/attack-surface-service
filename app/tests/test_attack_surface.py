import pytest
from fastapi import HTTPException
from models import VirtualMachine, FirewallRule, CloudEnvironment
from services import AttackSurfaceAnalyzer

@pytest.fixture
def sample_env():
    vms = [
        VirtualMachine(vm_id="vm-a", name="web", tags=["web"]),
        VirtualMachine(vm_id="vm-b", name="db", tags=["db"]),
        VirtualMachine(vm_id="vm-c", name="admin", tags=["admin"])
    ]
    rules = [
        FirewallRule(fw_id="fw-1", source_tag="web", dest_tag="db"),
        FirewallRule(fw_id="fw-2", source_tag="admin", dest_tag="web")
    ]
    return CloudEnvironment(vms=vms, fw_rules=rules)

@pytest.mark.asyncio
async def test_attackers_for_vm_b(sample_env):
    analyzer = AttackSurfaceAnalyzer()
    analyzer.load_environment(sample_env)
    result = await analyzer.get_attackers("vm-b")
    assert result == {"vm-a"}

@pytest.mark.asyncio
async def test_attackers_for_vm_a(sample_env):
    analyzer = AttackSurfaceAnalyzer()
    analyzer.load_environment(sample_env)
    result = await analyzer.get_attackers("vm-a")
    assert result == {"vm-c"}

@pytest.mark.asyncio
async def test_no_attackers(sample_env):
    analyzer = AttackSurfaceAnalyzer()
    analyzer.load_environment(sample_env)
    result = await analyzer.get_attackers("vm-c")
    assert result == set()

@pytest.mark.asyncio
async def test_vm_not_found(sample_env):
    analyzer = AttackSurfaceAnalyzer()
    analyzer.load_environment(sample_env)
    with pytest.raises(HTTPException) as exc:
        await analyzer.get_attackers("vm-unknown")
    assert exc.value.status_code == 404
