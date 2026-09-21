"""Manifest schema for atlas-agent."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ActionType(str, Enum):
    FILE_WRITE = "file_write"
    FILE_APPEND = "file_append"
    ATLAS_JOURNAL = "atlas_journal"
    ATLAS_PROJECT = "atlas_project"
    ATLAS_SERVICE = "atlas_service"
    GIT_COMMIT = "git_commit"
    GIT_PUSH = "git_push"
    GITHUB_PR = "github_pr"
    GITHUB_PR_MERGE = "github_pr_merge"
    GITHUB_RELEASE = "github_release"
    GITHUB_COMMENT = "github_comment"
    KSP_CHECK = "ksp_check"
    OBSIDIAN_WRITE = "obsidian_write"
    OBSIDIAN_COMMIT = "obsidian_commit"
    OBSIDIAN_OVM_NEW = "obsidian_ovm_new"


class RepositoryMap(BaseModel):
    """Named repositories referenced by actions."""

    model_config = ConfigDict(extra="forbid")

    path: Path = Field(..., description="Absolute path to the repository root")


class Action(BaseModel):
    """Base action with optional run condition."""

    model_config = ConfigDict(extra="forbid")

    if_: str | None = Field(default=None, alias="if", description="Skip if condition evaluates falsy")


class FileWriteAction(Action):
    type: Literal[ActionType.FILE_WRITE]
    target: str = Field(..., description="Repository or vault key from repositories/vaults map")
    path: Path = Field(..., description="Relative or absolute path")
    content: str = Field(..., description="Full file content")
    frontmatter: dict[str, Any] | None = Field(default=None, description="YAML frontmatter to prepend")


class FileAppendAction(Action):
    type: Literal[ActionType.FILE_APPEND]
    target: str
    path: Path
    content: str
    ensure_newline: bool = True


class AtlasJournalAction(Action):
    type: Literal[ActionType.ATLAS_JOURNAL]
    target: str
    date: str | None = None
    title: str
    content: str


class AtlasProjectAction(Action):
    type: Literal[ActionType.ATLAS_PROJECT]
    target: str
    name: str
    statut: str | None = None
    notes: str | None = None


class AtlasServiceAction(Action):
    type: Literal[ActionType.ATLAS_SERVICE]
    target: str
    domain: str
    name: str
    hote: str
    port: int | None = None
    access: str = "prive"
    notes: str | None = None


class GitCommitAction(Action):
    type: Literal[ActionType.GIT_COMMIT]
    target: str
    message: str


class GitPushAction(Action):
    type: Literal[ActionType.GIT_PUSH]
    target: str
    remote: str = "origin"
    branch: str | None = None


class GitHubPRAction(Action):
    type: Literal[ActionType.GITHUB_PR]
    target: str
    title: str
    body: str
    head: str
    base: str = "main"
    draft: bool = False


class GitHubPRMergeAction(Action):
    type: Literal[ActionType.GITHUB_PR_MERGE]
    target: str
    pr_number: int
    method: Literal["merge", "squash", "rebase"] = "merge"
    delete_branch: bool = False


class GitHubReleaseAction(Action):
    type: Literal[ActionType.GITHUB_RELEASE]
    target: str
    tag: str
    title: str
    notes: str
    draft: bool = False
    prerelease: bool = False


class GitHubCommentAction(Action):
    type: Literal[ActionType.GITHUB_COMMENT]
    target: str
    number: int
    body: str


class KSPCheckAction(Action):
    type: Literal[ActionType.KSP_CHECK]
    target: str
    fix: bool = False


class ObsidianWriteAction(Action):
    type: Literal[ActionType.OBSIDIAN_WRITE]
    vault: str
    path: Path
    content: str
    frontmatter: dict[str, Any] | None = None


class ObsidianCommitAction(Action):
    type: Literal[ActionType.OBSIDIAN_COMMIT]
    vault: str
    message: str


class ObsidianOvmNewAction(Action):
    type: Literal[ActionType.OBSIDIAN_OVM_NEW]
    title: str
    note_type: str = "simple"
    category: str = "resources"
    subcategory: str | None = None
    tags: list[str] = Field(default_factory=list)
    body: str = ""
    config: Path | None = None


ActionUnion = Annotated[
    FileWriteAction
    | FileAppendAction
    | AtlasJournalAction
    | AtlasProjectAction
    | AtlasServiceAction
    | GitCommitAction
    | GitPushAction
    | GitHubPRAction
    | GitHubPRMergeAction
    | GitHubReleaseAction
    | GitHubCommentAction
    | KSPCheckAction
    | ObsidianWriteAction
    | ObsidianCommitAction
    | ObsidianOvmNewAction,
    Field(discriminator="type"),
]


class Manifest(BaseModel):
    """Top-level task manifest."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., pattern=r"^[a-zA-Z0-9_.:-]+$")
    description: str
    repositories: dict[str, RepositoryMap] = Field(default_factory=dict)
    vaults: dict[str, Path] = Field(default_factory=dict)
    actions: list[ActionUnion] = Field(..., min_length=1)

    @model_validator(mode="after")
    def _validate_targets(self) -> "Manifest":
        for action in self.actions:
            target = getattr(action, "target", None)
            if target is not None and target not in self.repositories:
                raise ValueError(f"Action references unknown target '{target}'")
            vault = getattr(action, "vault", None)
            if vault is not None and vault not in self.vaults:
                raise ValueError(f"Action references unknown vault '{vault}'")
        return self
