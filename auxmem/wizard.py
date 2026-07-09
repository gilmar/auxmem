"""Interactive terminal wizard for `auxmem new`.

Stdlib only. Guided steps with plain-language context, a domain preset,
a creation preview, and live bootstrap progress. Falls back cleanly if stdin
is not a tty (raises so the CLI can tell the user to use flags instead).
"""

import json
import sys
from pathlib import Path

from . import scaffold

BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

DEFAULT_DOMAINS = {
    "10-projects": "projects",
    "20-governance": "governance",
    "30-ops": "ops",
}

STRUCTURAL_NOTES = {
    "00-inbox": "unsorted captures",
    "05-sources": "raw intake, synthesis queue",
    "60-decisions": "decision log (ADRs)",
    "70-meetings": "meeting notes",
    "71-log": "session logs",
    "72-tasks": "todo.txt task list",
    "80-moc": "generated maps of content",
    "85-synthesis": "derived pages with provenance",
    "90-templates": "note templates",
    "95-assets": "images and binaries",
    "99-archive": "stale content, do not search",
}


def _banner():
    print(f"{BOLD}auxmem{RESET} {DIM}create a governed memory vault for your AI agents{RESET}\n")
    print(
        "You are about to create a folder of plain markdown notes with a validator, "
        "a git hook, and agent skills. Your agents read and write it; nothing runs "
        "in the background.\n"
    )


def _step(n, total, title):
    print(f"{BOLD}Step {n}/{total}: {title}{RESET}")


def _ask(prompt, default=None, validate=None):
    suffix = f" [{default}]" if default is not None else ""
    while True:
        raw = input(f"{prompt}{suffix}: ").strip()
        if not raw and default is not None:
            raw = default
        if not raw:
            print("  required.")
            continue
        if validate:
            err = validate(raw)
            if err:
                print(f"  {err}")
                continue
        return raw


def _yesno(prompt, default=True):
    d = "Y/n" if default else "y/N"
    while True:
        raw = input(f"{prompt} [{d}]: ").strip().lower()
        if not raw:
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("  answer y or n.")


def _validate_name(v):
    if not scaffold.SLUG_RE.match(v):
        return "use lowercase letters, digits, and hyphens (e.g. my-work-vault)"
    return None


def _template_structural_folders():
    cfg_path = scaffold.TEMPLATE_DIR / ".scripts" / "vault.config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    return cfg.get("structural_folders", [])


def _collect_domains():
    print(
        f"{DIM}Domains are your subject-matter folders. Each note gets a domain slug "
        f"in its frontmatter so agents know where it belongs.{RESET}\n"
    )
    if _yesno("Use the starter set (projects, governance, ops)?", default=True):
        return dict(DEFAULT_DOMAINS)

    print(
        f"\n{DIM}Enter a short name per area (e.g. projects, governance). "
        "Folders are numbered automatically (10-projects, 20-governance, ...). "
        "For full control, type NN-folder=slug instead.{RESET}"
    )
    domains = {}
    while True:
        n = len(domains)
        raw = input(f"  area {n + 1} (blank to finish): ").strip()
        if not raw:
            if domains:
                break
            print("  at least one domain is required.")
            continue
        if "=" in raw:
            try:
                domains.update(scaffold.parse_domains([raw]))
            except scaffold.ScaffoldError as e:
                print(f"  {e}")
            continue
        if not scaffold.SLUG_RE.match(raw):
            print("  use lowercase letters, digits, and hyphens.")
            continue
        folder = f"{(n + 1) * 10}-{raw}"
        if folder in domains:
            print(f"  folder {folder} already added.")
            continue
        domains[folder] = raw
    return domains


def _show_preview(name, path, domains):
    print(f"\n{BOLD}This vault will contain:{RESET}\n")
    print(f"  {DIM}name{RESET}     {name}")
    print(f"  {DIM}path{RESET}     {path}")
    print(f"\n  {DIM}your domains{RESET}")
    for folder, slug in domains.items():
        print(f"    {folder}/  ({slug})")
    print(f"\n  {DIM}shared structure{RESET} (same in every vault)")
    for folder in _template_structural_folders():
        note = STRUCTURAL_NOTES.get(folder, "")
        suffix = f"  {DIM}{note}{RESET}" if note else ""
        print(f"    {folder}/{suffix}")
    print(f"\n  {DIM}tooling installed{RESET}")
    print("    git repo, validation hook, generated navigation")
    print("    agent skills linked for Claude Code, Codex, Gemini CLI, and Cursor")
    print("    AGENTS.md as the canonical guide for every agent\n")


def run():
    if not sys.stdin.isatty():
        raise scaffold.ScaffoldError(
            "no interactive terminal; use flags: auxmem new --name NAME --path PATH --domain NN-folder=slug ..."
        )

    _banner()
    total = 4

    _step(1, total, "Name your vault")
    print(
        f"{DIM}Used as the vault label, git repo name, and in config. "
        "Lowercase and hyphens only.{RESET}\n"
    )
    name = _ask("Vault name", default="my-vault", validate=_validate_name)

    _step(2, total, "Choose a location")
    print(f"{DIM}Must be empty or not exist yet.{RESET}\n")
    default_path = str(Path.home() / name)
    path = _ask("Path", default=default_path)

    _step(3, total, "Pick your domains")
    print()
    domains = _collect_domains()

    _step(4, total, "Review and create")
    _show_preview(name, path, domains)
    if not _yesno("Create this vault?", default=True):
        print("cancelled.")
        return None

    print(f"\n{BOLD}Creating vault...{RESET}\n")
    result = scaffold.scaffold(
        name, path, domains, run_bootstrap=True, stream_bootstrap=True
    )

    dest = result["dest"]
    print(f"\n{BOLD}Vault ready at {dest}{RESET}\n")
    print("Next steps:")
    print(f"  1. cd {dest}")
    print("  2. Point your agent at this folder (claude, codex, or gemini)")
    print("     It reads AGENTS.md automatically.")
    print("  3. Optional: set a private git remote and push")
    print("     git remote add origin <url>")
    print("     git add -A && git commit -m 'initial vault' && git push -u origin main")
    print("  4. Optional: seed from AI exports or import Obsidian (see docs/IMPORTING.md)")
    print(f"     auxmem seed <export.json> --staging ./seed-staging")
    print(f"     auxmem import-obsidian <old-vault> --dest {dest} --map map.json")
    return result
