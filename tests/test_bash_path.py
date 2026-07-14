"""Tests for Windows-safe bash resolution."""

from __future__ import annotations

from pathlib import Path

from koinome.bash_path import _looks_like_wsl_bash, resolve_bash


def test_resolve_bash_returns_something():
    path = resolve_bash()
    assert path
    assert "bash" in Path(path).name.lower() or path == "bash"


def test_wsl_bash_shim_is_detected():
    assert _looks_like_wsl_bash(r"C:\Windows\System32\bash.exe")
    assert _looks_like_wsl_bash(r"C:\Windows\System32\wsl.exe")
    assert _looks_like_wsl_bash(r"C:\Program Files\WindowsApps\MicrosoftCorporation...\\bash.exe")
    assert not _looks_like_wsl_bash(r"C:\Program Files\Git\bin\bash.exe")
    assert not _looks_like_wsl_bash("/usr/bin/bash")


def test_koinome_bash_env_overrides_on_windows(monkeypatch, tmp_path):
    fake = tmp_path / "bash.exe"
    fake.write_bytes(b"")
    monkeypatch.setenv("KOINOME_BASH", str(fake))
    monkeypatch.setattr("koinome.bash_path.os.name", "nt")
    resolve_bash.cache_clear()
    try:
        assert resolve_bash() == str(fake)
    finally:
        resolve_bash.cache_clear()
