# atlas-agent Development Guidelines

- Follow `docs/PROJECT_WORKFLOW.md` for branches, Conventional Commits, validation, merges, releases and branch cleanup.
- Keep `main` stable. Work from short-lived `feature/*`, `fix/*`, `docs/*`, `chore/*`, `refactor/*` or `test/*` branches.
- Rebase and fast-forward validated work into `main`; delete merged branches after verification.
- Keep commits atomic and use Conventional Commits.
- Release only through reviewed release PRs and annotated `vX.Y.Z` tags.
- Default to patch releases. Use a minor release for a coherent feature milestone. Never approve or create a major release without explicit maintainer approval.
- Never jump directly from `X.0.0` to `(X+1).0.0`. A major version consolidates a roadmap of milestones that must each ship first as their own minor release within the current major series (`X.1.0`, `X.2.0`, …), with patch versions between them (`X.0.1`, `X.0.2`, `X.1.1`, …).
- Run the project validation commands before merging; document them in `docs/TESTING.md`.
- Keep one authoritative project version in `pyproject.toml`.
- Keep detailed release history in `CHANGELOG.md` and GitHub Releases, not as a growing README section.
- Update README sections and roadmap whenever project behavior, setup, support or planned scope changes.
- Public documentation and commit messages in English; private repository commit descriptions may be in French.
- Never commit secrets, private data or generated production artifacts.
- Talos delegation is disabled by default. When enabled, delegate only isolated sandboxed jobs and review every result before integration.

## Project-specific constraints

- atlas-agent is a **deterministic executor**: it does not call an LLM to decide or rewrite content. Devin supplies the content in a manifest, atlas-agent applies it.
- The manifest schema is the public interface; keep it versioned and backward-compatible.
- Atlas operations reuse the existing `atlas` CLI from the Atlas repo when possible.
- GitHub operations use the `gh` CLI and require a configured `GH_TOKEN` or interactive `gh auth`.
- Obsidian operations write directly into the configured vault path and commit via git.
- KSP checks run read-only audits by default; applying corrections requires explicit approval in the manifest.
- All filesystem writes use temporary files + rename (atomic) when feasible.
- Use subprocess for external tools (`git`, `gh`, `atlas`) and never embed credentials.
