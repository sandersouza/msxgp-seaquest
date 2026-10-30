# Seaquest project instructions

## One GitHub issue per chat

User instruction, 2026-10-30: whenever work starts on a new GitHub issue, continue
in a **new Codex chat inside this same Seaquest project**. Do not implement the
next issue in the current issue's chat.

- Create or reuse the dedicated chat titled `ISSUE #<number>` in the Seaquest
  project. Avoid duplicate chats for the same active issue.
- Carry over the issue URL, goal, dependencies, branch/commit, pending changes,
  verified evidence, limitations and next actions. Keep a repository handoff when
  necessary so the next chat does not need to reconstruct the conversation.
- Once handed off, the old chat must stop changing the shared checkout. Do not
  run two issue implementations concurrently in the same working tree.
- Continue autonomously along satisfied dependencies toward the first playable
  MSX1/openMSX version, keeping GitHub issues, project statuses and PRs updated.
  Finishing an issue does not require asking again to start its successor chat.
- Only close an issue after its own acceptance/delivery conditions are met.

Project context: MSX1 with 64 KiB RAM / 16 KiB VRAM, no expansions, original Atari
2600 gameplay authority. Read `docs/project-workflow.md`, the relevant issue copy
under `.github/issues/`, and applicable plans/handoffs before implementation.
