# Project workflow

See the canonical KSP standard in the upstream `KSP` repo. The rules below apply specifically to atlas-agent.

## Branches

- `main` is the stable branch.
- Create short-lived branches from `main`: `feature/<topic>`, `fix/<topic>`, `docs/<topic>`, `chore/<topic>`, `refactor/<topic>` or `test/<topic>`.
- Rebase on `main`, validate tests, then fast-forward merge.
- Delete merged branches after verification.

## Commits

- Atomic Conventional Commits.
- Private repository: descriptions in French.
- Types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `build`, `ci`, `chore`.
- Example: `feat(runner): add obsidian write action`.

## Releases

- Version source of truth: `pyproject.toml`.
- Use Release Please; `release-please-config.json` is configured with `bump-minor-pre-major: true`.
- Annotated tags `vX.Y.Z` are created only on the release PR merge.
- No major release without explicit maintainer approval.

## Validation before merge

```bash
python -m pytest
python -m build
```

See `docs/TESTING.md` for details.
