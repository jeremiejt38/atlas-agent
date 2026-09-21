"""Runner that executes manifest actions and produces a report."""

from __future__ import annotations

import datetime
import json
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from atlas_agent.manifest import (
    Action,
    ActionUnion,
    AtlasJournalAction,
    AtlasProjectAction,
    AtlasServiceAction,
    FileAppendAction,
    FileWriteAction,
    GitCommitAction,
    GitHubPRAction,
    GitPushAction,
    KSPCheckAction,
    Manifest,
    ObsidianCommitAction,
    ObsidianWriteAction,
)


@dataclass
class Context:
    """Execution context shared between actions."""

    manifest: Manifest
    dry_run: bool
    env: dict[str, str]

    def repo_path(self, name: str) -> Path:
        if name not in self.manifest.repositories:
            raise KeyError(f"Unknown repository '{name}'")
        return Path(self.manifest.repositories[name].path).expanduser().resolve()

    def vault_path(self, name: str) -> Path:
        if name not in self.manifest.vaults:
            raise KeyError(f"Unknown vault '{name}'")
        return Path(self.manifest.vaults[name]).expanduser().resolve()


@dataclass
class StepReport:
    index: int
    action_type: str
    status: str  # success | skipped | failed
    message: str
    duration_s: float


@dataclass
class Report:
    task_id: str
    description: str
    dry_run: bool
    status: str  # success | partial | failed
    started_at: str
    finished_at: str
    steps: list[StepReport] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(
            {
                "task_id": self.task_id,
                "description": self.description,
                "dry_run": self.dry_run,
                "status": self.status,
                "started_at": self.started_at,
                "finished_at": self.finished_at,
                "steps": [
                    {
                        "index": s.index,
                        "action_type": s.action_type,
                        "status": s.status,
                        "message": s.message,
                        "duration_s": round(s.duration_s, 3),
                    }
                    for s in self.steps
                ],
            },
            indent=2,
            ensure_ascii=False,
        )


def _run(
    command: list[str],
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    input: str | None = None,  # noqa: A002
    timeout: int = 300,
) -> subprocess.CompletedProcess[str]:
    merged_env = {**os.environ, **(env or {})}
    return subprocess.run(
        command,
        cwd=cwd,
        input=input,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
        env=merged_env,
    )


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def _render_frontmatter(data: dict[str, Any]) -> str:
    import yaml

    return "---\n" + yaml.safe_dump(data, sort_keys=False, allow_unicode=True) + "---\n\n"


def _skip_condition(ctx: Context, action: Action) -> bool:
    cond = getattr(action, "if_", None)
    if not cond:
        return False
    # Support simple env var truthiness: "env.GH_TOKEN"
    if cond.startswith("env."):
        return not ctx.env.get(cond[4:])
    # Fallback: treat non-empty literal as truthy
    return not cond


# ---------------------------------------------------------------------------
# Executors
# ---------------------------------------------------------------------------


def _file_write(ctx: Context, action: FileWriteAction) -> str:
    base = ctx.repo_path(action.target)
    path = action.path if action.path.is_absolute() else base / action.path
    content = action.content
    if action.frontmatter:
        content = _render_frontmatter(action.frontmatter) + content
    if ctx.dry_run:
        return f"Would write {path} ({len(content)} chars)"
    _atomic_write(path, content)
    return f"Wrote {path} ({len(content)} chars)"


def _file_append(ctx: Context, action: FileAppendAction) -> str:
    base = ctx.repo_path(action.target)
    path = action.path if action.path.is_absolute() else base / action.path
    if ctx.dry_run:
        return f"Would append {len(action.content)} chars to {path}"
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if action.ensure_newline and existing and not existing.endswith("\n"):
        existing += "\n"
    _atomic_write(path, existing + action.content)
    return f"Appended to {path}"


def _atlas_journal(ctx: Context, action: AtlasJournalAction) -> str:
    repo = ctx.repo_path(action.target)
    date = action.date or datetime.date.today().isoformat()
    title = action.title
    body = action.content
    cmd: list[str] = [
        "atlas",
        "--repo",
        str(repo),
        "journal",
        "ajouter",
        "--date",
        date,
        "--contenu",
        body,
        title,
    ]
    if ctx.dry_run:
        return f"Would run: {' '.join(cmd)}"
    result = _run(cmd)
    if result.returncode != 0:
        raise RuntimeError(f"atlas journal ajouter failed: {result.stderr.strip()}")
    return f"Created journal entry {date}: {title}"


def _atlas_project(ctx: Context, action: AtlasProjectAction) -> str:
    repo = ctx.repo_path(action.target)
    cmd: list[str] = [
        "atlas",
        "--repo",
        str(repo),
        "projet",
        "maj",
    ]
    if action.statut:
        cmd.extend(["--statut", action.statut])
    if action.notes:
        cmd.extend(["--notes", action.notes])
    cmd.append(action.name)
    if ctx.dry_run:
        return f"Would run: {' '.join(cmd)}"
    result = _run(cmd)
    if result.returncode != 0:
        raise RuntimeError(f"atlas projet maj failed: {result.stderr.strip()}")
    return f"Updated project {action.name}"


def _atlas_service(ctx: Context, action: AtlasServiceAction) -> str:
    repo = ctx.repo_path(action.target)
    cmd: list[str] = [
        "atlas",
        "--repo",
        str(repo),
        "service",
        "ajouter",
        "--nom",
        action.name,
        "--hote",
        action.hote,
        "--acces",
        action.access,
    ]
    if action.domain:
        cmd.extend(["--domaine", action.domain])
    if action.port is not None:
        cmd.extend(["--port", str(action.port)])
    if action.notes:
        cmd.extend(["--notes", action.notes])
    if ctx.dry_run:
        return f"Would run: {' '.join(cmd)}"
    result = _run(cmd)
    if result.returncode != 0:
        raise RuntimeError(f"atlas service ajouter failed: {result.stderr.strip()}")
    return f"Updated service {action.domain}"


def _git_commit(ctx: Context, action: GitCommitAction) -> str:
    repo = ctx.repo_path(action.target)
    if ctx.dry_run:
        return f"Would commit in {repo}: {action.message}"
    add = _run(["git", "add", "-A"], cwd=repo)
    if add.returncode != 0:
        raise RuntimeError(f"git add failed: {add.stderr.strip()}")
    commit = _run(["git", "commit", "-m", action.message], cwd=repo)
    if commit.returncode != 0:
        if "nothing to commit" in commit.stdout.lower() or "rien à valider" in commit.stdout.lower():
            return "Nothing to commit"
        raise RuntimeError(f"git commit failed: {commit.stderr.strip()}")
    return f"Committed: {action.message}"


def _git_push(ctx: Context, action: GitPushAction) -> str:
    repo = ctx.repo_path(action.target)
    branch = action.branch or _run(["git", "branch", "--show-current"], cwd=repo).stdout.strip()
    cmd = ["git", "push", action.remote, branch]
    if ctx.dry_run:
        return f"Would run: {' '.join(cmd)} in {repo}"
    result = _run(cmd, cwd=repo)
    if result.returncode != 0:
        raise RuntimeError(f"git push failed: {result.stderr.strip()}")
    return f"Pushed to {action.remote}/{branch}"


def _github_pr(ctx: Context, action: GitHubPRAction) -> str:
    repo = ctx.repo_path(action.target)
    cmd: list[str] = [
        "gh",
        "pr",
        "create",
        "--title",
        action.title,
        "--body",
        action.body,
        "--head",
        action.head,
        "--base",
        action.base,
    ]
    if action.draft:
        cmd.append("--draft")
    if ctx.dry_run:
        return f"Would run: {' '.join(cmd)} in {repo}"
    result = _run(cmd, cwd=repo)
    if result.returncode != 0:
        raise RuntimeError(f"gh pr create failed: {result.stderr.strip()}")
    return f"Created PR: {result.stdout.strip()}"


def _ksp_check(ctx: Context, action: KSPCheckAction) -> str:
    repo = ctx.repo_path(action.target)
    issues: list[str] = []
    required = ["README.md", "CHANGELOG.md", "LICENSE", "AGENTS.md", "docs/PROJECT_WORKFLOW.md", "docs/TESTING.md"]
    for item in required:
        if not (repo / item).exists():
            issues.append(f"Missing {item}")

    pyproject = repo / "pyproject.toml"
    if pyproject.exists():
        import tomllib
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        version = data.get("project", {}).get("version")
        if not version:
            issues.append("pyproject.toml missing project.version")
    else:
        issues.append("No pyproject.toml")

    release_config = repo / "release-please-config.json"
    if release_config.exists():
        import json
        cfg = json.loads(release_config.read_text(encoding="utf-8"))
        pkg = cfg.get("packages", {}).get(".", {})
        if pkg.get("bump-patch-for-minor-pre-major") is True:
            issues.append("release-please has forbidden bump-patch-for-minor-pre-major=true")

    if issues:
        msg = "KSP check found issues:\n" + "\n".join(f"- {i}" for i in issues)
        if action.fix:
            raise RuntimeError("KSP auto-fix not yet implemented")
        raise RuntimeError(msg)
    return "KSP check passed"


def _obsidian_write(ctx: Context, action: ObsidianWriteAction) -> str:
    vault = ctx.vault_path(action.vault)
    path = action.path if action.path.is_absolute() else vault / action.path
    content = action.content
    if action.frontmatter:
        content = _render_frontmatter(action.frontmatter) + content
    if ctx.dry_run:
        return f"Would write {path} in vault {action.vault}"
    _atomic_write(path, content)
    return f"Wrote Obsidian note {path.relative_to(vault)}"


def _obsidian_commit(ctx: Context, action: ObsidianCommitAction) -> str:
    vault = ctx.vault_path(action.vault)
    if ctx.dry_run:
        return f"Would commit in vault {action.vault}: {action.message}"
    add = _run(["git", "add", "-A"], cwd=vault)
    if add.returncode != 0:
        raise RuntimeError(f"git add in vault failed: {add.stderr.strip()}")
    commit = _run(["git", "commit", "-m", action.message], cwd=vault)
    if commit.returncode != 0:
        if "nothing to commit" in commit.stdout.lower() or "rien à valider" in commit.stdout.lower():
            return "Nothing to commit in vault"
        raise RuntimeError(f"git commit in vault failed: {commit.stderr.strip()}")
    return f"Committed vault: {action.message}"


_EXECUTORS: dict[str, Callable[[Context, Action], str]] = {
    "file_write": _file_write,
    "file_append": _file_append,
    "atlas_journal": _atlas_journal,
    "atlas_project": _atlas_project,
    "atlas_service": _atlas_service,
    "git_commit": _git_commit,
    "git_push": _git_push,
    "github_pr": _github_pr,
    "ksp_check": _ksp_check,
    "obsidian_write": _obsidian_write,
    "obsidian_commit": _obsidian_commit,
}


def execute(manifest: Manifest, dry_run: bool = False) -> Report:
    """Execute all actions in the manifest and return a report."""
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    ctx = Context(
        manifest=manifest,
        dry_run=dry_run,
        env=dict(os.environ),
    )
    steps: list[StepReport] = []
    failed = False

    for idx, action in enumerate(manifest.actions):
        action_type = action.type
        start = time.perf_counter()
        if _skip_condition(ctx, action):
            steps.append(
                StepReport(
                    index=idx,
                    action_type=action_type,
                    status="skipped",
                    message="Condition evaluated falsy",
                    duration_s=time.perf_counter() - start,
                )
            )
            continue
        try:
            executor = _EXECUTORS[action_type]
            message = executor(ctx, action)
            status = "success"
        except Exception as exc:  # noqa: BLE001
            message = str(exc)
            status = "failed"
            failed = True
        steps.append(
            StepReport(
                index=idx,
                action_type=action_type,
                status=status,
                message=message,
                duration_s=time.perf_counter() - start,
            )
        )
        if failed:
            break

    finished = datetime.datetime.now(datetime.timezone.utc).isoformat()
    any_failed = any(s.status == "failed" for s in steps)
    any_success = any(s.status == "success" for s in steps)
    report_status = "failed" if any_failed else ("success" if any_success else "partial")
    return Report(
        task_id=manifest.id,
        description=manifest.description,
        dry_run=dry_run,
        status=report_status,
        started_at=started,
        finished_at=finished,
        steps=steps,
    )
