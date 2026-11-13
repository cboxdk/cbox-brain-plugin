# Changelog

Versions follow the vendored Brain CLI (`plugins/cbox-brain/scripts/brain.mjs`). Earlier versions (0.4.0 to 0.8.0) were not tagged; their commits carry the version in the subject.

## 0.10.0 — 2026-11-13

First tagged release.

- **Retries are recorded once.** `brain remember` and `brain mcp` send a `client_key` with every `brain_remember`. A keyed write is sent again after a dropped connection or a 502, 503 or 504, and the same write in the same session answers the memory written the first time (`replayed`) instead of a duplicate.
- **One install** (CLI 0.9.0, synced here for the first time): `brain setup` wires Claude Code, Codex, Cursor, VS Code Copilot, Devin, Gemini and OpenCode (MCP through `brain mcp`, a rules block, hooks in each agent's format). `brain doctor` shows which agents have used Brain. `brain update` replaces the CLI with the server's copy, checked against its sha256.
- **Hooks:** fixed a race in which two concurrent hooks could both take over a stale dedupe claim and inject the same context twice.
- **README:** leads with the installer (`curl -fsSL https://app.cboxbrain.com/install | sh`). The MCP server is now connected through `brain mcp` (one sign-in, the repository picks the organization). Requires Node 22.
