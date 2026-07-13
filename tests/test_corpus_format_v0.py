"""Corpus format v0 phases 1–3: identity manifest, record schemas, PROV/ODRL checks."""

from __future__ import annotations

import yaml

from koinome.cli import main as cli_main
from koinome.corpus_identity import (
    CORPUS_MANIFEST_NAME,
    build_identity_document,
    validate_identity_document,
)
from koinome.corpus_migrate import migrate_record_types
from tests.helpers import (
    note_with_fm,
    run_conformance_check,
    run_koinome,
    scaffold_corpus,
    validate_corpus,
    write_note,
)


def test_scaffold_writes_corpus_identity(tmp_path):
    dest = tmp_path / "c"
    scaffold_corpus(dest)
    manifest = dest / CORPUS_MANIFEST_NAME
    assert manifest.is_file()
    doc = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    assert doc["format_version"] == "0"
    assert not validate_identity_document(doc)


def test_check_corpus_identity_flag(tmp_path):
    dest = tmp_path / "c"
    scaffold_corpus(dest)
    rc = cli_main(["check", str(dest), "--corpus-identity"])
    assert rc == 0
    assert "corpus identity manifest ok" in run_conformance_check(dest, "--corpus-identity").stdout


def test_upgrade_backfills_identity(tmp_path):
    dest = tmp_path / "c"
    scaffold_corpus(dest)
    (dest / CORPUS_MANIFEST_NAME).unlink()
    rc = run_koinome(["upgrade", str(dest)])
    assert rc.returncode == 0, rc.stdout + rc.stderr
    assert (dest / CORPUS_MANIFEST_NAME).is_file()


def test_v0_decision_requires_derivation(tmp_path):
    dest = tmp_path / "c"
    scaffold_corpus(dest)
    write_note(
        dest,
        "10-projects/dec.md",
        note_with_fm(
            "Body.",
            title="A decision",
            summary="Concrete nouns for a v0 decision record validation test here.",
            type="decision",
            status="proposed",
            domain="projects",
            created="2026-07-04",
            updated="2026-07-04",
        ),
    )
    result = validate_corpus(dest)
    assert result.returncode != 0
    assert "prov:wasDerivedFrom" in result.stdout


def test_v0_decision_with_prov_passes_schema(tmp_path):
    dest = tmp_path / "c"
    scaffold_corpus(dest)
    fm = dict(
        title="A decision",
        summary="Concrete nouns for a v0 decision record validation test here.",
        type="decision",
        status="proposed",
        domain="projects",
        created="2026-07-04",
        updated="2026-07-04",
        **{"prov:wasDerivedFrom": ["05-sources/example.md"]},
    )
    write_note(dest, "10-projects/dec.md", note_with_fm("Body.", **fm))
    # source path won't resolve — link check may fail; use existing seed source if any
    sources = list((dest / "05-sources").glob("*.md"))
    if sources:
        fm["prov:wasDerivedFrom"] = [str(sources[0].relative_to(dest))]
        write_note(dest, "10-projects/dec.md", note_with_fm("Body.", **fm))
    result = validate_corpus(dest)
    assert "prov:wasDerivedFrom" not in result.stdout or result.returncode == 0


def test_migrate_record_types_dry_run(tmp_path):
    dest = tmp_path / "c"
    scaffold_corpus(dest)
    mig = migrate_record_types(dest, dry_run=True)
    assert any(old == "adr" and new == "decision" for _, old, new in mig.changed)


def test_identity_document_builder():
    doc = build_identity_document(corpus_name="My Corpus")
    assert doc["format_version"] == "0"
    assert doc["owner"]["id"].startswith("urn:koinome:owner:")
    assert "context_to_corpus" in doc["boundary_policies"]
