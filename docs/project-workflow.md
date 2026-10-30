# Delivery and project tracking

Work is tracked in [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7).
Only change Seaquest items. Preserve the project's shared fields and other projects.

## One issue per Codex chat

From the owner's instruction on 2026-10-30, start every new GitHub issue in a
**separate chat within the same Seaquest project**, titled `ISSUE #<number>`.
Reuse an existing dedicated issue chat when present. Transfer its URL, scope,
dependencies, branch/commit, pending changes, evidence and next actions; use
`docs/handoffs/` for durable implementation context. The previous chat stops
editing the shared checkout after handoff. Continue autonomously to the next
dependency-ready issue through another chat, without repeated permission requests.
The repository's `AGENTS.md` makes this rule visible to future agents.

## Issue and PR lifecycle

- Backlog: planned work; Ready: prerequisite evidence available; In progress:
  implementation underway; In review: delivery checks/review pending; Done:
  acceptance met and delivery integrated.
- Issues carry a category label, one priority label matching project Priority,
  Size and numeric Estimate (hours, not a deadline). Task type is recorded in the
  body because the native GitHub issue-type field did not persist for this repo.
- Write complete local copies under `.github/issues/` before publication, keep
  dependencies as linked issues and synchronize significant updates.
- Use a scoped `codex/<kind>/<issue>-<description>` branch and linked PR. Obtain
  independent review, fix material findings and run relevant checks before merge.
  Close only fully delivered issues; do not close work because a ROM merely boots.
- No milestone exists; reuse the existing no-milestone convention unless the
  owner selects a milestone scheme. Phases in the roadmap are planning groups.

## CI boundary

The Synthetic build and tests workflow uses pinned action commits and a pinned
sjasmplus commit on Ubuntu 24.04 with Python 3.12. It runs synthetic unit tests and
builds/validates the diagnostic cartridge and assembles the synthetic renderer
probe without original reference inputs. It
also rejects accidentally tracked original ROM inputs. The ROM and hash manifest
are uploaded as an explicitly named diagnostic artifact with a 14-day retention.

`bash scripts/ci.sh` reproduces these build/test steps locally. No network secrets,
original ROM downloads or expanded write permissions are required. Public CI
does **not** establish reference-ROM equivalence, openMSX runtime acceptance or
physical-machine compatibility. Local `make reference-check`, `make disassemble`
and `make smoke` provide the additional evidence they explicitly describe.
