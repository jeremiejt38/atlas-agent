"""Command-line interface for atlas-agent."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import typer
import yaml
from pydantic import ValidationError

from atlas_agent.manifest import Manifest
from atlas_agent.runner import Report, execute

app = typer.Typer(
    name="atlas-agent",
    help="Deterministic executor for Devin housekeeping tasks.",
    no_args_is_help=True,
)


def _load_manifest(path: Path) -> Manifest:
    data: dict[str, Any]
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".yaml", ".yml"):
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    return Manifest.model_validate(data)


def _load_env_file(path: Path | None) -> dict[str, str]:
    env: dict[str, str] = {}
    if path is None or not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


@app.command()
def validate(
    manifest: Path = typer.Argument(..., help="Path to JSON or YAML manifest"),
) -> None:
    """Validate a manifest without executing it."""
    try:
        _load_manifest(manifest)
    except ValidationError as exc:
        typer.echo(f"Manifest validation failed:\n{exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo("Manifest is valid.")


@app.command()
def run(
    manifest: Path = typer.Argument(..., help="Path to JSON or YAML manifest"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview actions without applying them"),
    report: Path | None = typer.Option(None, "--report", help="Write JSON report to this file"),
    env_file: Path | None = typer.Option(None, "--env-file", help="Load additional environment variables"),
) -> None:
    """Execute a manifest."""
    try:
        manifest_obj = _load_manifest(manifest)
    except ValidationError as exc:
        typer.echo(f"Manifest validation failed:\n{exc}", err=True)
        raise typer.Exit(code=1) from exc

    extra_env = _load_env_file(env_file)
    if extra_env:
        os.environ.update(extra_env)

    result: Report = execute(manifest_obj, dry_run=dry_run)
    typer.echo(result.to_json())
    if report:
        report.write_text(result.to_json() + "\n", encoding="utf-8")

    code = 0 if result.status == "success" else 1
    raise typer.Exit(code=code)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
