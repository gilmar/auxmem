# Corpus format v0 — phased proposal

**Status:** Proposal (RFC-first per strategy D10). **No implementation** in this document—only a map from [strategy §8](STRATEGY.md) and [§11 roadmap](STRATEGY.md) onto the current codebase.

## Context

Today's shipped corpus is a versioned **template** (`.koinome/manifest.json` + `.koinome-manifest.json` in the package) tracking **managed file upgrade state**, not **corpus identity**. Notes use ten templates under `koinome/template/90-templates/`. Validation is deterministic in `koinome/template/.scripts/validate_corpus.py`. Cross-corpus operations are design scope only.

v0 adds the smallest set of primitives required for sharing at the boundary between agent context and canonical corpus: identity, record types, provenance, inert policy fields, MCP proposal flow, and a recorded demo.

## Phase 1 — Corpus identity manifest (months 0–1)

### Problem

- `.koinome/manifest.json` (see `koinome/manifest.py`) records template version and managed-file hashes for `koinome upgrade`. It is **not** a durable corpus identity or policy document.
- Strategy requires: corpus ID independent of path/git remote, explicit owner vs steward, per-direction boundary policies stored **inert** until operations ship.

### Proposal

1. **RFC:** Name and schema for a **corpus identity manifest** at the corpus root (candidate: `corpus.manifest.yaml` or `koinome.corpus.yaml`—to be decided in RFC, not here).
2. **Fields (minimum):** `corpus_id` (UUID or URI), `created_at`, `owner` / `steward` (PROV-aligned agents), `boundary_policies` (per direction, ODRL-shaped, inert).
3. **CLI:** `koinome init` writes identity manifest; `koinome new` remains accepted alias until semantics diverge.
4. **Upgrade:** `koinome upgrade` backfills identity manifest for existing corpora with generated ID and default policies.
5. **Check:** `koinome check --manifest` (or dedicated flag) validates identity schema without conflating template manifest.

### Naming collision resolution

| Artifact | Purpose | Location |
| --- | --- | --- |
| Template / tooling manifest | Managed files for upgrade | `.koinome/manifest.json` (unchanged role; rename in docs only if needed) |
| Corpus identity manifest | Durable ID, ownership, policies | **New file at corpus root** (RFC) |

## Phase 2 — Six record types + JSON Schemas

### Target types (strategy §8)

`decision`, `claim`, `state`, `policy`, `instruction`, `source`.

### Mapping from current templates (`koinome/template/90-templates/`)

| Current template | Proposed v0 type | Notes |
| --- | --- | --- |
| `adr.md` | `decision` | ADR becomes decision records |
| `source.md` | `source` | Direct |
| `concept.md`, `entity.md` | `claim` / `state` | RFC splits vocabulary; migration table in upgrade |
| `governance-finding.md` | `claim` or `state` | RFC |
| `project-doc.md`, `meeting.md`, `1on1.md`, `weekly-review.md`, `stakeholder.md` | Legacy individual-use templates | **Kept** for shipped value; not v0 canonical types |

### Proposal

1. **RFC:** JSON Schema per record type; frontmatter `type` enum narrowed for v0 corpora.
2. **Templates:** Six minimal templates replace or sit beside legacy set; `koinome.config.json` vocabulary updated.
3. **`koinome upgrade`:** Optional migration pass (ADR → decision, etc.) with report in `00-inbox/`.
4. **Validator:** Schema validation hook in `validate_corpus.py`.

## Phase 3 — PROV frontmatter + inert ODRL

1. **RFC:** PROV-O mapped YAML keys (`wasDerivedFrom`, `wasAttributedTo`, `generatedAtTime`, etc.).
2. **Inert ODRL:** Policy fields on records and corpus manifest; validator checks shape only until enforcement ships.
3. **Validator extensions:** Missing sources, supersession without successor, scope violations (extend existing checks).

## Phase 4 — MCP server (months 1–4)

1. **Resources:** Scoped context bundles (domain, record types, sensitivity flags).
2. **Tools:** Proposal flow (create/update record proposals, not direct canonical writes).
3. **Acceptance:** Second agent client in strategy demo mounts same corpus.

Implementation location: new package module (e.g. `koinome/mcp/`) behind optional extra dependency group.

## Phase 5 — Example corpus + 90-second demo

1. Refresh `examples/` or add `examples/v0-demo/` aligned with six types and identity manifest.
2. Record demo script matching [strategy §8 demo](STRATEGY.md): init → MCP context → blocked proposal → revised approval → second client.
3. Deterministic evaluation extends `koinome.evaluation` when fixtures exist.

## Legacy surface (explicit stance)

**Keep and maintain** for individual-use value, documented honestly:

- Provider importers and `koinome seed` (`koinome/importers/`)
- MOC generation (`gen_mocs.py`)
- Synthesis skills and staleness lint (`koinome-synthesize`, `synthesis_status.py`)
- Git sync (`koinome_sync.py`, quarantine flow)

New investment prioritises the five v0 items above. Legacy features are not the strategy v0 **surface**, but they remain supported tooling until superseded by RFCs.

## RFC order (suggested)

1. Corpus identity manifest file name and schema.
2. Record type schemas and template migration.
3. PROV/ODRL frontmatter profile.
4. MCP resource and tool contracts.
5. Demo corpus acceptance criteria.

Each RFC should state **shipped vs design** per strategy §7.11 and land with tests in `tests/` and `koinome.evaluation` where deterministic.

## Out of scope for v0 (reminder)

Cross-corpus share/merge/federate execution, accounts, telemetry, embeddings database, autonomous overnight enrichment.
