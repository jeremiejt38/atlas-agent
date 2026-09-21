"""Tests for manifest parsing and validation."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from atlas_agent.manifest import Manifest


MINIMAL_MANIFEST = {
    "id": "test-001",
    "description": "Minimal test manifest",
    "repositories": {"atlas": {"path": "/tmp/atlas"}},
    "actions": [
        {"type": "file_write", "target": "atlas", "path": "test.md", "content": "# test"}
    ],
}


def test_minimal_manifest_loads() -> None:
    manifest = Manifest.model_validate(MINIMAL_MANIFEST)
    assert manifest.id == "test-001"
    assert manifest.repositories["atlas"].path == Path("/tmp/atlas")


def test_missing_repository_raises() -> None:
    data = dict(MINIMAL_MANIFEST)
    data["actions"] = [
        {"type": "file_write", "target": "missing", "path": "test.md", "content": "# test"}
    ]
    with pytest.raises(ValidationError, match="unknown target"):
        Manifest.model_validate(data)


def test_obsidian_action_without_repo() -> None:
    data = {
        "id": "test-obsidian",
        "description": "Obsidian write without repo",
        "vaults": {"obsidian": "/tmp/vault"},
        "actions": [
            {
                "type": "obsidian_write",
                "vault": "obsidian",
                "path": "Projects/test.md",
                "content": "# test",
            }
        ],
    }
    manifest = Manifest.model_validate(data)
    assert manifest.vaults["obsidian"] == Path("/tmp/vault")


def test_invalid_action_type() -> None:
    data = dict(MINIMAL_MANIFEST)
    data["actions"] = [{"type": "unknown_action", "target": "atlas"}]
    with pytest.raises(ValidationError):
        Manifest.model_validate(data)


def test_empty_actions_fails() -> None:
    data = {
        "id": "test-empty",
        "description": "Empty actions",
        "repositories": {"atlas": {"path": "/tmp/atlas"}},
        "actions": [],
    }
    with pytest.raises(ValidationError):
        Manifest.model_validate(data)
