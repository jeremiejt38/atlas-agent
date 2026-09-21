<div align="center">

# atlas-agent

[![Version](https://img.shields.io/badge/version-v0.1.0-blue)](https://github.com/jeremiejt38/atlas-agent/releases)
[![Status](https://img.shields.io/badge/status-alpha-orange)](https://github.com/jeremiejt38/atlas-agent)
[![Python](https://img.shields.io/badge/python-%3E%3D3.11-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

**Deterministic executor for KSP, Atlas, GitHub and Obsidian housekeeping offloaded from Devin.**

</div>

## Introduction

atlas-agent takes over the repetitive "meta" work Devin does after a coding session: updating Atlas journals and project cards, keeping KSP compliance consistent, running lightweight GitHub operations and syncing the Obsidian vault.

The Obsidian backend is provided by [atlas-obsidian](https://github.com/jeremiejt38/atlas-obsidian) (formerly obsidian-manager), a Rust daemon that manages the Obsidian vault autonomously.

Devin remains responsible for thinking through the content, but delegates the execution to atlas-agent through a turnkey JSON/YAML manifest. The agent applies actions mechanically and does not use an LLM to rewrite content in the critical path.

## Features

- **Manifest-driven**: one task file describes atomic actions (write files, update projects, commit, push, Obsidian sync, KSP checks).
- **Deterministic**: no LLM is required to run a manifest; actions are validated and applied mechanically.
- **Atlas integration**: creates journal entries, updates project cards, edits service/network docs.
- **Git + GitHub integration**: commits, pushes, creates/merges PRs, creates releases and comments.
- **Obsidian integration**: writes notes into the PARA vault, commits them via git, or delegates to the `atlas-obsidian` (`ovm`) daemon.
- **KSP checks**: audits README, CHANGELOG, version and release-please consistency.
- **Dry-run + validation**: preview and validate manifests before applying them.

## Installation

```bash
git clone https://github.com/jeremiejt38/atlas-agent.git
cd atlas-agent
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
```

## Quick start

Validate a manifest:

```bash
.venv/bin/atlas-agent validate examples/manifest-example.json
```

Preview what would happen:

```bash
.venv/bin/atlas-agent run examples/manifest-example.json --dry-run
```

Apply it:

```bash
.venv/bin/atlas-agent run examples/manifest-example.json
```

## Manifest overview

```json
{
  "id": "task-20260921-001",
  "description": "Post-session housekeeping",
  "repositories": {
    "atlas": "/home/jerem/workspace/atlas"
  },
  "actions": [
    {
      "type": "atlas_journal",
      "target": "atlas",
      "date": "2026-09-21",
      "slug": "atlas-agent-init",
      "title": "Initial setup of atlas-agent",
      "content": "Started the atlas-agent project..."
    },
    {
      "type": "atlas_project",
      "target": "atlas",
      "name": "atlas-agent",
      "fields": { "statut": "en cours" }
    },
    {
      "type": "git_commit",
      "target": "atlas",
      "message": "docs(atlas): journal and project update for atlas-agent"
    },
    {
      "type": "git_push",
      "target": "atlas"
    }
  ]
}
```

See `examples/manifest-example.json` for a complete example.

## Development

```bash
python -m pytest
python -m build
```

See `docs/PROJECT_WORKFLOW.md` and `docs/TESTING.md` for contribution guidelines.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) and the [releases](https://github.com/jeremiejt38/atlas-agent/releases) for the detailed version history.

## License

Distributed under the MIT license. See [LICENSE](LICENSE).
