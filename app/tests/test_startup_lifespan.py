import os
from contextlib import contextmanager
from pathlib import Path

import pytest
from asgi_lifespan import LifespanManager

from attack_surface import app


@contextmanager
def temp_env(value: str | None):
    """Temporarily override ENV_PATH for startup tests."""
    previous = os.environ.get("ENV_PATH")
    if value is None:
        os.environ.pop("ENV_PATH", None)
    else:
        os.environ["ENV_PATH"] = value
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("ENV_PATH", None)
        else:
            os.environ["ENV_PATH"] = previous


@pytest.mark.asyncio
async def test_startup_requires_env_path() -> None:
    with temp_env(None):
        with pytest.raises(RuntimeError, match="Missing ENV_PATH"):
            async with LifespanManager(app):
                pass


@pytest.mark.asyncio
async def test_startup_fails_when_file_missing() -> None:
    with temp_env("tests/does-not-exist.json"):
        with pytest.raises(RuntimeError, match="File not found"):
            async with LifespanManager(app):
                pass


@pytest.mark.asyncio
async def test_startup_fails_on_invalid_payload(tmp_path: Path) -> None:
    invalid_file = tmp_path / "invalid_env.json"
    invalid_file.write_text('{"vms": []}', encoding="utf-8")
    with temp_env(str(invalid_file)):
        with pytest.raises(RuntimeError, match="Invalid environment configuration"):
            async with LifespanManager(app):
                pass
