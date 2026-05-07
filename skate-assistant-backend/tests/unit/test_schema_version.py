"""Schema drift and migration discipline tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from app.services import schema_version


def test_expected_schema_version_matches_initial_revision() -> None:
    assert schema_version.get_expected_schema_version() == "20260507_0001"


@pytest.mark.asyncio
async def test_validate_schema_compatibility_passes_when_versions_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(schema_version, "get_expected_schema_version", lambda: "20260507_0001")

    async def _fake_current() -> str:
        return "20260507_0001"

    monkeypatch.setattr(schema_version, "get_current_db_schema_version", _fake_current)
    assert await schema_version.validate_schema_compatibility() == "20260507_0001"


@pytest.mark.asyncio
async def test_validate_schema_compatibility_raises_on_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(schema_version, "get_expected_schema_version", lambda: "20260507_0001")

    async def _fake_current() -> str:
        return "old_rev"

    monkeypatch.setattr(schema_version, "get_current_db_schema_version", _fake_current)

    with pytest.raises(RuntimeError, match="Schema drift detected"):
        await schema_version.validate_schema_compatibility()


def test_migration_has_upgrade_and_downgrade_contract() -> None:
    migration_file = (
        Path(__file__).resolve().parents[2]
        / "migrations/versions/20260507_0001_initial_schema.py"
    )
    content = migration_file.read_text(encoding="utf-8")
    assert "def upgrade()" in content
    assert "def downgrade()" in content
    assert "op.create_table(" in content
    assert "audit_log" in content
    assert "op.drop_table(\"audit_log\")" in content


def test_migration_module_importable() -> None:
    migration_file = (
        Path(__file__).resolve().parents[2]
        / "migrations/versions/20260507_0001_initial_schema.py"
    )
    spec = importlib.util.spec_from_file_location("story12_migration", migration_file)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert getattr(module, "revision") == "20260507_0001"
