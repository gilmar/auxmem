"""Normalize line endings for scripts that bash must execute."""

from __future__ import annotations

from pathlib import Path

# Relative paths always considered bash entrypoints (even without .sh suffix).
NAMED_BASH_SCRIPTS = frozenset(
    {
        "bootstrap.sh",
        ".scripts/pre-commit",
        ".git/hooks/pre-commit",
    }
)

_SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        ".koinome",
        "99-archive",
        "node_modules",
        ".venv",
        "venv",
    }
)


def ensure_lf_bytes(data: bytes) -> bytes:
    """Convert CRLF/CR to LF without rewriting already-LF content."""
    if b"\r" not in data:
        return data
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def is_bash_script(path: Path, *, corpus_root: Path | None = None) -> bool:
    name = path.name
    if name.endswith(".sh") or name == "bootstrap.sh":
        return True
    if name == "pre-commit":
        return True
    if corpus_root is not None:
        try:
            rel = path.resolve().relative_to(corpus_root.resolve()).as_posix()
        except ValueError:
            return False
        return rel in NAMED_BASH_SCRIPTS
    return False


def normalize_script_file(path: Path) -> bool:
    """Rewrite bash scripts with LF endings if needed. Returns True when bytes changed."""
    if not path.is_file() or not is_bash_script(path):
        return False
    raw = path.read_bytes()
    fixed = ensure_lf_bytes(raw)
    if fixed == raw:
        return False
    path.write_bytes(fixed)
    return True


def _iter_bash_script_paths(corpus_root: Path) -> list[Path]:
    root = Path(corpus_root)
    found: list[Path] = []
    seen: set[Path] = set()

    def add(path: Path) -> None:
        try:
            resolved = path.resolve()
        except OSError:
            return
        if resolved in seen or not path.is_file():
            return
        seen.add(resolved)
        found.append(path)

    for named in (
        root / "bootstrap.sh",
        root / ".scripts" / "pre-commit",
        root / ".git" / "hooks" / "pre-commit",
    ):
        add(named)

    for path in sorted(root.rglob("*.sh")):
        if any(part in _SKIP_DIR_NAMES for part in path.relative_to(root).parts):
            continue
        add(path)

    return found


def normalize_corpus_shell_scripts(corpus_root: Path) -> list[str]:
    """Ensure every bash-executed corpus script uses LF. Returns changed rel paths."""
    root = Path(corpus_root)
    changed: list[str] = []
    for path in _iter_bash_script_paths(root):
        if normalize_script_file(path):
            changed.append(str(path.relative_to(root)).replace("\\", "/"))
    return changed
