# Darukaa.Earth — AI Biodiversity Intelligence

![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)
![Model](https://img.shields.io/badge/LLM-NVIDIA%20Nemotron%20(OpenRouter)-green)

An AI Environmental Scientist that evaluates multi-variable land conditions (soil health, climate aridity, land use, water dynamics, human impact, biodiversity) and generates non-obvious, scientifically grounded interventions. Every recommendation is backed by peer-reviewed studies (FAO, IPBES, Plant and Soil 2023) with explicit confidence ratings, time horizons, and measurable impact metrics.

Full scientific design rationale:
- [docs/research.md](docs/research.md) — Underlying environmental science and peer-reviewed verification.
- [docs/architecture.md](docs/architecture.md) — System architecture, RAG design, and deterministic reasoning.
- [docs/decision-log.md](docs/decision-log.md) — Architectural decision records (ADRs D1–D20).
- [docs/implementation-plan.md](docs/implementation-plan.md) — Evaluation scenarios and benchmark test mapping.
- [FINDINGS.md](FINDINGS.md) — Post-implementation audit and architectural verification.

---

## 🌐 Live Demo

**🔗 [Try Darukaa Live](https://darukaa-y3yp.onrender.com)**

The latest deployed version of **Darukaa** is available for live testing:

-> **https://darukaa-y3yp.onrender.com**

> **Note:** The application is hosted on Render's free tier, which may automatically put the service to sleep after a period of inactivity. If the application has been inactive, the initial load may take a little longer while the server starts back up. Subsequent requests should load normally.

---


## 1. Architecture Overview

Darukaa combines **deterministic ecological reasoning** with **bounded conversational intelligence**:

```
                                      [User Query (Text or JSON)]
                                                   │
                       ┌───────────────────────────┴───────────────────────────┐
                       ▼                                                       ▼
            [Free-Text Chat Input]                                  [Structured Profile Input]
                       │                                                       │
                       ▼                                                       │
          NVIDIA Nemotron Extraction                                           │
         (Structured Tool-Use via OpenRouter)                                  │
                       │                                                       │
                       └───────────────────────────┬───────────────────────────┘
                                                   ▼
                                     [Conversation Controller]
                                (Memory Merge & Contradiction Check)
                                                   │
                          ┌────────────────────────┴────────────────────────┐
                          ▼                                                 ▼
             Needs Clarification (< 2 domains)                  Sufficient Data (≥ 2 domains)
                          │                                                 │
                          ▼                                                 ▼
               Targeted Diagnostic Question                     [Multi-Metric Reasoning Engine]
                                                        ┌───────────────────┴───────────────────┐
                                                        ▼                                       ▼
                                              Per-Domain Assessments                  Hybrid RAG Retrieval
                                              (Severity computation)              (Dense Chroma + Sparse BM25)
                                                        │                                       │
                                                        └───────────────────┬───────────────────┘
                                                                            ▼
                                                              [Ecological Interaction Matrix]
                                                             (Multi-variable compounding rules)
                                                                            │
                                                                            ▼
                                                               [Knowledge Base Matching]
                                                              (SQLite Interventions Table)
                                                                            │
                                                                            ▼
                                                            [NVIDIA Nemotron Narration]
                                                           (Faithfulness check vs Ground Truth)
                                                                            │
                                                                            ▼
                                                                [Structured Action Card]
```

### Why This Architecture?
- **No LLM Hallucinations in Reasoning**: The LLM never invents interventions or manipulates rankings. Field extraction and conversational narration are bounded. Ecological assessment, reciprocal rank fusion retrieval, and threshold comparisons are pure, deterministic Python.
- **Multi-Metric Non-Obvious Solutions**: Rather than single-variable answers, Darukaa evaluates how environmental variables interact (e.g., aridity compounding soil organic carbon degradation under monoculture).
- **Faithfulness Verification**: Any conversational narration produced by the LLM is subjected to a deterministic verification filter against the source intervention before reaching the user.

---

## 2. Database & Schema

### A. SQLite Database (`darukaa.db`)
Created and maintained automatically on bootstrap:
1. **`interventions`**: The structured scientific knowledge base of 12 verified ecological interventions across soil, land use, water, and biodiversity domains.
   - Schema: `id`, `name`, `domains`, `conditions` (JSON threshold criteria), `what`, `why`, `effect_size`, `time_horizon`, `evidence_type` (`established_evidence` | `reasonable_inference` | `non_quantifiable`), `source_name`, `source_url`, `limitations`.
2. **`sessions`**: `session_id TEXT PRIMARY KEY`, `profile_json TEXT`. Stores the accumulated `EnvironmentalProfile` across turns, enabling multi-turn conversation memory.

### B. Hybrid RAG Vector & Sparse Index
- **Dense Vector Store**: Persistent ChromaDB collection (`.chroma/`) indexing domain research chunks.
- **Sparse BM25 Index**: In-memory rank-bm25 index for exact keyword and biological nomenclature matching.
- **Fusion**: Merged via Reciprocal Rank Fusion (RRF) at query time.
- **Single Source of Truth**: Indexed directly from [docs/research.md](docs/research.md) finding tables at startup (`darukaa/knowledge/ingest.py`).

---

## 3. Local Setup & Installation

### Prerequisites
- Python 3.10, 3.11, or 3.12+ (tested through Python 3.14)
- macOS, Linux, or Windows WSL

### Installation Steps

```bash
# 1. Clone repository
git clone https://github.com/Ayushlanke/Darukaa-AI.git
cd Darukaa-AI

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate       # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify test suite (Runs 100% offline, no API key required)
PYTHONPATH=. pytest -v
```

All 49 unit, scenario, and integration tests pass out-of-the-box.

---

## 4. Environment Configuration (`.env`)

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Contents of `.env`:
```env
# OpenRouter API Key (Required for live natural language extraction & narration)
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Target Model Selection:
# Free Tier Accounts (Zero cost, 50 requests/day):
OPENROUTER_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free

# Paid Accounts (With purchased credits):
# OPENROUTER_MODEL=nvidia/nemotron-3-ultra-550b-a55b

# OpenRouter Gateway
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

---

## 5. Usage & Interaction Modes

### Method A: Web Chat Interface (Recommended)
Start the FastAPI application:

```bash
uvicorn darukaa.api.main:app --reload
```

Open your browser at:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

Features:
- **ChatGPT-Style Layout**: Sidebar with consultation history, "+ New Consultation" button, and model indicators.
- **In-Stream Reasoning Animation**: Live typing indicator with real-time status as NVIDIA Nemotron extracts parameters and searches the knowledge base.
- **Multi-Turn Follow-Ups**: Ask follow-up questions (e.g. *"How do I manage this during dry spells?"*); Darukaa maintains state and answers conversationally while preserving scientific grounding.
- **Pre-Loaded Benchmark Chips**: 1-click test buttons for the hackathon challenge prompt, incomplete queries, and acidic soil cases.

---

### Method B: Interactive OpenAPI Swagger Docs
Navigate to:
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

Pre-configured endpoints:
- `POST /chat`: Natural language queries (extracts measurements and narrates via Nemotron).
- `POST /profile`: Structured JSON input (bypasses LLM, 100% offline).
- `GET /health`: System liveness check.

Example `curl` request:
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_1",
    "message": "My soil organic carbon is 0.3%, annual rainfall is low, and the land use is monoculture."
  }'
```

---

### Method C: Terminal Interactive CLI
For direct command-line interaction without a browser:

```bash
python -m darukaa.api.cli
```

---

## 6. CI/CD Details

Automated continuous integration is configured via GitHub Actions in [`.github/workflows/ci.yml`](.github/workflows/ci.yml):
- **Triggers**: On every push and pull request to `main` / `master`.
- **Steps**:
  1. Checks out repository.
  2. Sets up Python 3.11 environment with pip caching.
  3. Installs dependencies from `requirements.txt`.
  4. Runs complete pytest test suite (`PYTHONPATH=. pytest -v`).
  5. Validates zero regressions across all 49 test cases.

---

### Key Verification Notes for Reviewers
1. **Benchmark Scenario**:
   - **Input**: Soil carbon: 0.3%, Rainfall: low, Land use: monoculture wheat.
   - **Output**: Identifies aridity compounding soil degradation; matches *temporary wheat-vetch intercropping* with 37% microbial biomass carbon increase; surfaces FAO, IPBES, and Plant and Soil (2023) citations; notes single-trial boundary conditions.
2. **Deterministic Fallbacks**: Without an API key, the system safely executes all reasoning, clarification, and structured `/profile` turns fully offline without failing.
