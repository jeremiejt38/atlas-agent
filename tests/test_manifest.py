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


def test_github_actions_load() -> None:
    data = dict(MINIMAL_MANIFEST)
    data["actions"] = [
        {"type": "github_pr", "target": "atlas", "title": "t", "body": "b", "head": "feat"},
        {"type": "github_pr_merge", "target": "atlas", "pr_number": 1},
        {"type": "github_release", "target": "atlas", "tag": "v0.1.0", "title": "t", "notes": "n"},
        {"type": "github_comment", "target": "atlas", "number": 1, "body": "lgtm"},
    ]
    manifest = Manifest.model_validate(data)
    assert len(manifest.actions) == 4
    assert manifest.actions[1].method == "merge"


def test_obsidian_ovm_new_loads() -> None:
    data = {
        "id": "test-ovm",
        "description": "ovm new",
        "actions": [
            {
                "type": "obsidian_ovm_new",
                "title": "My note",
                "note_type": "project",
                "category": "projects",
                "tags": ["atlas-agent"],
            }
        ],
    }
    manifest = Manifest.model_validate(data)
    assert manifest.actions[0].title == "My note"


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
