# Cbox Brain for Claude Code

The plugin that makes Claude Code read your team's shared memory before it works and write to it after. Licensed under MIT.

[Cbox Brain](https://cboxbrain.com) is persistent, versioned memory for people, teams and AI agents: facts, decisions, learnings, procedures and policies, with provenance and history. Connecting the MCP server gives an agent the tools. This plugin makes it use them without being asked.

## Install

The simplest way is Brain's installer. It installs the CLI, signs you in once, installs this plugin in Claude Code and wires every other coding agent it finds:

```bash
curl -fsSL https://app.cboxbrain.com/install | sh
```

By hand, in Claude Code:

```
/plugin marketplace add cboxdk/cbox-brain-plugin
/plugin install cbox-brain@cbox-brain-plugin
```

Then sign in, and connect the MCP server through the CLI. The hooks read nothing until you have signed in:

```bash
node ~/.claude/plugins/marketplaces/cbox-brain-plugin/plugins/cbox-brain/scripts/brain.mjs login
claude mcp add --scope user cbox-brain -- node ~/.claude/plugins/marketplaces/cbox-brain-plugin/plugins/cbox-brain/scripts/brain.mjs mcp --agent claude-code
```

`login` opens Cbox ID in your browser (authorization code with PKCE; `--hint <your Cbox ID user id>` asks on your phone instead, `--device` uses the device grant) and stores the credentials in `~/.config/cbox-brain/credentials.json`, mode 600. Nothing is printed. A self-hosted Brain: `login --server https://brain.example.com`. A machine token from your Brain's Settings works too: `BRAIN_TOKEN` in the environment.

`brain mcp` is the MCP server on stdio. One sign-in serves the hooks and the tools, and the repository picks the organization. It also gives every `brain_remember` a `client_key`, so a write whose answer was lost and is sent again is recorded once. The plain HTTP server (`claude mcp add --transport http cbox-brain https://app.cboxbrain.com/mcp`) works as well, but it has neither.

Requires Node 22 or newer. No dependencies: the CLI is one file, `plugins/cbox-brain/scripts/brain.mjs`.

## What the hooks do

| Hook | What lands in the agent's context |
|---|---|
| `SessionStart` (also after a compaction) | "Cbox Brain context for `<project>`": the last session's handoff, the current decisions and policies, the open reminders, the nearest procedures and learnings, open contradictions and the tags to search by, labelled as a selection with each line's status. Shorter after a compaction |
| `UserPromptSubmit` | what changed in Brain since the previous prompt (accepted, promoted, superseded, archived; new decision and policy proposals) plus up to three memories near the prompt, within about 1500 characters; a question about the past also gets a nudge to search Brain. The ids are acknowledged as seen, so the Decisions page shows which agents saw a decision |
| `PreToolUse` (Bash, edits, `brain_remember`, `brain_handoff`) | counts the work done; a deploy-shaped command (`deploy`, `migrate`, `git push`, `git tag`, `gh release`, `kubectl`, `tofu`, `terraform`, `helm`) goes through Brain's gate: a warning with the matched policies, or a deny when a policy tagged `blocking` matches |
| `PreCompact` | instructions for the compaction summary: keep what was learned and not yet remembered, the memory ids cited, the project, and what is left to do |
| `Stop` | after more than eight tool calls with nothing remembered, one reminder to remember the learnings by itself and show where they went; after files changed or a commit with no handoff, one reminder to write `brain_handoff` if the work is unfinished |

The agent reads the delta instead of re-fetching, so the cost per turn is small: one request to `/api/v1/changes` with a cursor kept in `~/.cache/cbox-brain/<project>.cursor`.

The `using-brain` skill tells the agent when to call which tool: `brain_context` at the start, `brain_search` before writing or deciding, `brain_remember` after a learning or a decision, `brain_ack` when acting on a decision, `brain_supersede` when a decision changes, a reminder for what belongs to other work, and `brain_handoff` before stopping with work unfinished.

## Fails open, never breaks a session

No Node, no CLI, no network, not signed in: the hooks exit 0 with nothing on stdout. Every hook has a timeout of 5 to 15 seconds. Memories are injected as data for the agent to weigh, never as instructions.

Opt out per repository with a `.brain-ignore` file in its root, or everywhere with `BRAIN_HOOKS=off`.

## Other clients

The installer (`brain setup`) also connects Codex, Cursor, VS Code Copilot, Devin, Gemini and OpenCode. Each one gets the same `brain mcp` server, a rules block in its instructions file and the hooks in its own format, so Brain is read and written in every session. `brain doctor` shows which agents have used Brain recently. See [Installation](https://github.com/cboxdk/cbox-brain/blob/main/docs/getting-started/installation.md).

## Keeping the CLI current

`plugins/cbox-brain/scripts/brain.mjs` is vendored from [`cboxdk/cbox-brain`](https://github.com/cboxdk/cbox-brain) `bin/brain.mjs`; the header line records the source commit. `scripts/sync-brain-cli.sh /path/to/cbox-brain` refreshes it and the plugin version. `python3 scripts/validate.py` checks the marketplace, the manifest, the hooks and the skill.

## Security

Credentials are stored with mode 600 and never printed. The CLI talks only to the Brain server it was signed in to. Report a vulnerability through GitHub's private vulnerability reporting on this repository.
