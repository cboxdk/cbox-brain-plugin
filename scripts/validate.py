#!/usr/bin/env python3
"""Validate the marketplace catalog, plugin manifests, hooks, and every SKILL.md.

Exits non-zero if anything looks wrong. Uses stdlib only — no pip install needed in CI.
"""

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


# 1. marketplace.json
marketplace_path = ROOT / ".claude-plugin" / "marketplace.json"
marketplace = None
if not marketplace_path.exists():
    err(f"{rel(marketplace_path)}: file not found")
else:
    try:
        marketplace = json.loads(marketplace_path.read_text())
    except json.JSONDecodeError as e:
        err(f"{rel(marketplace_path)}: invalid JSON — {e}")

if marketplace:
    for field in ("name", "owner", "plugins"):
        if field not in marketplace:
            err(f"marketplace.json: missing required field '{field}'")
    if "owner" in marketplace and "name" not in marketplace["owner"]:
        err("marketplace.json: owner.name is required")

# 2. Each plugin entry
for plugin in (marketplace or {}).get("plugins", []):
    if "name" not in plugin:
        err("marketplace.json: a plugin entry is missing 'name'")
        continue
    pname = plugin["name"]
    if "source" not in plugin:
        err(f"marketplace.json: plugin '{pname}' missing 'source'")
        continue
    if not isinstance(plugin["source"], str):
        continue  # only validate local-path sources

    plugin_root = (ROOT / plugin["source"]).resolve()
    plugin_json = plugin_root / ".claude-plugin" / "plugin.json"
    if not plugin_json.exists():
        err(f"{pname}: missing plugin.json at {rel(plugin_json)}")
        continue

    try:
        manifest = json.loads(plugin_json.read_text())
    except json.JSONDecodeError as e:
        err(f"{rel(plugin_json)}: invalid JSON — {e}")
        continue

    if "name" not in manifest:
        err(f"{rel(plugin_json)}: missing required field 'name'")

    # 3. Hooks: valid JSON, and every referenced script exists and is executable
    hooks_json = plugin_root / "hooks" / "hooks.json"
    if hooks_json.exists():
        try:
            hooks = json.loads(hooks_json.read_text())
        except json.JSONDecodeError as e:
            err(f"{rel(hooks_json)}: invalid JSON — {e}")
            hooks = {}
        for event, entries in (hooks.get("hooks") or {}).items():
            for entry in entries:
                for hook in entry.get("hooks", []):
                    cmd = hook.get("command", "")
                    m = re.search(r"\$\{CLAUDE_PLUGIN_ROOT\}\"?(/[^\s\"']+)", cmd)
                    if not m:
                        continue
                    script = plugin_root / m.group(1).lstrip("/")
                    if not script.exists():
                        err(f"{rel(hooks_json)}: hook script not found: {m.group(1)}")
                    elif not os.access(script, os.X_OK):
                        err(f"{rel(script)}: hook script is not executable (chmod +x)")

    # 4. Each skill inside the plugin
    skills_dir = plugin_root / "skills"
    if not skills_dir.exists():
        continue

    for skill_dir in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            err(f"{rel(skill_dir)}: missing SKILL.md")
            continue

        content = skill_md.read_text()
        fm_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        if not fm_match:
            err(f"{rel(skill_md)}: missing YAML frontmatter")
            continue

        frontmatter = fm_match.group(1)
        name_m = re.search(r"^name:\s*(.+?)\s*$", frontmatter, re.MULTILINE)
        desc_m = re.search(r"^description:\s*(.+?)\s*$", frontmatter, re.MULTILINE)

        if not name_m:
            err(f"{rel(skill_md)}: frontmatter missing 'name'")
        elif name_m.group(1) != skill_dir.name:
            err(
                f"{rel(skill_md)}: frontmatter name '{name_m.group(1)}' "
                f"doesn't match directory '{skill_dir.name}'"
            )

        if not desc_m:
            err(f"{rel(skill_md)}: frontmatter missing 'description'")

        # Referenced files (anything in backticks starting with references/)
        for ref_m in re.finditer(r"`(references/[^`]+)`", content):
            ref_path = skill_dir / ref_m.group(1)
            if not ref_path.exists():
                err(f"{rel(skill_md)}: referenced file not found: {ref_m.group(1)}")

# 5. No legacy .skill zip bundles
for skill_zip in ROOT.rglob("*.skill"):
    if ".git" in skill_zip.parts:
        continue
    err(f"{rel(skill_zip)}: .skill zip bundles are not allowed — use the plugin structure")

# Report
if errors:
    print("Validation failed:", file=sys.stderr)
    for e in errors:
        print(f"  ✗ {e}", file=sys.stderr)
    sys.exit(1)

print("All validation checks passed.")
