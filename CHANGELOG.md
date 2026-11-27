# Changelog

Versions follow the vendored Brain CLI (`plugins/cbox-brain/scripts/brain.mjs`). Earlier versions (0.4.0 to 0.8.0) were not tagged; their commits carry the version in the subject.

## 0.13.1 — 2026-11-27

- **Your answer stays visible in focus view.** Stop is silent; optional reminders arrive before the answer through PreToolUse, without starting another turn.
- **Scratchpads are not repository work.** File and notebook edits outside the Git top level no longer trigger handoff reminders, including paths through symlinks.
- **Plugin updates take effect.** Hooks use the bundled CLI before an older `brain` on PATH. An explicit `BRAIN_CLI` override still works for other events; Stop remains silent even with an older override.
- Verified with 12 real Claude Code 2.1.316 focus-view sessions on Linux, comparing the original 0.10.1 plugin and this fix. All six fixed sessions retained the requested answer with no Stop feedback. macOS was not tested.

## 0.13.0 — 2026-11-26

The CLI from cbox-brain 0.13.0 (cboxdk/cbox-brain#55).

- **Several organizations at once.** `brain login` signs in to each of your organizations, and every session uses the one its repository belongs to. Nothing to switch.
- **No guessing.** If you are in several organizations and a repository belongs to none of them (no project, and no root for its GitHub owner), the session start says so in one line with `brain org set <slug>`; nothing is read or written there.
- **Personal stays personal.** What concerns only you or your machine is filed in your personal space.
- **One repository only.** `brain setup --local` wires Claude Code for the current repository alone, without the plugin and without committing anything. If you use the plugin, Brain runs in every repository; uninstall it to keep Brain to `--local` repositories.

## 0.12.0 — 2026-11-26

The CLI from cbox-brain 0.12.0 (cboxdk/cbox-brain#53).

- **You hear when a newer Brain CLI is out.** Brain now names its current CLI on every answer. When this copy is behind, the session start adds one line for the agent to pass on: the new version and how to update it. For this plugin that is `claude plugin marketplace update cbox-brain-plugin`, then `claude plugin update cbox-brain@cbox-brain-plugin`. `brain doctor` shows the same line. Nothing updates by itself.
- **A CLI too old to work is refused with what to run.** Brain serves CLI 0.10.0 and newer. An older one gets the update command as its session-start context and on each tool call, instead of errors without an explanation.

## 0.11.1 — 2026-11-25

The CLI from cbox-brain 0.11.1. This also brings in 0.10.2 and 0.11.0, which were not synced here.

- **No more 400 at the start of every Claude Code session.** Claude Code 2.1.33x first sends `server/discover` with its protocol version (2026-07-28) in `_meta`. `brain mcp` now sends that version as `MCP-Protocol-Version` and mirrors `Mcp-Method` and `Mcp-Name`, as Brain's MCP server requires. Before, Brain refused the probe and Claude Code fell back to `initialize`.
- **Shorter Brain lines in replies.** `tell_the_person` is one line ("Saved to Brain: <type> in <space> · <url>"). The stop reminder asks the agent to end with that line and not to mention Brain when nothing was learned.
- **0.11.0:** `brain setup` wires Amp, on the machine and in its orbs.
- **0.10.2:** the install signs in again when the sign-in is dead, `brain login` ends once signed in, and `brain` lands on `PATH`.

## 0.10.1 — 2026-11-13

- **The deploy gate names only what blocks.** When `PreToolUse` denies a command, the reason now names just the policy that blocks and the word it blocks on (`blocked_on`), for example `"Octane is banned in Cbox apps" [mem_…], on \`octane\``. Policies that only warn are no longer listed as blockers. A false hit is to be reported to the person, not reworded around. A Brain server that sends no `blocked_on` gets the old wording.
- Pairs with the gate fix in Brain (cboxdk/cbox-brain#23). A blocking policy now blocks only on a whole word of its subject, never on a word of its rationale. That fix takes effect when Brain is deployed.

## 0.10.0 — 2026-11-13

First tagged release.

- **Retries are recorded once.** `brain remember` and `brain mcp` send a `client_key` with every `brain_remember`. A keyed write is sent again after a dropped connection or a 502, 503 or 504, and the same write in the same session answers the memory written the first time (`replayed`) instead of a duplicate.
- **One install** (CLI 0.9.0, synced here for the first time): `brain setup` wires Claude Code, Codex, Cursor, VS Code Copilot, Devin, Gemini and OpenCode (MCP through `brain mcp`, a rules block, hooks in each agent's format). `brain doctor` shows which agents have used Brain. `brain update` replaces the CLI with the server's copy, checked against its sha256.
- **Hooks:** fixed a race in which two concurrent hooks could both take over a stale dedupe claim and inject the same context twice.
- **README:** leads with the installer (`curl -fsSL https://app.cboxbrain.com/install | sh`). The MCP server is now connected through `brain mcp` (one sign-in, the repository picks the organization). Requires Node 22.
