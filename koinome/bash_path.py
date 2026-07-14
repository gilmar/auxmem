"""Resolve a usable bash executable (prefer Git Bash on Windows)."""

from __future__ import annotations

import os
import shutil
from functools import lru_cache


def _looks_like_wsl_bash(path: str) -> bool:
    lowered = path.replace("/", "\\").lower()
    return (
        "\\system32\\bash.exe" in lowered
        or "\\system32\\wsl.exe" in lowered
        or lowered.endswith("\\wsl.exe")
        or "\\windowsapps\\" in lowered
    )


def _git_bash_candidates() -> list[str]:
    candidates: list[str] = []
    env = os.environ.get("KOINOME_BASH") or os.environ.get("BASH")
    if env:
        candidates.append(env)
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    local_app = os.environ.get("LOCALAPPDATA", "")
    for root in (program_files, program_files_x86):
        candidates.append(os.path.join(root, "Git", "bin", "bash.exe"))
        candidates.append(os.path.join(root, "Git", "usr", "bin", "bash.exe"))
    if local_app:
        candidates.append(os.path.join(local_app, "Programs", "Git", "bin", "bash.exe"))
    which = shutil.which("bash")
    if which:
        candidates.append(which)
    return candidates


@lru_cache(maxsize=1)
def resolve_bash() -> str:
    """Return bash path suitable for running corpus bootstrap.sh.

    On Windows, prefer Git for Windows and skip the WSL ``bash.exe`` shim, which
    fails on runners (and some desktops) with no WSL distro installed.
    """
    if os.name != "nt":
        return shutil.which("bash") or "bash"

    for candidate in _git_bash_candidates():
        if not candidate or _looks_like_wsl_bash(candidate):
            continue
        if os.path.isfile(candidate):
            return candidate
    # Last resort: whatever PATH finds (may still be WSL).
    return shutil.which("bash") or "bash"
