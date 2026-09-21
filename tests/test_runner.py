"""Tests for the deterministic runner."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas_agent.manifest import Manifest
from atlas_agent.runner import execute


def test_file_write_dry_run(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    manifest = Manifest.model_validate(
        {
            "id": "dry-001",
            "description": "Dry-run file write",
            "repositories": {"atlas": {"path": str(repo)}},
            "actions": [
                {
                    "type": "file_write",
                    "target": "atlas",
                    "path": "hello.md",
                    "content": "# Hello",
                    "frontmatter": {"tags": ["test"]},
                }
            ],
        }
    )
    report = execute(manifest, dry_run=True)
    assert report.status == "success"
    assert (repo / "hello.md").exists() is False
    assert "Would write" in report.steps[0].message


def test_file_write_applies(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    manifest = Manifest.model_validate(
        {
            "id": "write-001",
            "description": "Apply file write",
            "repositories": {"atlas": {"path": str(repo)}},
            "actions": [
                {
                    "type": "file_write",
                    "target": "atlas",
                    "path": "hello.md",
                    "content": "# Hello",
                }
            ],
        }
    )
    report = execute(manifest, dry_run=False)
    assert report.status == "success"
    written = repo / "hello.md"
    assert written.exists()
    assert written.read_text(encoding="utf-8") == "# Hello"


def test_git_commit_in_temp_repo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    import subprocess

    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)

    manifest = Manifest.model_validate(
        {
            "id": "git-001",
            "description": "Git commit",
            "repositories": {"atlas": {"path": str(repo)}},
            "actions": [
                {
                    "type": "file_write",
                    "target": "atlas",
                    "path": "hello.md",
                    "content": "# Hello",
                },
                {
                    "type": "git_commit",
                    "target": "atlas",
                    "message": "test: add hello.md",
                },
            ],
        }
    )
    report = execute(manifest, dry_run=False)
    assert report.status == "success"
    log = subprocess.run(
        ["git", "log", "--oneline"], cwd=repo, capture_output=True, text=True, check=True
    )
    assert "test: add hello.md" in log.stdout


def test_execution_stops_on_failure(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    manifest = Manifest.model_validate(
        {
            "id": "fail-001",
            "description": "Failure stops execution",
            "repositories": {"atlas": {"path": str(repo)}},
            "actions": [
                {
                    "type": "git_commit",
                    "target": "atlas",
                    "message": "empty commit",
                },
                {
                    "type": "file_write",
                    "target": "atlas",
                    "path": "hello.md",
                    "content": "# Hello",
                },
            ],
        }
    )
    report = execute(manifest, dry_run=False)
    assert report.status == "failed"
    assert report.steps[0].status == "failed"
    assert len(report.steps) == 1
