#!/usr/bin/env python3
"""JSON Schema validation for Koinome corpus format v0 (identity + record types)."""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CORPUS_ROOT = SCRIPT_DIR.parent
SCHEMAS_DIR = CORPUS_ROOT / ".schemas" / "v0"

V0_RECORD_TYPES = frozenset(
    {"decision", "claim", "state", "policy", "instruction", "source"}
)

ISO_DATETIME = re.compile(
    r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2}))?$"
)


def _schema_store() -> dict[str, dict]:
    store: dict[str, dict] = {}
    if not SCHEMAS_DIR.is_dir():
        return store
    for path in sorted(SCHEMAS_DIR.glob("*.json")):
        store[path.name] = json.loads(path.read_text(encoding="utf-8"))
    return store


def _validator_for(schema_name: str, store: dict[str, dict]):
    try:
        import jsonschema
        from jsonschema import Draft202012Validator
        from jsonschema.validators import validator_for
    except ImportError:
        return None

    schema = store.get(schema_name)
    if not schema:
        return None

    def resolve(ref: str):
        name = ref.split("/")[-1]
        if name in store:
            return store[name]
        if ref in store:
            return store[ref]
        return None

    registry_resources = []
    for name, doc in store.items():
        uri = doc.get("$id") or f"https://koinome.dev/schemas/v0/{name}"
        registry_resources.append((uri, doc))

    try:
        from referencing import Registry, Resource

        registry = Registry().with_resources(
            (uri, Resource.from_contents(doc)) for uri, doc in registry_resources
        )
        cls = validator_for(schema)
        return cls(schema, registry=registry)
    except Exception:
        # Fallback for older jsonschema without referencing registry
        resolver = jsonschema.RefResolver(
            base_uri="https://koinome.dev/schemas/v0/",
            referrer=schema,
            store={f"https://koinome.dev/schemas/v0/{k}": v for k, v in store.items()},
        )
        return Draft202012Validator(schema, resolver=resolver)


def validate_corpus_identity(doc: dict) -> list[str]:
    store = _schema_store()
    if not store:
        return []
    validator = _validator_for("corpus-identity.schema.json", store)
    if validator is None:
        return _fallback_identity(doc)
    errors: list[str] = []
    for err in sorted(validator.iter_errors(doc), key=lambda e: list(e.path)):
        loc = ".".join(str(p) for p in err.path) if err.path else "(root)"
        errors.append(f"{loc}: {err.message}")
    return errors


def _fallback_identity(doc: dict) -> list[str]:
    errors: list[str] = []
    if doc.get("format_version") != "0":
        errors.append("format_version must be '0'")
    return errors


ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _coerce_fm_for_json(fm: dict) -> dict:
    out: dict = {}
    for key, val in fm.items():
        if isinstance(val, date) and not isinstance(val, datetime):
            out[key] = val.isoformat()
        elif isinstance(val, datetime):
            out[key] = val.isoformat()
        else:
            out[key] = val
    return out


def validate_v0_frontmatter(fm: dict) -> list[str]:
    typ = fm.get("type")
    if typ not in V0_RECORD_TYPES:
        return []
    # Legacy intake notes kept type: source before origin/captured were required.
    if typ == "source" and "origin" not in fm and "captured" not in fm:
        return []
    store = _schema_store()
    schema_name = f"record-{typ}.schema.json"
    if schema_name not in store:
        return [f"no JSON Schema bundled for v0 type '{typ}'"]
    validator = _validator_for(schema_name, store)
    if validator is None:
        return []
    fm_json = _coerce_fm_for_json(fm)
    errors: list[str] = []
    for err in sorted(validator.iter_errors(fm_json), key=lambda e: list(e.path)):
        loc = ".".join(str(p) for p in err.path) if err.path else "(root)"
        errors.append(f"v0 schema {loc}: {err.message}")
    errors.extend(_check_prov_odrl(fm, typ))
    errors.extend(_check_v0_semantics(fm, typ))
    return errors


def _check_prov_odrl(fm: dict, typ: str) -> list[str]:
    errors: list[str] = []
    for key in ("prov:wasDerivedFrom", "odrl:permission", "odrl:prohibition", "odrl:duty"):
        if key not in fm:
            continue
        val = fm[key]
        if key == "prov:wasDerivedFrom":
            if not isinstance(val, list) or not all(isinstance(x, str) and x for x in val):
                errors.append(f"{key} must be a non-empty list of strings when present")
        elif key.startswith("odrl:"):
            if not isinstance(val, list):
                errors.append(f"{key} must be a list when present")
            else:
                for i, item in enumerate(val):
                    if not isinstance(item, dict):
                        errors.append(f"{key}[{i}] must be an object")
    gen = fm.get("prov:generatedAtTime")
    if gen is not None and isinstance(gen, str) and not ISO_DATETIME.match(gen.strip()):
        errors.append("prov:generatedAtTime must be ISO-8601 date or date-time")
    attr = fm.get("prov:wasAttributedTo")
    if attr is not None and not isinstance(attr, str):
        errors.append("prov:wasAttributedTo must be a string when present")
    return errors


def _check_v0_semantics(fm: dict, typ: str) -> list[str]:
    errors: list[str] = []
    status = fm.get("status")
    if status == "superseded":
        sup = fm.get("supersedes")
        if not sup or not isinstance(sup, str):
            errors.append("status superseded requires non-empty supersedes (successor record id or path)")
    if typ in ("decision", "claim"):
        derived = fm.get("prov:wasDerivedFrom")
        if not isinstance(derived, list) or not derived:
            errors.append(
                f"type '{typ}' requires prov:wasDerivedFrom with at least one source reference"
            )
    if typ == "source" and ("origin" in fm or "captured" in fm):
        origin = fm.get("origin")
        if not isinstance(origin, str) or not origin.strip():
            errors.append("type 'source' with v0 fields requires non-empty origin")
        captured = fm.get("captured")
        cap = captured.isoformat() if isinstance(captured, date) and not isinstance(captured, datetime) else captured
        if not isinstance(cap, str) or not ISO_DATE.match(cap.strip()):
            errors.append("type 'source' with v0 fields requires captured: YYYY-MM-DD")
    return errors


def load_corpus_identity_yaml(path: Path) -> tuple[dict | None, str | None]:
    import yaml

    if not path.is_file():
        return None, f"missing {path.name}"
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return None, f"invalid YAML in {path.name}: {exc}"
    if not isinstance(data, dict):
        return None, f"{path.name} must be a YAML mapping"
    return data, None
