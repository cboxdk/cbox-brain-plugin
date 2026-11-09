#!/bin/bash
# Vendors cbox-brain's CLI into the plugin: copies bin/brain.mjs from a cbox-brain checkout
# to plugins/cbox-brain/scripts/brain.mjs and records the source commit in a header line, so
# the hooks work without a cbox-brain checkout and the copy is traceable. The copy is
# committed; run this after every CLI change in cbox-brain.
#
#   scripts/sync-brain-cli.sh [/path/to/cbox-brain]     # default: ../cbox-brain next to this repo, or $BRAIN_SRC
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd "$here/.." && pwd)"
src="${1:-${BRAIN_SRC:-$repo/../cbox-brain}}"
file="$src/bin/brain.mjs"
target="$repo/plugins/cbox-brain/scripts/brain.mjs"

if [ ! -f "$file" ]; then
    echo "sync-brain-cli: no $file; pass the cbox-brain checkout as the first argument" >&2
    exit 1
fi

commit="$(git -C "$src" rev-parse --short HEAD 2>/dev/null || echo unknown)"
dirty=""
git -C "$src" diff --quiet -- bin/brain.mjs 2>/dev/null || dirty=", with uncommitted changes"

{
    sed -n '1p' "$file"
    echo "// Vendored from cboxdk/cbox-brain bin/brain.mjs at commit $commit$dirty, $(date -u +%Y-%m-%d), by scripts/sync-brain-cli.sh. Do not edit here: change it in cbox-brain and run the sync again."
    sed -n '2,$p' "$file"
} > "$target"
chmod +x "$target"
node --check "$target"

version="$(grep -oE "const VERSION = '[^']+'" "$target" | head -1 | sed "s/.*'\(.*\)'/\1/")"
if [ -n "$version" ]; then
    python3 - "$repo/plugins/cbox-brain/.claude-plugin/plugin.json" "$version" <<'PY'
import json, sys
path, version = sys.argv[1], sys.argv[2]
manifest = json.load(open(path))
# The plugin may be a patch ahead of the CLI (skill-only changes); keep that unless the CLI moved.
if not str(manifest.get("version", "")).startswith(version + "."):
    manifest["version"] = version
json.dump(manifest, open(path, "w"), indent=2, ensure_ascii=False)
open(path, "a").write("\n")
PY
fi

echo "plugins/cbox-brain/scripts/brain.mjs ← $file @ $commit$dirty (CLI ${version:-?})"
