# Tests

## Validation commands

| Level | Command | Expected |
| --- | --- | --- |
| Format / types | `python -m py_compile src/atlas_agent/**/*.py` | No syntax errors |
| Unit tests | `python -m pytest` | All tests pass |
| Build | `python -m build` | Wheel and sdist build successfully |

## Test structure

- `tests/test_manifest.py` — manifest schema validation and edge cases.
- `tests/test_runner.py` — runner orchestration, dry-run mode, error handling.
- `tests/executors/` — executor unit tests using temporary git repos and files.

## Rules

- Use temporary directories and fixtures; never touch production repositories.
- Mock external CLI calls (`git`, `gh`, `atlas`) when testing GitHub/Atlas executors.
- Each bug fix must include a regression test when reasonable.
- Run the validation commands before merging into `main`.
