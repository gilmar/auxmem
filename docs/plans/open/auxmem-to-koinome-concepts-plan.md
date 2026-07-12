# Align the Koinome repo with docs/STRATEGY.md

## Context

The AuxMem → Koinome transform is done, and `docs/STRATEGY.md` (new, untracked) now publishes the project strategy. The repo was transformed under an older internal plan (`docs/plans/open/koinome-transform-plan.md`) whose rules the strategy now supersedes in three places: it preserved MIT ("unless the user makes a separate licensing decision" — strategy D6 makes it: Apache-2.0 + DCO, no CLA), it forbade publishing the strategy (now public by design), and it framed a future commercial edition (strategy §14 rejects that framing). The README also still uses the narrow, individual-only corpus definition and never states the sharing thesis, the commitments, or the single-principal claim.

Decisions confirmed with the user:
- **Switch licence to Apache-2.0 now** (sole-author window; add DCO via CONTRIBUTING).
- **Scope: docs + governance + cheap code alignments** (`koinome init` alias, CLI help, pyproject description). Corpus-format v0 work is proposed in writing, not implemented.
- **Legacy surface (importers, MOCs, synthesis, sync): keep, reposition honestly.**
- **COMPARISONS.md: rewrite around the strategy's positioning**, keeping markdown-brain comparisons as a secondary section.

## Gap catalog (findings)

| Area | Current state | Strategy requirement |
|---|---|---|
| Licence | MIT (`LICENSE`, `pyproject.toml:6`, `README.md:104`) | Apache-2.0 + DCO, no CLA (§5, D6) |
| Contribution/security policy | No CONTRIBUTING.md, SECURITY.md, or security.txt | DCO in place, security.txt live (§11 months 0–1) |
| README positioning | "personal knowledge corpus… for an individual"; no thesis, no commitments, no strategy link | "Knowledge in common"; broad corpus definition; §5 commitments; honest scope (§7.11) |
| Corpus definition | "maintained by an individual" (README.md:5) | "belonging to a person, agent, project, team, community, or organisation" (§1) |
| COMPARISONS.md | Compares markdown-brain tools; calls the product "corpus" | Single-principal claim vs Mem0/Zep/Letta/LangMem (§3); honest competitor = folder+AGENTS.md+git (§8) |
| USAGE.md | Transform typos: "the \`corpus\` command", "pip install corpus" (lines 3, 19) | Product command is `koinome` |
| EVALUATION.md | No benchmark-integrity statement | D11: publish all results, incl. unfavourable |
| CLI | `koinome new` | Strategy demo uses `koinome init` (§8) |
| Transform plan | Lives in `docs/plans/open/`, contradicts public strategy | Completed; archive it |
| Format (not this pass) | Template manifest tracks files only; 10 note templates; no PROV/ODRL/JSON Schema | Corpus identity manifest, 6 record types, PROV frontmatter, inert ODRL, JSON Schemas (§8) |

## Work plan

### 1. Licence switch (MIT → Apache-2.0)

- `LICENSE` — replace with the full Apache-2.0 text.
- `NOTICE` (new) — `Koinome / Copyright 2026 Gilmar Souza`.
- `pyproject.toml:6` — `license = "Apache-2.0"`; also update `description` to match strategy positioning (e.g. "Koinome CLI: local-first, governed knowledge corpora for humans and AI agents.").
- `README.md` Licence section — Apache-2.0; contributions accepted under the DCO, no CLA (mirror §5 wording).
- `CHANGELOG.md` — entry: relicensed MIT → Apache-2.0 per strategy D6; strategy published; docs realigned. Note: the already-published PyPI `0.0.0alpha1` stays MIT; the next release carries the new metadata.
- No per-file licence headers (not required by Apache-2.0; keeps the diff small).

### 2. Governance files (new)

- `CONTRIBUTING.md` — DCO sign-off (`git commit -s`), explicitly no CLA and why (structural anti-relicensing guarantee, §5); inbound = outbound Apache-2.0; honest response-time expectations (§13); link STRATEGY.md.
- `SECURITY.md` — report privately to gilmar.souza@gmail.com; note that `.well-known/security.txt` goes live with the project website (strategy months 0–1 item; the repo-side artifact is SECURITY.md).

### 3. README rewrite (`README.md`)

Keep the shipped-software sections (quick start, workflow, commands, AuxMem migration) nearly intact — they describe what actually exists. Change the framing around them:

- Tagline: **"Knowledge in common."** Open with the strategy's positioning: a governed knowledge system for humans and AI agents; the unit is the corpus, using the **broad** definition from §1 (person, agent, project, team, community, or organisation).
- State the thesis in one short paragraph: sharing is the point; the local individual product is its foundation (D1). Today's release manages individual corpora, **one corpus at a time**; **cross-corpus** operations (share, contribute, transfer, merge, split, combine, federate…) are design scope proceeding via public RFCs, not shipped software. Link `docs/STRATEGY.md` prominently.
- Add a **Commitments** section with the eight bullets from §5 (local-first; account-free individual use forever; **no telemetry**; human-approved persistence; nothing crosses a boundary silently; AI proposes, never decides; complete and free; portable by construction).
- One or two sentences on the single-principal claim with a link to §3 (full essay comes later per roadmap).
- Mention `koinome init` alongside `koinome new` once the alias lands (step 5).
- Test constraints to preserve (tests/test_naming_consistency.py, tests/test_doc_consistency.py): the strings "free and open-source", "corpus", "corpora", "one corpus at a time", "cross-corpus" must remain; `--domain` examples must still parse.

### 4. Other docs

- `docs/USAGE.md` — fix line 3 ("Full reference for the **`koinome`** command… install to get **`koinome <cmd>`**") and line 19 (`pip install koinome`); add a `## koinome init` section (required by `test_cli_commands_documented_and_exist` once the alias exists).
- `docs/COMPARISONS.md` — rewrite: lead with the single-principal claim (§3: Mem0, Zep, Letta, LangMem, provider memory features — architectural claim, checkable, not implemented-feature claims); then the honest competitor (§8: markdown folder + AGENTS.md + git, the fifteen-minute bar); keep the LLM Wiki / GBrain / OpenBrain comparisons as a secondary "same substrate, different bets" section with the product named Koinome (currently called "corpus" throughout — transform artifact).
- `docs/EVALUATION.md` — add the D11 integrity statement (harness public, all results published including ones Koinome loses); mark the cross-tool benchmark harness as future work (§11 months 6–9) so design and shipped stay separated.
- `examples/README.md` — rephrase "governed work memory patterns" → governed-knowledge phrasing ("memory" reserved for the AI session-memory problem).
- `docs/plans/open/koinome-transform-plan.md` → move to `docs/plans/closed/`, with a one-line header note that it was executed and that `docs/STRATEGY.md` supersedes its licensing/scope/commercial guidance. Update `ALLOWLIST_PATHS` in `tests/test_naming_consistency.py:11` to the new path.
- `AGENTS.md` (repo root) — add a line: `docs/STRATEGY.md` is the source of truth for positioning, terminology, and honest-scope rules when editing docs.
- Commit `docs/STRATEGY.md` itself (currently untracked).

### 5. Cheap code alignments

- `koinome/cli.py` — add `init` as an alias of `new` (argparse `add_parser(..., aliases=["init"])` or a second parser delegating to `cmd_new`); update the module docstring, subcommand help, and `EPILOG` so wording matches strategy terminology. The strategy demo (§8) opens with `koinome init`; `new` stays as the documented long-form until the manifest work gives `init` its real semantics.
- Smoke coverage: extend `tests/test_cli_smoke.py` so `koinome init --name t --path …` scaffolds identically to `new`.
- `pyproject.toml` description (done in step 1).

### 6. Written proposal for the remaining codebase work (new file, no implementation)

Create `docs/plans/open/corpus-format-v0-proposal.md` — the phased proposal mapping strategy §8/§11 onto the current code, RFC-first per D10:

1. **Corpus identity manifest** (months 0–1): durable corpus ID, explicit owner/steward, per-direction boundary policies stored inert. Resolve the naming collision: today's `.koinome/manifest.json` (`koinome/manifest.py`) is template-file upgrade state, not corpus identity — propose a separate corpus manifest file at the corpus root.
2. **Six record types + JSON Schemas** (decision, claim, state, policy, instruction, source): mapping from the ten current templates (`koinome/template/90-templates/` — adr→decision, source→source, concept/entity/governance-finding→claim/state, policy/instruction new), with a `koinome upgrade` migration path.
3. **PROV-mapped frontmatter + inert ODRL fields**; validator extensions in `koinome/template/.scripts/validate_corpus.py` (schema correctness, missing sources, supersession rules, scope violations — some checks already exist).
4. **MCP server** (months 1–4): scoped context resources, proposal-flow tools.
5. **Example corpus + recorded 90-second demo** as the acceptance test for all of the above.
6. **Legacy surface stance** (per user decision): importers, MOCs, synthesis, and sync are kept and maintained as shipped individual-use value, documented as the current toolset rather than the v0 strategy surface; new investment goes to the five v0 items.

## Verification

- `uv run pytest` — full suite; specifically `tests/test_doc_consistency.py`, `tests/test_naming_consistency.py`, `tests/test_cli_smoke.py`.
- `uv run ruff check .`
- `uv build` — package builds with the new licence metadata.
- Smoke in a temp dir: `uv run koinome init --name t --path <tmp>` and `koinome new …`, then `koinome check <tmp>`.
- Grep gates: `grep -rn "MIT" README.md pyproject.toml docs/` returns only historical CHANGELOG/plan mentions; `grep -rn 'pip install corpus\|\`corpus\` command' docs/` returns nothing.

## Manual follow-ups (outside this repo)

- Enable DCO enforcement on GitHub (DCO app or branch requirement).
- Next PyPI release publishes under Apache-2.0 metadata (no republish of `0.0.0alpha1`).
- `.well-known/security.txt` when the project website exists; trademark registration (§5) is a legal action outside the repo.
