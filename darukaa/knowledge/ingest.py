import re
from dataclasses import dataclass
from pathlib import Path

SECTION_TOPIC = {
    "1.1": "soil",
    "1.2": "land_use",
    "1.3": "climate",
    "1.4": "water",
    "1.5": "human_impact",
    "1.6": "soil",
    "1.7": "biodiversity",
}

# research.md §1.8 is the one section that mixes two domains in a single table (rows 1-5 water,
# rows 6-8 human_impact) — an explicit, documented exception rather than general multi-topic
# table parsing, since it is the only section shaped this way.
SECTION_1_8_TOPIC_BY_ROW = {1: "water", 2: "water", 3: "water", 4: "water", 5: "water",
                            6: "human_impact", 7: "human_impact", 8: "human_impact"}

_SECTION_RE = re.compile(r"^### (\d\.\d+)\s")
_ROW_RE = re.compile(r"^\|\s*(\d+)\s*\|(.+)\|([^|]+)\|([^|]+)\|\s*$")
_EVIDENCE_TYPES = {"established_evidence", "reasonable_inference", "engineering_assumption", "non_quantifiable"}
_MARKDOWN_RE = re.compile(r"\*\*|\*|~~|`")


@dataclass(frozen=True)
class Chunk:
    id: str
    text: str
    topic: str
    evidence_type: str
    source_name: str
    section: str


def _clean(text: str) -> str:
    return _MARKDOWN_RE.sub("", text).strip()


def parse_research_md(path: Path) -> list:
    """Builds the evidence corpus directly from research.md's own finding tables (Part 1),
    so the corpus and the research record can never drift apart. Skips rejected rows
    (evidence_type contains "rejected") since those are corrections, not citable evidence."""
    section = None
    chunks = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## Part 2"):
            break
        section_match = _SECTION_RE.match(line)
        if section_match:
            section = section_match.group(1)
            continue
        if section not in SECTION_TOPIC:
            continue
        row_match = _ROW_RE.match(line)
        if not row_match:
            continue
        row_num, claim, evidence_type, source = (g.strip() for g in row_match.groups())
        if evidence_type not in _EVIDENCE_TYPES:
            continue
        topic = SECTION_1_8_TOPIC_BY_ROW[int(row_num)] if section == "1.8" else SECTION_TOPIC[section]
        chunks.append(
            Chunk(
                id=f"{section}.{row_num}",
                text=_clean(claim),
                topic=topic,
                evidence_type=evidence_type,
                source_name=_clean(source),
                section=section,
            )
        )
    return chunks


def indexed_text(chunk: Chunk) -> str:
    """Deterministic per-chunk context template (architecture.md §4 step 3, D11) — no LLM call."""
    return f"Source: {chunk.source_name}. Topic: {chunk.topic}. {chunk.text}"


def is_fao_or_ipcc(chunk: Chunk) -> bool:
    return "FAO" in chunk.source_name or "IPCC" in chunk.source_name
