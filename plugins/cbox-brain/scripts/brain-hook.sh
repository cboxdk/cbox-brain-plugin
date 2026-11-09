#!/bin/bash
# Claude Code hook → Cbox Brain. One line of work: hand Claude Code's hook JSON
# (stdin) to `brain hook <event>` and let the CLI answer (stdout). The CLI does
# the thinking: session-start injects the project's context, prompt injects what
# changed in Brain since the last turn, pre-tool gates deploy-shaped Bash
# commands against the team's policies, stop reminds once to remember.
#
# Which CLI, in order: $BRAIN_CLI (a path), `brain` on PATH, the copy vendored
# next to this script (scripts/brain.mjs, kept current by scripts/sync-brain-cli.sh).
#
# Never fails the session: no node, no CLI, no network, not signed in,
# BRAIN_HOOKS=off or a .brain-ignore file in the repo → exit 0 with nothing on
# stdout. The CLI exits 0 on every hook path itself; this wrapper only guards
# what runs before it. Hook contract (stdin JSON, hookSpecificOutput on stdout,
# exit 0 = proceed): https://code.claude.com/docs/en/hooks, "Hook input and output".
set -uo pipefail

event="${1:-}"
[ -n "$event" ] || exit 0
[ "${BRAIN_HOOKS:-}" != "off" ] || exit 0

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)" || exit 0
root="${CLAUDE_PLUGIN_ROOT:-$here/..}"

if [ -n "${BRAIN_CLI:-}" ] && [ -e "$BRAIN_CLI" ]; then
    case "$BRAIN_CLI" in
        *.mjs|*.js) command -v node >/dev/null 2>&1 || exit 0; node "$BRAIN_CLI" hook "$event" || exit 0 ;;
        *) "$BRAIN_CLI" hook "$event" || exit 0 ;;
    esac
elif command -v brain >/dev/null 2>&1; then
    brain hook "$event" || exit 0
elif [ -f "$root/scripts/brain.mjs" ]; then
    command -v node >/dev/null 2>&1 || exit 0
    node "$root/scripts/brain.mjs" hook "$event" || exit 0
fi

exit 0
