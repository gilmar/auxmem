"""Optional v0 record-type migration during template upgrade."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml

TYPE_MIGRATION: dict[str, str] = {
    "adr": "decision",
    "concept": "claim",
    "entity": "state",
    "governance-finding": "claim",
    # source stays source
}

FM_DELIM = re.compile(r"^---\s*$", re.M)


@dataclass
class MigrationResult:
    changed: list[tuple[str, str, str]]  # path, old_type, new_type
    skipped: list[str]


def _split_frontmatter(text: str) -> tuple[dict | None, str, str | None]:
    if not text.startswith("---"):
        return None, text, "missing frontmatter"
    parts = FM_DELIM.split(text, maxsplit=2)
    if len(parts) < 3:
        return None, text, "unterminated frontmatter"
    fm = yaml.safe_load(parts[1])
    if not isinstance(fm, dict):
        return None, text, "frontmatter not a mapping"
    body = parts[2]
    return fm, body, None


def _dump_frontmatter(fm: dict) -> str:
    return yaml.dump(
        fm, sort_keys=False, allow_unicode=True, default_flow_style=False, width=1000
    ).rstrip()


def migrate_record_types(corpus_root: Path, *, dry_run: bool = False) -> MigrationResult:
    """Rewrite legacy template types to v0 canonical types where mapped."""
    config_path = corpus_root / ".scripts" / "koinome.config.json"
    skip_dirs = {".git", ".scripts", ".koinome", ".skills", "90-templates", "99-archive"}
    if config_path.is_file():
        import json

        try:
            cfg = json.loads(config_path.read_text(encoding="utf-8"))
            skip_dirs = set(cfg.get("skip_dirs", list(skip_dirs)))
        except json.JSONDecodeError:
            pass

    changed: list[tuple[str, str, str]] = []
    skipped: list[str] = []

    for path in sorted(corpus_root.rglob("*.md")):
        rel = path.relative_to(corpus_root)
        if rel.parts and rel.parts[0] in skip_dirs:
            continue
        if len(rel.parts) == 1 and rel.name in {"AGENTS.md", "CLAUDE.md", "GEMINI.md", "README.md"}:
            continue
        text = path.read_text(encoding="utf-8")
        fm, body, err = _split_frontmatter(text)
        if err or fm is None:
            skipped.append(f"{rel}: {err}")
            continue
        old = fm.get("type")
        if not isinstance(old, str):
            continue
        new = TYPE_MIGRATION.get(old)
        if not new or new == old:
            continue
        if not dry_run:
            fm["type"] = new
            path.write_text(f"---\n{_dump_frontmatter(fm)}\n---{body}", encoding="utf-8")
        changed.append((str(rel), old, new))

    return MigrationResult(changed=changed, skipped=skipped)


def write_migration_report(corpus_root: Path, result: MigrationResult) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out = corpus_root / "00-inbox" / f"record-type-migration-{ts}.md"
    lines = [
        "---",
        "title: Record type migration report",
        "summary: Optional upgrade pass mapping legacy note types to v0 canonical record types.",
        "type: log",
        "status: active",
        "domain: general",
        "created: " + datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "updated: " + datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "---",
        "",
        "## Migrated",
        "",
    ]
    if result.changed:
        for rel, old, new in result.changed:
            lines.append(f"- `{rel}`: `{old}` → `{new}`")
    else:
        lines.append("- (none)")
    lines += ["", "## Skipped", ""]
    if result.skipped:
        lines.extend(f"- {s}" for s in result.skipped[:50])
        if len(result.skipped) > 50:
            lines.append(f"- … and {len(result.skipped) - 50} more")
    else:
        lines.append("- (none)")
    lines.append("")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out
