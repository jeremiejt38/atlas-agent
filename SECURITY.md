# Security Policy

## Supported versions

| Version | Supported |
| --- | --- |
| Latest stable | Yes |
| Older releases | No, unless stated otherwise |

## Reporting a vulnerability

Do not report vulnerabilities through public issues. Contact Jérémie directly or use GitHub Private Vulnerability Reporting when enabled. Include the affected version, reproduction steps, impact and any mitigation you identified.

## Response targets

- Acknowledgement: as soon as possible.
- Status update: within 48 hours.
- Fix or mitigation: as soon as reasonably possible after confirmation.

## Security rules

- Never commit secrets, access tokens, private keys, production databases or personally identifiable production data.
- Keep `.env` files ignored; version only `.env.example` with safe placeholders.
- Store deployment secrets in the hosting platform’s secret manager or in the Atlas vault.
- Keep dependencies and base images updated.
- Use least-privilege credentials and service accounts.

## Scope

atlas-agent may execute git operations, GitHub CLI commands and file writes on local repositories. It does not run arbitrary shell commands from manifests; command execution is limited to well-defined action types with validated parameters.
