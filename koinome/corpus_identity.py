"""Corpus identity manifest (format v0): durable ID, ownership, inert boundary policies."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

CORPUS_MANIFEST_NAME = "koinome.corpus.yaml"
FORMAT_VERSION = "0"

_PKG_ROOT = Path(__file__).resolve().parent
SCHEMAS_DIR = _PKG_ROOT / "schemas" / "v0"
CORPUS_SCHEMA_PATH = SCHEMAS_DIR / "corpus-identity.schema.json"


class CorpusIdentityError(Exception):
    pass


def corpus_manifest_path(corpus_root: Path) -> Path:
    return Path(corpus_root) / CORPUS_MANIFEST_NAME


def default_boundary_policies() -> dict[str, Any]:
    return {
        "context_to_corpus": {
            "permission": [{"action": "propose", "assignee": "agent"}],
            "prohibition": [],
            "duty": [],
        },
        "corpus_to_context": {
            "permission": [{"action": "read", "assignee": "agent"}],
            "prohibition": [],
            "duty": [],
        },
    }


def default_agents(*, label_prefix: str = "local") -> tuple[dict[str, str], dict[str, str]]:
    owner = {"id": f"urn:koinome:owner:{label_prefix}", "label": "Corpus owner"}
    steward = {"id": f"urn:koinome:steward:{label_prefix}", "label": "Corpus steward"}
    return owner, steward


def build_identity_document(
    *,
    corpus_name: str,
    corpus_id: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Build a new identity manifest mapping (not yet YAML-serialized)."""
    slug = "".join(c if c.isalnum() else "-" for c in corpus_name.lower()).strip("-") or "local"
    owner, steward = default_agents(label_prefix=slug)
    when = created_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return {
        "format_version": FORMAT_VERSION,
        "corpus_id": corpus_id or str(uuid.uuid4()),
        "created_at": when,
        "owner": owner,
        "steward": steward,
        "boundary_policies": default_boundary_policies(),
    }


def dump_identity_yaml(doc: dict[str, Any]) -> str:
    return (
        yaml.dump(
            doc,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
            width=1000,
        ).rstrip()
        + "\n"
    )


def write_identity_manifest(corpus_root: Path, *, corpus_name: str) -> Path:
    path = corpus_manifest_path(corpus_root)
    if path.is_file():
        return path
    doc = build_identity_document(corpus_name=corpus_name)
    path.write_text(dump_identity_yaml(doc), encoding="utf-8")
    return path


def load_identity_manifest(corpus_root: Path) -> dict[str, Any]:
    path = corpus_manifest_path(corpus_root)
    if not path.is_file():
        raise CorpusIdentityError(f"missing corpus identity manifest: {CORPUS_MANIFEST_NAME}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise CorpusIdentityError(f"{CORPUS_MANIFEST_NAME} is not valid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise CorpusIdentityError(f"{CORPUS_MANIFEST_NAME} must be a YAML mapping")
    return data


def _load_corpus_schema() -> dict[str, Any]:
    import json

    if not CORPUS_SCHEMA_PATH.is_file():
        raise CorpusIdentityError(f"bundled schema missing: {CORPUS_SCHEMA_PATH}")
    return json.loads(CORPUS_SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_identity_document(doc: dict[str, Any]) -> list[str]:
    """Return human-readable errors; empty list means valid."""
    try:
        import jsonschema
    except ImportError:
        return _validate_identity_fallback(doc)

    schema = _load_corpus_schema()
    validator = jsonschema.Draft202012Validator(schema)
    errors: list[str] = []
    for err in sorted(validator.iter_errors(doc), key=lambda e: list(e.path)):
        loc = ".".join(str(p) for p in err.path) if err.path else "(root)"
        errors.append(f"{loc}: {err.message}")
    return errors


def _validate_identity_fallback(doc: dict[str, Any]) -> list[str]:
    """Minimal checks when jsonschema is not installed (e.g. CI with only PyYAML)."""
    errors: list[str] = []
    if doc.get("format_version") != FORMAT_VERSION:
        errors.append("format_version must be '0'")
    cid = doc.get("corpus_id")
    if not isinstance(cid, str) or not cid.strip():
        errors.append("corpus_id must be a non-empty string")
    elif not _looks_like_uuid(cid):
        errors.append("corpus_id must be a UUID string")
    if not isinstance(doc.get("created_at"), str) or not doc.get("created_at"):
        errors.append("created_at must be an ISO-8601 timestamp string")
    for role in ("owner", "steward"):
        agent = doc.get(role)
        if not isinstance(agent, dict) or not isinstance(agent.get("id"), str) or not agent["id"]:
            errors.append(f"{role} must be an object with non-empty id")
    policies = doc.get("boundary_policies")
    if not isinstance(policies, dict):
        errors.append("boundary_policies must be a mapping")
    else:
        for direction in ("context_to_corpus", "corpus_to_context"):
            if direction not in policies:
                errors.append(f"boundary_policies missing {direction}")
    return errors


def _looks_like_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


def validate_identity_file(corpus_root: Path) -> list[str]:
    try:
        doc = load_identity_manifest(corpus_root)
    except CorpusIdentityError as exc:
        return [str(exc)]
    return validate_identity_document(doc)


def ensure_identity_manifest(corpus_root: Path, *, corpus_name: str | None = None) -> tuple[Path, bool]:
    """Create identity manifest if missing. Returns (path, created)."""
    path = corpus_manifest_path(corpus_root)
    if path.is_file():
        return path, False
    name = corpus_name or "corpus"
    if corpus_name is None:
        cfg = corpus_root / ".scripts" / "koinome.config.json"
        if cfg.is_file():
            import json

            try:
                name = json.loads(cfg.read_text(encoding="utf-8")).get("name") or name
            except json.JSONDecodeError:
                pass
    write_identity_manifest(corpus_root, corpus_name=name)
    return path, True
