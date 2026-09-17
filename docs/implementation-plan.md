# Implementation Plan — Darukaa.Earth AI Biodiversity Intelligence

This plan sequences the build described in [architecture.md](architecture.md), post Pass 2
review. Each milestone has a goal, concrete tasks, and exit criteria that must be checked
(tests run, code inspected, dead code removed) before moving to the next one.

**Pass 2 changes reflected here:** six reasoning domains (biodiversity added), one parameterized
assessor engine (not six modules), no LLM-generated chunk blurbs or reranker in v1, no "AHP" —
domains are ranked by severity, a concrete confidence formula, a 10-row interaction table, a
single deterministic contradiction rule, specificity-based KB matching with an explicit no-match
fallback, and three new evaluation scenarios. See [decision-log.md](decision-log.md) D11-D24.

## Milestones

### M0 — Project scaffolding
- Python 3.11+ project layout: `measurements/`, `knowledge/`, `reasoning/`, `conversation/`,
  `api/`, `data/`, `tests/`.
- Dependency management (`pyproject.toml`), config for the Anthropic API key via environment
  variables, `pytest` wired up.
- Minimal FastAPI app that boots and returns a health check.
- Exit criteria: `pytest` runs; app starts locally.

### M1 — Environmental data model & normalization
- `EnvironmentalProfile` across all **six** domains (soil, climate, land_use, water,
  human_impact, biodiversity — architecture.md §3) with range validation.
- The single deterministic contradiction rule (rainfall_category="high" + arid-range
  aridity_index) — architecture.md §3/D15. No other contradiction rules in v1.
- Exit criteria: unit tests cover a valid full profile, an out-of-range value (rejected), and
  the contradiction rule (flagged, not silently resolved).

### M2 — Intervention knowledge base (structured dataset)
- Encode intervention entries from research.md §1.6 (soil/land-use: agroforestry, intercropping,
  cover cropping, rotation + reduced tillage, buffer strips) **and §1.8 (water and human-impact
  interventions, Pass 2 gap-fill)** into SQLite, each with `applicable_conditions` tags (region,
  aridity-class, crop-type, land-use-type, timeframe), effect size range, time horizon,
  evidence_type, and exact citation copied from research.md.
- Exit criteria: KB loads and is queryable by condition tags across all six domains; a review
  pass confirms every entry's citation matches research.md exactly; at least one entry exists per
  domain, or the domain is explicitly documented as relying on the no-match fallback (D20) rather
  than left silently empty.

### M3 — Evidence corpus ingestion & hybrid retrieval
- Curate short, fair-use excerpts (not full copyrighted PDFs) plus full citation metadata for the
  sources in research.md.
- Chunking, **deterministic per-chunk context template** (D11 — not an LLM call), metadata
  tagging (including the `biodiversity` topic), Chroma + BM25 indexing, reciprocal-rank-fusion.
  **No reranker in v1** (D12).
- Deterministic filter builder (`{topic: domain, region: profile.region}`), not an LLM
  self-query step (D13).
- FAO/IPCC-inclusion rule (D21): if FAO/IPCC-sourced evidence exists in the filtered result set
  for a domain, include it as supporting context regardless of relevance rank.
- Exit criteria: a query such as "soil organic carbon semi-arid" returns relevant chunks with
  correct metadata and resolvable citations; hybrid retrieval demonstrably outperforms BM25-only
  and dense-only on a small hand-labeled query set; manually inspect 10-15 real queries and only
  add a reranker (D12) if fusion alone is visibly putting wrong evidence in the top-3-5.

### M4 — Multi-metric reasoning pipeline
- **One** `ParameterizedAssessor(config)` engine (D16) run once per populated domain, computing
  `deviation` (numeric: bounded linear distance from the evidence-stated reference range;
  categorical: a small fixed lookup from research.md, e.g. land-use type) and `confidence`
  (`ceiling(evidence_type) x context_match_factor`, per architecture.md §5.1) for each.
- The 10-row cross-variable interaction table (architecture.md §5.2, D17).
- Severity ranking (`severity = deviation x confidence`, architecture.md §5.3, D18) — no weight
  table, no AHP machinery.
- Exit criteria: given the challenge PDF's own example input (SOC 0.3%, low rainfall, monoculture
  wheat, semi-arid region), the pipeline reproduces the worked example in architecture.md §5.3
  (interaction row #1 fires, soil ranks above land_use above climate, confidence = 0.45/"medium"),
  fully traceable back to specific evidence and the specific interaction row.

### M5 — Recommendation generation & citation attribution
- Intervention KB matching with the specificity tie-break and multi-domain preference (D20):
  prefer entries whose supporting domains overlap >=2 of the top-ranked domains; among ties, most
  matching condition tags wins; among remaining ties, prefer `established_evidence`.
- Explicit no-KB-match fallback (D20): state the limitation, offer the best RAG-grounded
  qualitative evidence directly, capped confidence — never silently substitute or invent.
- Faithfulness self-check with its defined failure contract (D22): on failure, drop the
  unsupported clause, downgrade confidence one tier, state the limitation.
- Secondary blocklist check on `what`/`why` against generic phrasings (architecture.md §5.5),
  as a backstop behind the structural multi-domain/specificity preference.
- Exit criteria: recommendations always populate all required fields (what / why / impacted
  metrics / time horizon / evidence / limitations / confidence); no evidence field ever contains
  an unresolvable citation; the PDF's own example selects the wheat-vetch/semi-arid-weighted
  citation over the generic decadal agroforestry figure, with an FAO/IPCC citation included
  alongside it per D21.

### M6 — Conversational layer
- Session store; LLM-based structured extraction with validation-retry; deterministic
  missing-field controller.
- Reasoning threshold (D23): attempt full reasoning once >=2 of 6 domains are populated;
  otherwise ask one batched clarifying question.
- Default field set (D23): SOC%, rainfall category, land-use type when the query names no
  specific domain (reproduces the brief's own example); narrows to the named domain's fields
  when the query is domain-specific.
- Exit criteria: "Biodiversity is declining on my land" reproduces the brief's exact clarifying
  question; a later turn revising one field updates the session profile without re-asking
  already-answered fields; a domain-specific query ("my soil seems degraded") asks only about
  soil fields, not the full default set.

### M7 — API & CLI front ends
- FastAPI endpoints for text chat, structured JSON input, session management; a CLI chat loop
  against the same conversation core.
- Exit criteria: the same underlying pipeline is reachable through both text and JSON input paths
  with identical reasoning/output behavior.

### M8 — Evaluation suite
- Automated tests for the 11 scenarios below, each asserting the *properties* required, not just
  that a response was returned.
- Exit criteria: all 11 scenario tests pass on their actual assertions.

### M9 — Polish & documentation
- Remove scratch scripts, dead code, and duplicate utilities. Confirm no "AHP" language survives
  anywhere in code or docs (D18), and that all six domains are consistently named throughout.
- Write `README.md` covering: architecture summary, database/schema summary, local setup, and a
  statement of CI/CD scope.
- Exit criteria: repository matches the "Final Deliverable" list in the master prompt, with no
  leftover experimental files.

---

## Requirement coverage matrix

| Challenge requirement | Implementation | Milestone(s) |
|---|---|---|
| Structured knowledge base spanning soil, land use, biodiversity indicators, climate, human impact | Intervention KB (SQLite) + evidence-corpus metadata schema, all six domains including biodiversity (D14) | M2, M3 |
| Understand user queries about ecosystems, land, climate | `EnvironmentalProfile` (6 domains) + LLM structured extraction | M1, M6 |
| Actionable, non-obvious recommendations | Multi-domain-preferred, specificity-ranked KB matching (D20) — a structural mechanism, not just schema compliance | M4, M5 |
| Every recommendation backed by scientific reasoning + evidence | `Recommendation.why`/`.evidence`, faithfulness check with defined failure path (D22) | M5 |
| Knowledge system: RAG / embeddings / vector DB / structured datasets | Chroma + BM25 hybrid RAG (deterministic templates, no reranker in v1), structured intervention KB | M2, M3 |
| Index research papers, reports, datasets | Ingestion pipeline over FAO/IPCC/peer-reviewed sources | M3 |
| Clearly show how knowledge is retrieved and used | Citation provenance on every recommendation; FAO/IPCC inclusion rule (D21) | M3, M5 |
| Clarifying questions when input incomplete | Deterministic missing-field controller with reasoning threshold + default field set (D23) | M6 |
| Multi-turn conversations with memory | Session store | M6 |
| Adapt responses based on context | Incremental profile updates across turns | M6 |
| Evidence-backed recommendations (what/why/metric/reference) | `Recommendation` schema | M5 |
| Multi-metric reasoning (soil<->biodiversity, water<->species, land use<->fragmentation) | `ParameterizedAssessor` + 10-row interaction table (D16, D17) | M4 |
| Text input (mandatory) | CLI/API text endpoint | M7 |
| Structured input, JSON (mandatory) | JSON endpoint merging into `EnvironmentalProfile` | M1, M7 |
| Geo-coordinates / spatial context (bonus) | `RegionContext.lat/lon` used as a retrieval metadata filter only | M1, M3 |
| Output: recommendation, impacted metrics, time horizon, confidence | `Recommendation` schema + output formatting | M5 |
| Must handle >=3 environmental variables together | Interaction table + severity ranking across up to 6 domains | M4 |
| No shallow/generic/single-variable answers | Structural multi-domain preference + specificity tie-break (D20), blocklist backstop | M2, M4, M5 |

## Evaluation scenarios (M8)

1. **Complete structured input** — full JSON profile across multiple domains. Checks: retrieval
   invoked per populated domain; multiple sub-assessments produced; recommendation fields all
   populated.
2. **Missing environmental variables** — partial/no domain named. Checks: one batched clarifying
   question naming the default field set (D23) exactly.
3. **Conflicting measurements** — the D15 rainfall/aridity contradiction. Checks: `Contradiction`
   raised and surfaced, not silently resolved.
4. **Low-confidence evidence** — a domain whose only matching evidence is `non_quantifiable`.
   Checks: confidence is forced to "low" and the narration is qualitative-only (§5.1 ceiling
   rule), regardless of any numeric deviation computed.
5. **Multiple interacting environmental variables** — inputs chosen to fire at least two distinct
   rows of the 10-row interaction table (D17). Checks: both adjustments are visible in the trace
   and affect the resulting domain ranking/recommendation.
6. **A query requiring clarification** — the brief's own example ("Biodiversity is declining on
   my land"). Checks: the default field set (D23) is asked for verbatim.
7. **A recommendation requiring scientific retrieval, with the specificity tie-break** — the
   brief's own example inputs (SOC 0.3%, low rainfall, monoculture wheat, semi-arid). Checks: the
   wheat–vetch/semi-arid-weighted citation is selected over the generic decadal agroforestry
   figure (D20), and an FAO/IPCC citation is present alongside it (D21).
8. **A recommendation where evidence does not support a precise numerical estimate** — checks a
   qualitative statement or sourced range is used, not a fabricated percentage (regression test
   for D8).
9. **No KB match for the top-ranked domain** — an input whose top-ranked concern has no matching
   intervention KB entry. Checks: the limitation is stated explicitly and the system falls back
   to qualitative RAG evidence at capped confidence, rather than silently substituting a
   different domain or inventing a recommendation (D20).
10. **Non-obvious/genericity enforcement** — an input where both a single-domain-generic KB entry
    and a multi-domain interaction-linked entry could apply. Checks: the multi-domain entry is
    preferred (D20); a unit test separately confirms the blocklist check rejects a deliberately
    generic phrasing ("use sustainable practices" with no named practice).
11. **Faithfulness-check failure path** — a deliberately unsupported clause injected into a
    narration. Checks: the clause is dropped, confidence is downgraded one tier, and the
    limitation is stated (D22) — never silently passed through.
