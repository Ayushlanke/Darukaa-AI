# Decision Log — Darukaa.Earth AI Biodiversity Intelligence

Concise record of architectural decisions and why they were made. See
[research.md](research.md) for the full option comparisons behind each entry.

---

**D1 — Repository starts from scratch.**
Context: the working directory contained only the master prompt and the challenge PDF — no
existing code, no git history, no package manifest.
Decision: greenfield Python project; no legacy constraints to preserve.
Status: confirmed by direct inspection (`find` over the repo root).

---

**D2 — Language/runtime: Python 3.11+.**
Context: needs a mature RAG/ML ecosystem (embeddings, vector stores, structured-output LLM
clients) and easy handling of structured environmental data.
Alternatives: Node/TypeScript (weaker RAG-library ecosystem; would mean hand-rolling more of
§4/§5 of architecture.md).
Rationale: every technical research finding (RAG, vector store, reasoning, memory) cites
Python-ecosystem libraries (LlamaIndex/LangChain, Chroma, `rank_bm25`, Pydantic/Instructor) as
the current, best-precedented tooling for this exact problem shape.
Status: decided.

---

**D3 — RAG architecture: hybrid (BM25 + dense) retrieval, contextual chunking, reranking, wrapped
in a bounded two-tool agent that also reads structured measurements.**
Context: research.md §2.1 compared naive single-index RAG, this hybrid approach, a fuller
agentic RAG, and GraphRAG.
Rejected: naive RAG (weak on exact scientific vocabulary, no query-time filtering); GraphRAG
(cold-start entity/relationship extraction from narrative reports is not reliable within a
hackathon timeline; per-chunk metadata filtering captures most of the same benefit far more
cheaply at this corpus size); open-ended/unbounded agentic planning (too many failure modes to
debug on a fixed clock).
Rationale: a directly analogous production system (ChatClimate, grounded in IPCC AR6) validates
this general pattern for this exact domain; Anthropic's published Contextual Retrieval technique
is a one-time, affordable preprocessing step with a documented accuracy gain.
Status: decided.

---

**D4 — Retrieval storage: Chroma (embedded, persistent) + in-process BM25 for the evidence
corpus; structured environmental measurements and the intervention knowledge base live in
SQLite, never embedded as pseudo-documents.**
Context: research.md §2.2 compared Chroma, FAISS, pgvector, LanceDB, Weaviate, Pinecone, Qdrant,
and plain BM25/JSON.
Rejected: FAISS (no persistence/metadata filtering — would require hand-building exactly the
scaffolding Chroma provides free); Pinecone/Weaviate (external network dependency or Docker/K8s
ops burden not justified at hackathon corpus size); plain BM25 alone (misses paraphrase/synonym
matches central to scientific grounding).
Rationale: zero-setup, fully offline (no demo-day network dependency), native metadata filtering,
comfortably handles the corpus size in play. Keeping structured measurements out of the vector
store avoids a known RAG anti-pattern (conflating structured, filterable data with unstructured
text-to-search).
Status: decided. Production migration path (pgvector/Postgres) documented in architecture.md §9,
not built now.

---

**D5 — Multi-metric reasoning: blackboard-style per-domain sub-assessments -> hand-authored
cross-variable interaction table -> AHP-style weighted combination with mechanical confidence
propagation. The LLM never performs the combination arithmetic.**
Context: research.md §2.3 compared AHP/MCDA, Bayesian networks, fuzzy cognitive maps, a
neurosymbolic hybrid, and a blackboard multi-agent pattern.
Rejected as the *sole* pattern: AHP alone (no cross-variable interaction modeling); full Bayesian
networks (conditional-probability-table elicitation too heavy for the timeline); a single
LLM prompt asked to "consider all variables" (fails the hard inspectability requirement outright
— cannot show which variable drove which part of a score, cannot reproduce the same confidence
twice).
Rationale: this is the master prompt's explicitly named "most important part of the project."
Combining patterns (blackboard for provenance/orchestration, AHP for the actual combination step,
a small interaction table for known couplings, neurosymbolic split for where the LLM is trusted)
is the only combination that satisfies the hard "inspectable and explicit" requirement while
staying buildable in the timeline.
Status: decided.

---

**D6 — Conversational memory: a custom lightweight typed-schema + deterministic missing-field
controller, not a framework (LangGraph, LlamaIndex memory blocks).**
Context: research.md §2.4 compared four options, including the explicit anti-pattern of dumping
the raw transcript into the prompt each turn.
Rejected: dumping the transcript and letting the LLM decide what to ask (documented failure mode
— LLMs recognize incompleteness internally but still fail to ask, silently guessing instead);
LangGraph/LlamaIndex memory frameworks (real capabilities, but their advantages — checkpointed
multi-session persistence, integrated retrieval-memory pipelines — matter more for a production
system than for a judged hackathon demo, and add real learning-curve risk on a fixed clock).
Rationale: conversational intelligence is only 15% of the score; "what's missing" being ordinary
deterministic code (not model-decided) directly protects against a dropped required metric
silently corrupting a downstream recommendation — a correctness property worth more than
framework polish here.
Status: decided. Revisit if the project moves beyond a hackathon (LangGraph becomes reasonable
once multi-session persistence and replay/debugging actually matter).

---

**D7 — Embeddings and reranking run locally; only structured-extraction and final narration call
an external LLM API.**
Context: an external vector-DB or reranking API was rejected in D4 partly for demo-day network
risk; the same reasoning applies to embeddings.
Rationale: keeps the retrieval half of the system fully offline and reproducible; the LLM API
dependency is unavoidable for the conversational/reasoning-narration half of an "AI" system, so
it is accepted there, but not spread into components that do not need it.
Status: decided.

---

**D8 — The hackathon brief's own worked example statistic ("agroforestry/cover crops increase
soil organic carbon by ~15–25% over 2–3 years, FAO studies") is rejected as a citable fact.**
Context: independent verification (research.md §1.6) fetched FAO's own primary SOC materials
directly and found no such figure — only decadal (+40% over 5 decades) and annual-mass (~7 t
C/ha/yr) figures.
Rationale: the master prompt's working rule ("do not invent scientific relationships,
percentages, datasets, papers, APIs, or capabilities... verify the underlying source") applies
even to figures supplied by the challenge brief itself. Using it uncritically would mean building
a system that fails its own scientific-grounding requirement on day one.
Consequence: the intervention knowledge base (architecture.md §3) uses the actually-verified,
correctly-cited figures from research.md §1.6 instead (notably the wheat–vetch intercropping
trial, which is a better timeframe/region match for the brief's own scenario than the rejected
figure was).
Status: decided, and treated as the motivating example for D9.

---

**D9 — Citation verification is a first-class architecture concern, not an afterthought.**
Context: even the careful, source-checking research pass behind this project's own docs produced
several misattributed authors/journals/years (caught only by a second, independent verification
pass — see research.md's Method section).
Rationale: if careful human-directed research still produces citation errors, a
recommendation-generation LLM asked to cite sources from memory will too. The system must never
let the LLM write a citation string from memory — citations are always resolved from stored
chunk-level provenance (architecture.md §4), and a lightweight faithfulness self-check runs
before a claim reaches the user.
Status: decided; directly shapes architecture.md §4 and §5.4.

---

**D10 — No dedicated frontend; a CLI and a thin JSON API are the interaction surfaces.**
Context: the brief states explicitly "we are not looking for UI-heavy applications... depth of
thinking, system design, and scientific reasoning" are what's scored; output clarity is only 10%
of the score.
Rationale: hackathon time is better spent on the reasoning/knowledge pipeline (75% of the score
combined) than on frontend polish. The same thin API can be pointed at a minimal static page
later if a "live demo URL" is wanted for submission, without changing any core component.
Status: decided.

---

## Pass 2 — critical review

A second, independent review round (four parallel audits: a fact-check of Part 1's *technical*
research claims — which, unlike the scientific claims, had never been independently verified;
an architecture-complexity audit; a requirements-coverage audit against the original PDF; and a
scientific gap-fill for the intervention KB) found real problems in the Pass 1 design below.
Nothing in D1-D10 above needed to be reversed; D11-D24 are corrections and refinements on top of
it, per research.md §2.5 and the Pass 2 audit findings.

---

**D11 — Ingestion uses a deterministic per-chunk context template, not an LLM-generated blurb.**
Context: Pass 1 proposed prepending an LLM-written 1-2 sentence context blurb to every chunk
before indexing ("Anthropic Contextual Retrieval"), justified by a claimed ~87%->~95% Pass@10
gain. The Pass 2 fact-check found that figure is real but misattributed: reaching ~95% requires
*combining* the blurb step with reranking (D12); the blurb alone only reaches ~92% (research.md
§2.5). At our corpus scale (~100-300 chunks), the very next ingestion step already attaches the
same disambiguating information as structured metadata (source_doc, section, topic).
Rejected: paying for an LLM call per chunk for a benefit largely redundant with metadata already
being attached, and only partially responsible for the benchmark number originally cited.
Decision: prepend a deterministic template (`"Source: {doc}. Section: {section}. Topic: {topic}."`)
instead — zero cost, same disambiguation value at this scale.
Status: decided.

---

**D12 — Cross-encoder reranking is deferred, not built in v1.**
Context: Pass 1 specified reranking the fused top-20 retrieval results as a required pipeline
step. The complexity audit found this sized for corpora far larger than ours, adding a model
dependency and failure point for a benefit not demonstrated at this scale (a metadata pre-filter
already narrows the candidate pool before fusion runs).
Decision: ship v1 without a reranker; add one only if manual inspection of real queries during
M3 shows RRF fusion alone puts the wrong evidence in the top-3-5.
Status: decided, revisit during M3 if evidence quality warrants it.

---

**D13 — The retrieval/reasoning pipeline is a fixed sequence of plain function calls; there is no
agentic tool-calling loop, and no LLM-based "self-query" filter-extraction step.**
Context: D3 originally described the RAG design as "a bounded two-tool agent," and Pass 1's
architecture separately proposed an LLM "self-query" step to extract retrieval filters. The
complexity audit found both are agent-shaped machinery solving a problem plain code already
solves: by the time retrieval is called, the calling code already knows its own domain and the
user's region from the validated `EnvironmentalProfile` — there is no free text left to parse,
and no need for an LLM to decide whether to call a tool.
Decision: retrieval and knowledge-base lookups are direct function calls made by the reasoning
code; filter construction is `{topic: domain, region: profile.region}`, computed in plain code.
Status: decided; D3 is superseded by this framing.

---

**D14 — Biodiversity indicators (species richness, habitat diversity, pollinator activity) are a
sixth first-class input domain, not only an output the system optimizes for.**
Context: the requirements-coverage audit found the PDF explicitly lists biodiversity indicators
as one of five required knowledge-system categories, on par with soil/land-use/climate/human-
impact — but Pass 1's `EnvironmentalProfile`, sub-assessors, and retrieval metadata schema only
covered four of the five, treating biodiversity purely as an outcome.
Rationale: without this, the brief's own opening example ("Biodiversity is declining on my
land") has nowhere to be recorded as structured input, and the knowledge system is missing an
explicitly required category.
Decision: add `BiodiversityMetrics` to `EnvironmentalProfile`, a sixth `ParameterizedAssessor`
domain, a `biodiversity` retrieval topic tag, and research.md §1.7 as its reference-point
research (reframing findings already gathered, not new primary research).
Status: decided.

---

**D15 — Contradiction detection ships exactly one deterministic, structural rule in v1.**
Context: Pass 1's architecture implied a broader contradiction-detection capability but its own
worked example (a stated "recent conversion" to a different land use) depended on interpreting
free text — which conflicts with the same section's claim that contradiction checks are "plain
code, not LLM."
Rejected: any contradiction rule that requires inferring a fact from free text, since that
reintroduces LLM-judgment false-positive risk the "plain code" framing was meant to avoid.
Decision: v1 ships one purely structural rule (`rainfall_category="high"` together with an
`aridity_index` in the arid range is logically inconsistent) with room to add more later, as
long as every future rule is expressible over structured fields alone.
Status: decided.

---

**D16 — One parameterized assessor engine, not five/six near-identical per-domain modules.**
Context: the complexity audit flagged that building six separate sub-assessor classes (one per
domain, each doing the same three-step shape) risks copy-paste drift under hackathon time
pressure for no rubric benefit — traceability is preserved just as well by one engine driven by
per-domain config.
Decision: implement a single `ParameterizedAssessor(config)`; keep per-domain thresholds, query
templates, and severity lookups in a small config structure, not six classes or files.
Status: decided.

---

**D17 — The cross-variable interaction table ships with 10 systematically-sourced rows in v1, not
3 illustrative ones.**
Context: the interaction table is explicitly the project's own stated core differentiator (the
master prompt's "most important part"), but Pass 1's architecture doc showed only 3 example
rows with no stated target size or sourcing method — a real risk of under-delivering on the
highest-weighted rubric dimension (reasoning depth, 30%).
Decision: commit to 10 rows (architecture.md §5.2), each traceable to a specific coupling
discussed somewhere in research.md, as the v1 floor — not a ceiling; more may be added if
implementation time allows.
Status: decided.

---

**D18 — Dropped the "AHP-style" framing; domains are ranked by severity (deviation x confidence),
not combined via any weighted-sum/AHP method. Cross-domain weights derived from global driver-
attribution statistics were considered and rejected.**
Context: the complexity audit found "AHP-style" mischaracterized what was actually specified (a
fixed weighted sum/min with no pairwise comparison matrix or eigenvector weight derivation) —
risking either wasted effort building real AHP machinery, or a credibility problem for claiming
a named method without its substance. Separately, while designing a replacement, deriving
cross-domain weights from IPBES's global biodiversity-driver-attribution percentages
(land/sea-use ~30%, exploitation ~23%, climate ~14%, pollution ~14%, invasive ~11%) was
considered, since research.md already contains those figures.
Rejected: the IPBES weighting idea specifically — those are aggregate, cross-ecosystem global
statistics; treating them as a per-user-profile domain-priority weight would be exactly the kind
of unsupported inferential leap D8/D9 exist to prevent.
Decision: rank domains independently by `severity = deviation x confidence`; no cross-domain
combination step or weight table is needed at all, which resolves the under-specification finding
by removing the need for weights rather than inventing a number for them.
Status: decided.

---

**D19 — The LLM boundary is a thin wrapper around one concrete provider (Anthropic Claude, native
tool use), not a swappable multi-provider abstraction.**
Context: Pass 1's architecture named a formal, swappable `LLMClient` interface for "any function-
calling-capable model." The complexity audit flagged this as untested generality: the project
will only ever call one provider, so an abstraction built for provider-swapping that is never
exercised against a second provider costs design/implementation time without being verifiable,
and nothing in the rubric rewards it.
Decision: a plain wrapper function/class around the Anthropic SDK's tool-use API, sufficient for
mocking in tests. No formal multi-provider interface.
Status: decided.

---

**D20 — Recommendation-to-intervention matching prefers multi-domain, most-specific KB entries,
and has an explicit no-match fallback.**
Context: the requirements audit found two related gaps: (1) nothing structurally prevented a
schema-compliant but generic recommendation (the brief's explicit "no shallow or obvious
recommendations" constraint had no enforcement beyond hoping the LLM narrates well); (2) when
several KB entries satisfy the same "applicable conditions" (e.g. the brief's own semi-arid
example, where both a generic decadal agroforestry figure and the more specific wheat-vetch
semi-arid trial from research.md §1.6 apply), nothing guaranteed the better-matched one was
actually selected; (3) it was undocumented what happens when the top-ranked concern domain has
no matching KB entry at all.
Decision: (1) prefer KB entries whose supporting domains overlap >=2 of the top-ranked (severity-
linked) domains over single-domain matches — this is a structural, not hopeful, defense against
genericity; (2) among matching entries, rank by number of matching condition tags (region/
aridity-class/crop-type/timeframe), most-specific wins, tie-broken by evidence_type; (3) if no KB
entry matches, state that limitation explicitly and fall back to the best RAG-grounded
qualitative evidence directly, at capped confidence — never silently substitute a different
domain or invent a recommendation.
Status: decided; see architecture.md §5.4.

---

**D21 — Retrieval always surfaces relevant FAO/IPCC evidence alongside the primary citation when
it exists in the corpus for that domain, even if it ranks below the top-3-5 by relevance.**
Context: the requirements audit noted the brief's own worked example explicitly expects FAO/IPCC
references, but the scientifically strongest citation for the specific SOC-improvement numbers
is peer-reviewed journal literature (research.md §1.6), not FAO/IPCC directly. Per D8, the system
correctly will not force a fabricated FAO figure — but nothing guaranteed a genuinely relevant
FAO/IPCC citation (e.g., drylands/aridity context) still appeared in the response alongside the
more precise citation, risking a literal grading pass penalizing a scientifically-better answer.
Decision: when filtered retrieval for a domain includes FAO/IPCC-sourced evidence, include it as
supporting context alongside the primary citation, regardless of its relevance rank.
Status: decided; see architecture.md §4 step 4.

---

**D22 — The faithfulness self-check has an explicit failure contract: drop the unsupported
clause, downgrade confidence one tier, state the limitation. It never silently passes an
unsupported claim through.**
Context: Pass 1 named a faithfulness self-check (motivated by the citation-hygiene findings in
D9) but never specified what happens when it fails. Given that citation integrity failed
silently during this project's own Phase 1 research process (caught only by a second review),
leaving the failure path unspecified risked the same silent-failure pattern reaching production.
Status: decided; see architecture.md §5.5.

---

**D23 — Full reasoning is attempted once >=2 of 6 domains have at least one populated field;
below that threshold, the system always asks one batched clarifying question first, using a
defined default field set when the query names no specific domain.**
Context: Pass 1 left both the minimum-information threshold and the default question content
undefined, risking either thin/ungrounded reasoning on a near-empty profile or an over-eager
clarification loop, and leaving the brief's own canonical example ("Biodiversity is declining on
my land" -> asks for SOC%, rainfall pattern, land use type) without a documented mechanism to
reproduce it for domain-less queries.
Decision: threshold = 2 of 6 domains populated; default ask set for domain-less queries = SOC%,
rainfall category, land-use type (matching the brief's example verbatim); a query naming a
specific domain narrows the ask to that domain's fields instead.
Status: decided; see architecture.md §6.

---

**D24 — The intervention knowledge base includes verified entries for the water and human-impact
domains, not only soil/land-use.**
Context: the requirements audit found the KB (research.md §1.6) contained only soil/cropping-
management interventions, even though the reasoning pipeline runs sub-assessors across all six
domains — if water or human-impact ranked as the top concern for a real user profile, there was
no KB entry to match, and no documented fallback (now provided by D20 regardless).
Decision: research and add water-scarcity and human-impact/pollution interventions at the same
verification rigor as the existing entries (research.md §1.8).
Status: decided; entries recorded in research.md §1.8.
