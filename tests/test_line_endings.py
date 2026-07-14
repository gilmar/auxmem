"""Regression: Windows/Git autocrlf must not break bootstrap.sh (issue #36)."""

from __future__ import annotations

from pathlib import Path

import pytest

from koinome.line_endings import ensure_lf_bytes, normalize_corpus_shell_scripts
from koinome.scaffold import ScaffoldError, scaffold
from tests.helpers import REPO_ROOT, run_koinome, scaffold_corpus
from tests.test_bootstrap import run_bootstrap

TEMPLATE_BOOTSTRAP = REPO_ROOT / "koinome" / "template" / "bootstrap.sh"


def test_template_bootstrap_has_unix_line_endings():
    raw = TEMPLATE_BOOTSTRAP.read_bytes()
    assert b"\r" not in raw, "template bootstrap.sh must be LF-only in the repo"


def test_template_gitattributes_forces_lf_for_shell():
    text = (REPO_ROOT / "koinome" / "template" / ".gitattributes").read_text(encoding="utf-8")
    assert "eol=lf" in text
    assert "*.sh" in text
    assert ".scripts/pre-commit" in text


def test_repo_gitattributes_forces_lf_for_shell():
    text = (REPO_ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert "*.sh text eol=lf" in text


def test_normalizes_all_template_shell_scripts(tmp_path):
    dest = tmp_path / "corpus"
    scaffold_corpus(dest, no_bootstrap=True)
    targets = [
        dest / "bootstrap.sh",
        dest / ".scripts" / "koinome-sync.sh",
        dest / ".scripts" / "pre-commit",
    ]
    for path in targets:
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        assert b"\r\n" in path.read_bytes()
    changed = normalize_corpus_shell_scripts(dest)
    assert set(changed) >= {"bootstrap.sh", ".scripts/koinome-sync.sh", ".scripts/pre-commit"}
    for path in targets:
        assert b"\r" not in path.read_bytes()


def test_normalizes_installed_git_hook(tmp_path):
    dest = tmp_path / "corpus"
    scaffold_corpus(dest)
    hook = dest / ".git" / "hooks" / "pre-commit"
    assert hook.is_file()
    hook.write_bytes(hook.read_bytes().replace(b"\n", b"\r\n"))
    changed = normalize_corpus_shell_scripts(dest)
    assert ".git/hooks/pre-commit" in changed
    assert b"\r" not in hook.read_bytes()


def test_upgrade_up_to_date_still_normalizes_shell_scripts(tmp_path):
    dest = tmp_path / "corpus"
    scaffold_corpus(dest)
    sync = dest / ".scripts" / "koinome-sync.sh"
    sync.write_bytes(sync.read_bytes().replace(b"\n", b"\r\n"))
    result = run_koinome(["upgrade", str(dest)])
    assert result.returncode == 0, result.stdout + result.stderr
    assert b"\r" not in sync.read_bytes()
    assert "normalized LF" in result.stdout or "already at template" in result.stdout


def test_bootstrap_installs_hook_without_cr(tmp_path):
    dest = tmp_path / "corpus"
    scaffold_corpus(dest, no_bootstrap=True)
    pre = dest / ".scripts" / "pre-commit"
    pre.write_bytes(pre.read_bytes().replace(b"\n", b"\r\n"))
    # Source stays CRLF; bootstrap must strip when installing the hook.
    result = run_bootstrap(dest)
    assert result.returncode == 0, result.stdout + result.stderr
    hook = dest / ".git" / "hooks" / "pre-commit"
    assert hook.is_file()
    assert b"\r" not in hook.read_bytes()


def test_template_shell_scripts_are_lf_only():
    root = REPO_ROOT / "koinome" / "template"
    offenders = []
    for path in [root / "bootstrap.sh", *sorted((root / ".scripts").glob("*.sh")), root / ".scripts" / "pre-commit"]:
        if b"\r" in path.read_bytes():
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert not offenders, f"CRLF in template scripts: {offenders}"



def test_normalized_crlf_bootstrap_runs(tmp_path):
    dest = tmp_path / "corpus"
    scaffold_corpus(dest, no_bootstrap=True)
    path = dest / "bootstrap.sh"
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    normalize_corpus_shell_scripts(dest)
    result = run_bootstrap(dest)
    assert result.returncode == 0, result.stdout + result.stderr


def test_scaffold_normalizes_crlf_copied_from_template(tmp_path, monkeypatch):
    """If the bundled template arrives with CRLF (Windows checkout), scaffold still works."""
    import shutil

    import koinome.scaffold as scaffold_mod

    real_copytree = shutil.copytree

    def copytree_inject_crlf(src, dst, *args, **kwargs):
        result = real_copytree(src, dst, *args, **kwargs)
        bootstrap = Path(dst) / "bootstrap.sh"
        # copytree recurses into subdirs; only rewrite the corpus-root bootstraps.
        if bootstrap.is_file():
            bootstrap.write_bytes(bootstrap.read_bytes().replace(b"\n", b"\r\n"))
            for script in (Path(dst) / ".scripts").glob("*.sh"):
                script.write_bytes(script.read_bytes().replace(b"\n", b"\r\n"))
            pre = Path(dst) / ".scripts" / "pre-commit"
            if pre.is_file():
                pre.write_bytes(pre.read_bytes().replace(b"\n", b"\r\n"))
        return result

    monkeypatch.setattr(scaffold_mod.shutil, "copytree", copytree_inject_crlf)
    dest = tmp_path / "corpus"
    try:
        result = scaffold(
            "win-test",
            dest,
            {"10-projects": "projects"},
            run_bootstrap=True,
        )
    except ScaffoldError as exc:
        pytest.fail(f"scaffold failed with CRLF-injected template: {exc}")
    assert result["bootstrapped"] is True
    assert b"\r" not in (dest / "bootstrap.sh").read_bytes()
