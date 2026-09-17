# Architecture — Darukaa.Earth AI Biodiversity Intelligence

This document describes the system to be built. It follows from the research in
[research.md](research.md) and the decisions in [decision-log.md](decision-log.md).

**Revision note (Pass 2):** this is the post-review version. A critical second pass (documented
in decision-log.md D11-D18) found real over-engineering, under-specification, and one missing
knowledge-system category in the Pass 1 version of this document. Every section below reflects
those fixes; nothing here was changed for stylistic reasons.

## 1. Goals, mapped to how the system is scored

| Scoring dimension | Weight | Architectural answer |
|---|---|---|
| Depth of reasoning | 30% | Explicit multi-stage reasoning chain (§5) — no single-prompt "consider everything" LLM call. Multi-domain, interaction-linked recommendations are structurally preferred over single-variable ones (§5.4). |
| Scientific grounding | 25% | Hybrid RAG over a real evidence corpus with chunk-level citation provenance (§4), a structured, correctly-cited intervention knowledge base spanning all six domains (§3), and a faithfulness check with a defined failure path (§5.5). |
| Knowledge system design | 20% | Explicit retrieval pipeline (§4) and reasoning pipeline (§5) that are individually inspectable and testable, not folded into one component. |
| Conversational intelligence | 15% | Deterministic slot-filling + clarifying questions with a defined default field set + session memory (§6). |
| Output clarity | 10% | A fixed `Recommendation` schema (§5.4) rendered consistently every turn. |

## 2. Component map

```
                         +---------------------------+
                         |   User Interaction (API)   |  text / JSON / geo-coords
                         +-------------+---------------+
                                       v
                     +-----------------------------------+
                     |   Query Understanding              |  structured extraction
                     |   (LLM, function-calling only)     |  from free text -> schema
                     +-------------+-----------------------+
                                   v
                     +-----------------------------------+
                     | Conversation / Context Handling    |  session store, slot state
                     | (deterministic controller)         |  missing-field detection
                     +------+-------------------+---------+
             below threshold |                   | >= 2 of 6 domains populated
                            v                   v
                +--------------------+  +--------------------------------+
                | Clarifying question |  | Environmental Data              |
                | generation (LLM,     |  | Normalization                   |
                | batched, default      |  | (Pydantic validation, units,    |
                | field set if no       |  |  contradiction checks)          |
                | domain named)         |  +----------------+-----------------+
                +--------------------+                    v
                              +-------------------------------------------+
                              |  Multi-Metric Reasoning                    |
                              |  one ParameterizedAssessor call per        |
                              |  populated domain (soil, climate,          |
                              |  land-use, water, human-impact,            |
                              |  biodiversity)                             |
                              +-------+-----------------------+-----------+
                                     | retrieval() call         | SubAssessments
                                     v                          v
                     +----------------------------+  +-----------------------------+
                     | Knowledge Retrieval (RAG)   |  | Interaction Table +          |
                     | hybrid BM25+dense, metadata  |  | Severity Ranking +           |
                     | filter                        |  | Confidence Propagation      |
                     +-------------+----------------+  +--------------+--------------+
                                 v                                v
                     +----------------------------+  +-----------------------------+
                     | Scientific Evidence Corpus  |  | Recommendation Generation    |
                     | (Chroma + BM25, chunk-level  |  | (KB-matched, specificity-    |
                     | provenance)                   |  | ranked, multi-domain-       |
                     +-------------+----------------+  | preferred)                   |
                                 | citations           +--------------+--------------+
                                 +----------------------------->      v
                                                             +-----------------------------+
                                                             | Faithfulness Check +         |
                                                             | Citation Attribution         |
                                                             | (defined failure path)       |
                                                             +--------------+--------------+
                                                                           v
                                                             +-----------------------------+
                                                             | Output Formatting            |
                                                             | (fixed Recommendation        |
                                                             | schema -> conversational     |
                                                             | text)                        |
                                                             +-----------------------------+
```

Every arrow above is a plain function call. There is no LLM-orchestrated agent loop anywhere in
this pipeline (Pass 2 D13) — the LLM appears only at three named, bounded points: structured
extraction from free text (§6), narrating a computed `Recommendation` into prose (§5.4), and
generating a batched clarifying question (§6). Retrieval and KB lookups are ordinary function
calls the reasoning code makes directly, not tools an agent decides whether to invoke.

## 3. Environmental data model

A single Pydantic model, `EnvironmentalProfile`, holds every metric the system can reason about,
across **six** domains (Pass 2 added the sixth — see D14):

```
EnvironmentalProfile
  soil: SoilMetrics             { organic_carbon_pct, ph, moisture_pct }
  climate: ClimateMetrics       { rainfall_category | rainfall_mm_annual, temperature_c, aridity_index }
  land_use: LandUseMetrics      { land_use_type (enum: monoculture, intercropped, agroforestry,
                                   natural_habitat, pasture, ...), fragmentation_notes }
  water: WaterMetrics           { availability_category, groundwater_trend, irrigation_dependent }
  human_impact: HumanImpactMetrics { pesticide_use, deforestation_nearby, pollution_notes }
  biodiversity: BiodiversityMetrics { species_richness_estimate, habitat_diversity_index,
                                   pollinator_activity_observed, trend }
  region: RegionContext         { free_text_region, lat, lon }  # geo-coordinates optional (bonus)
```

`BiodiversityMetrics` exists because the challenge brief lists "biodiversity indicators (species
richness, habitat diversity)" as one of five required knowledge-system categories, on par with
soil/land-use/climate/human-impact — not merely as the outcome the system optimizes for. Its
reference points come from research.md §1.7. This lets the brief's own opening example
("Biodiversity is declining on my land") be recorded as a `trend` value from turn one, not
discarded because it doesn't fit elsewhere.

**Normalization** (plain code, not LLM):
- Coerce category strings ("low"/"medium"/"high") to a canonical enum per field.
- Reject out-of-range values (pH outside 0–14, organic carbon outside 0–100%, etc.) with a
  specific error, not a silent clamp.
- **Contradiction detection is deliberately small and fully deterministic** (Pass 2 D15 — the
  Phase 1 version implied a broader, partly text-dependent contradiction check that would have
  quietly required LLM judgment calls with false-positive risk). v1 ships exactly one rule:
  `climate.rainfall_category == "high"` together with `climate.aridity_index` in the arid range
  (>0.54, the lowest of the three empirically-grounded thresholds in research.md §1.3) is
  logically inconsistent and raises a `Contradiction`, surfaced as a clarifying question rather
  than silently resolved. Additional rules may be added later, but only ones expressible purely
  over structured fields — semantic contradictions inferred from free text are explicitly out of
  scope for this project.

The **intervention knowledge base** holds the regenerative-practice entries from research.md §1.6
and (Pass 2) §1.8, spanning all six domains, not just soil/land-use. Each entry has: applicable
conditions (region/aridity-class/crop-type/land-use-type/timeframe tags), effect size range, time
horizon, evidence_type, and citation. Where a domain genuinely has no strong quantified
intervention (per research.md), the entry is marked `non_quantifiable` and carries qualitative
guidance instead of an invented number — the KB never fills a gap with a fabricated figure.

## 4. Knowledge retrieval pipeline (RAG)

**Ingestion (offline, one-time per corpus update):**
1. Parse source reports (FAO, IPCC, the peer-reviewed papers cited in research.md) by document
   structure (chapters/sections preserved).
2. Recursively chunk within sections to ~300–500 tokens with ~15–20% overlap; tables are
   extracted as their own chunks, never split mid-row.
3. **Prepend a deterministic template**, not an LLM-generated blurb, to each chunk before
   indexing: `"Source: {doc_title}. Section: {section_title}. Topic: {topic}."` (Pass 2 D11 —
   the Phase 1 version proposed an LLM call per chunk to write this context sentence. At
   ~100-300 chunks, the very next step already attaches the same information as structured
   metadata; research.md §2.5 also found that Anthropic's own benchmark only reaches its full
   accuracy gain when the blurb step is *combined* with reranking, which Pass 2 also deferred
   [below] — paying for one without the other doesn't earn the published number, so this project
   pays for neither in v1.)
4. Tag every chunk with metadata: `source_doc`, `doc_type`, `publication_year`, `region`
   (if applicable), `topic` (soil/climate/land-use/water/human-impact/biodiversity),
   `variable_name(s)`, `section`/`page`, and `evidence_type`.
5. Index into two stores: a Chroma (embedded, persistent) dense-vector collection, and an
   in-process `rank_bm25` sparse index. (`rank_bm25` is a hackathon-scale choice; if the corpus
   grows past prototype scale, architecture.md §9 notes a more actively-maintained BM25
   implementation should be substituted.)

**Query time:**
1. **Filter construction is a deterministic function, not a "self-query" LLM step** (Pass 2 D11
   — the calling sub-assessor already knows its own `domain` and the profile's `region`; there is
   no free text left to parse at this point in the pipeline): `filters = {topic: domain, region:
   profile.region.free_text_region}`.
2. Both the BM25 and dense retrievers run independently over the filtered set; results are fused
   with Reciprocal Rank Fusion (`score(d) = sum of 1/(k + rank(d))`, k=60 — the constant from the
   original RRF paper, Cormack et al. 2009, still the de facto default).
3. **Reranking is deferred, not built in v1** (Pass 2 D12 — a cross-encoder reranking stage over
   a fused top-20 is sized for corpora far larger than ~100-300 chunks; at this scale a metadata
   pre-filter plus RRF fusion is expected to already surface the right evidence in the fused
   top-3-5). Add a reranker only if manual inspection of real queries during M3 shows fusion
   alone puts the wrong evidence in the top results.
4. If evidence tagged `source_doc` from FAO or IPCC exists in the filtered result set for the
   domain being queried, it is included as supporting context alongside the primary citation even
   if it ranks below the top-3-5 by relevance (Pass 2 — the brief's own worked example
   specifically expects FAO/IPCC references; the scientifically strongest citation for a given
   number is often a peer-reviewed paper instead, per research.md §1.6, so this rule keeps both
   present rather than letting one silently exclude the other).
5. Every returned chunk carries its citation metadata forward; nothing is ever cited by a
   free-text string the LLM invents — citations are always resolved from stored provenance.

## 5. Multi-metric reasoning pipeline

This is the core differentiator the brief asks for. It is a fixed sequence of plain function
calls — no agent loop, no LLM performing the combination arithmetic.

### 5.1 Per-domain sub-assessment — one engine, not six modules

Pass 2 (D16) replaced six near-identical per-domain classes with **one** `ParameterizedAssessor`,
driven by a small per-domain config (query template, reference-metric lookup, categorical
severity table). For each populated domain in the `EnvironmentalProfile`:

1. Call `retrieve(domain, region)` (§4) for evidence relevant to that variable and the user's
   region.
2. Compute **deviation** — how far the measured value is from the reference/healthy range implied
   by the retrieved evidence, normalized to [0, 1]. For numeric fields (e.g. `soil.organic_carbon_pct`)
   this is a bounded linear distance from the range stated in the evidence. For categorical
   fields (e.g. `land_use.land_use_type`) it is a small fixed lookup derived directly from
   research.md (e.g. `monoculture` → 0.8, `intercropped` → 0.4, `agroforestry`/`natural_habitat`
   → 0.1 — drawn from the land-use/fragmentation findings in research.md §1.2).
3. Compute **confidence** from the evidence actually retrieved: `confidence = ceiling(evidence_type)
   x context_match_factor`, where `ceiling` is `established_evidence -> 0.9`, `reasonable_inference
   -> 0.6`, `non_quantifiable -> 0.35` (an entry tagged `non_quantifiable` is *always* capped at
   "low" and its narration is qualitative-only, never a fabricated number — this is the
   mechanical enforcement of the evidence_type taxonomy that Phase 1 named but never wired up),
   and `context_match_factor` is `1.0` (region/timeframe explicitly match), `0.8` (partial match),
   or `0.6` (generic, no explicit match).
4. Emit: `SubAssessment { domain, deviation, confidence, evidence: [Citation, ...], notes }`.

This record — not free LLM prose — is what everything downstream consumes, and it is what makes
the chain inspectable: any sub-assessment can be traced to the exact evidence chunk(s) and the
exact deviation/confidence numbers that produced it.

### 5.2 Cross-variable interaction table

A small, hand-authored, versioned table encodes known couplings from research.md, applied after
all populated domains have a `SubAssessment`. **v1 ships 11 rows**, systematically drawn from a
coupling explicitly discussed somewhere in research.md (Pass 2 D17 — Phase 1 shipped only 3
illustrative rows, which under-delivered on the project's own stated core differentiator; row 11
was added post-implementation once an audit noticed the brief's own three named example
couplings — soil↔biodiversity, water↔species survival, land use↔fragmentation — weren't all
covered by an explicit rule):

| # | If | And | Then | Source |
|---|---|---|---|---|
| 1 | soil.organic_carbon deviation > 0.5 | climate.rainfall = low | amplify soil deviation by +0.15 (aridity compounds soil degradation) | research.md §1.3, Berdugo et al. |
| 2 | land_use = monoculture | land_use.fragmentation = high | prefer interventions addressing both habitat structure and crop diversity | research.md §1.2, Fahrig 2017 + Niether et al. |
| 3 | water.availability = low | land_use.irrigation_dependent = true | flag drought-driven risk before recommending water-intensive interventions | research.md §1.4 |
| 4 | human_impact.pesticide_use = high | biodiversity.pollinator_activity_observed in {none, rare} | raise human_impact confidence as primary driver over competing domains | research.md §1.5, §1.1 |
| 5 | soil.ph deviation > 0.5 | biodiversity.trend = declining | raise soil confidence as a primary driver | research.md §1.1 |
| 6 | climate.aridity_index > 0.7 | biodiversity.habitat_diversity_index = low | flag discontinuous threshold risk, not gradual decline, in the narration | research.md §1.3, Berdugo/Morant |
| 7 | land_use in {agroforestry, natural_habitat} | water.availability = low | de-prioritize land-use interventions (already favorable); shift priority to water domain | research.md §1.2 |
| 8 | human_impact.deforestation_nearby = true | land_use.fragmentation = high | prioritize edge/corridor-relevant interventions | research.md §1.2, Pfeifer et al. |
| 9 | soil.moisture = low | soil.organic_carbon deviation > 0.5 | amplify soil deviation by +0.15 (compounding, not independent, risk) | research.md §1.1, Bogati et al. |
| 10 | water.groundwater_trend = declining | land_use.irrigation_dependent = true | prefer groundwater-recharge/efficient-irrigation interventions over surface interventions | research.md §1.4, Rohde et al. |
| 11 | water.availability = low | biodiversity.trend = declining (or species richness = low) | links water scarcity directly to species survival — the brief's own named example coupling | research.md §1.4 |

Each fired row either adjusts a domain's deviation/confidence by a stated, fixed amount (clamped
to [0,1]) or adjusts which domain(s) are preferred for intervention matching (§5.4) — never both
silently at once, and every adjustment is logged with which row fired.

### 5.3 Severity ranking (replaces the Phase 1 "AHP-style combination")

Pass 2 (D18) dropped the "AHP-style weighted combination" framing entirely — the Phase 1
description had none of AHP's actual machinery (no pairwise comparison matrix, no
eigenvector-derived weights), so keeping the name risked either wasted effort building real AHP
during implementation or a credibility problem for claiming a named method without its substance.
It is also unnecessary: **no cross-domain weight table is needed**, because domains are not
combined into one overall score. Each domain is ranked independently:

```
severity(domain) = deviation(domain) x confidence(domain)
```

Domains are ranked by `severity` descending. Pass 2 explicitly considered — and rejected —
deriving cross-domain weights from the IPBES global driver-attribution percentages
(land/sea-use ~30%, exploitation ~23%, climate ~14%, pollution ~14%, invasive species ~11%;
research.md §1.2/§1.5): those are aggregate, global, cross-ecosystem statistics, and stretching
them into a per-user-profile domain-priority weight would be exactly the kind of unsupported
inferential leap D8/D9 exist to prevent. Severity-by-deviation avoids inventing that
relationship while still producing a principled ranking.

**Worked example.** Populated domains: soil (deviation 0.8, confidence 0.9 — established
evidence, exact region match), climate (deviation 0.6, confidence 0.45 — reasonable_inference,
partial match), land_use (deviation 0.8, confidence 0.81 — established evidence, strong match).
Interaction row #1 fires (soil deviation > 0.5, low rainfall) -> soil deviation 0.8 -> 0.95
(clamped). Severities: soil = 0.95 x 0.9 = 0.855; land_use = 0.8 x 0.81 = 0.648; climate = 0.6 x
0.45 = 0.27. Ranked: soil > land_use > climate. Because row #1 links soil and climate, the
recommendation is built from **both** domains (§5.4's multi-domain preference), not soil alone.
Its confidence is `min(confidence(soil), confidence(climate)) = min(0.9, 0.45) = 0.45` -> label
"medium" (thresholds: high >=0.7, medium 0.4-0.7, low <0.4; forced to "low" and qualitative-only
phrasing if any contributing domain's evidence_type is `non_quantifiable`, regardless of the
numeric value).

### 5.4 Recommendation generation

1. Take the top-ranked domain(s) — a single domain, or the set linked by a fired interaction row
   (preferred, since it directly satisfies the brief's "no single-variable answers" constraint
   structurally, not just by hoping the LLM avoids genericity).
2. Query the intervention KB (§3) for entries whose `applicable_conditions` match the profile.
   If multiple entries match: prefer entries whose own supporting domains overlap ≥2 of the
   top-ranked domains; among ties, rank by number of matching condition tags (region/aridity-
   class/crop-type/timeframe — most specific wins, e.g. the wheat–vetch semi-arid trial over a
   generic decadal agroforestry figure for the brief's own example); among remaining ties, prefer
   `established_evidence` over `reasonable_inference`.
3. **If no KB entry matches the top-ranked domain**, the system does not silently substitute a
   different domain or invent a recommendation. It states the limitation explicitly ("no specific
   intervention in our knowledge base directly targets X under these conditions") and offers the
   best available RAG-grounded qualitative guidance from retrieved evidence directly, with
   citation, at capped ("low"/"medium") confidence.
4. Build the `Recommendation`:
   ```
   Recommendation {
     what: str
     why: str                       # LLM-narrated, must reference >=1 concrete measured value
                                     # from supporting_variables (checked, §5.5)
     supporting_variables: [str]
     impacted_metrics: [str]
     time_horizon: "short" | "medium" | "long"
     evidence: [Citation]
     limitations: str
     confidence: "low" | "medium" | "high"
   }
   ```
   The LLM's only role is narrating this already-computed object — it does not invent `what`,
   `impacted_metrics`, or `confidence`.

### 5.5 Faithfulness check and its failure path

A lightweight check runs before a `Recommendation` is returned: does every factual clause in the
narrated `why` trace back to a retrieved evidence chunk or a structured measured value? Pass 2
added the failure contract Phase 1 left unspecified: **on failure, the unsupported clause is
dropped from the narration (never silently passed through), the recommendation's confidence is
downgraded one tier, and the limitation is stated explicitly.** A second blocklist check screens
`what`/`why` against a short list of generic phrasings ("use sustainable practices", "protect
biodiversity" with no named practice) as a defense-in-depth backstop — the primary defense
against genericity is structural (multi-domain preference + specific-citation preference in
§5.4), not this blocklist.

## 6. Conversational intelligence

- **Session store**: keyed by session id, holds the accumulated `EnvironmentalProfile` plus
  per-field provenance.
- **Extraction**: each user turn is passed to the LLM in structured-output/tool-use mode,
  constrained to `EnvironmentalProfile`'s schema, to extract new field values. A validation-retry
  loop re-prompts on invalid values rather than accepting a guess.
- **Reasoning threshold** (Pass 2 — previously unspecified): the system attempts full reasoning
  and produces a recommendation once **at least 2 of the 6 domains have >=1 populated field**.
  Below that, it always asks a batched clarifying question first.
- **Default field set** (Pass 2 — previously unspecified, and this is exactly the brief's own
  worked example): when a query expresses general concern without naming a domain (e.g.
  "Biodiversity is declining on my land"), the clarifying question asks for the baseline triage
  set — `soil.organic_carbon_pct`, `climate.rainfall_category`, `land_use.land_use_type` —
  matching the brief's example verbatim. When the query names a specific domain or symptom (e.g.
  "my soil seems degraded"), the question narrows to that domain's fields instead.
- **Contradiction handling**: if normalization (§3) raises a `Contradiction`, the controller asks
  the user to resolve it explicitly.
- **Context adaptation**: later turns can add or revise a single metric without re-asking
  already-answered fields; the session profile updates incrementally and is re-reasoned.

## 7. Interfaces and replaceability

| Interface | Current implementation | Notes |
|---|---|---|
| `EvidenceStore` (add/query chunks) | Chroma (embedded) + `rank_bm25` | Swappable for Qdrant/pgvector if the corpus outgrows this scale (architecture.md §9). |
| `MeasurementStore` (session profiles, intervention KB) | SQLite | Swappable for Postgres. |
| `llm_extract(text, schema)` / `llm_narrate(recommendation)` | Thin wrapper around one concrete provider (Anthropic Claude, native tool use) | **Not a multi-provider abstraction** — this project only ever calls one provider; a formal swappable `LLMClient` interface was cut as untested generality per the Pass 2 complexity audit. The wrapper exists so tests can mock it, nothing more. |

No component reaches into another's storage directly.

## 8. Input handling

- **Text** (mandatory): free-form message, run through extraction (§6).
- **Structured (JSON)**: a request body matching `EnvironmentalProfile` (or a subset) merges
  directly into the session profile, bypassing LLM extraction for those fields.
- **Geo-coordinates (bonus)**: used only as a metadata filter tag for regional evidence retrieval
  and narrative context — no geospatial modeling is invented for this.

## 9. Deployment architecture

Single Python process (FastAPI) is sufficient for the hackathon scope:
- Chroma persists to a local directory; BM25 index and SQLite files live alongside it.
- A CLI chat loop and a thin JSON API are both provided as front ends to the same conversation
  core — no dedicated frontend build, consistent with the brief's "not UI-heavy" framing.
- The same single-process design deploys as-is to a small VM/container if a live demo URL is
  wanted for submission.
- Production migration path (documented, not built): swap `EvidenceStore` to pgvector and
  `MeasurementStore` to Postgres; reconsider `rank_bm25` in favor of a more actively-maintained
  BM25 implementation (e.g. `bm25s`) if the corpus grows past prototype scale (research.md §2.5
  fact-check).

## 10. Explicitly out of scope for this build

- GraphRAG / knowledge-graph extraction.
- Any agentic tool-calling loop — retrieval and KB lookups are plain function calls (§2, §5.1).
- LLM-generated per-chunk context blurbs and cross-encoder reranking in v1 (§4) — deferred until
  observed retrieval quality justifies the added cost.
- A formal multi-LLM-provider abstraction (§7).
- Real AHP (pairwise comparison matrices, eigenvector weight derivation) — replaced by severity
  ranking (§5.3).
- Cross-domain weights derived from global driver-attribution statistics (§5.3) — rejected as
  scientific overreach.
- Semantic (free-text-derived) contradiction detection (§3) — only structural, field-level
  contradictions are checked.
- Any invented geospatial modeling beyond using coordinates as a metadata/context tag (§8).
- A dedicated frontend application.
