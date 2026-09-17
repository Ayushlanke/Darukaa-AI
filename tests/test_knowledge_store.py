from pathlib import Path

import pytest

from darukaa.knowledge.ingest import parse_research_md
from darukaa.knowledge.store import EvidenceStore

RESEARCH_MD = Path(__file__).resolve().parent.parent / "docs" / "research.md"


@pytest.fixture(scope="module")
def store():
    chunks = parse_research_md(RESEARCH_MD)
    return EvidenceStore(chunks, persist=False)


def test_retrieval_returns_correct_topic(store):
    results = store.retrieve("soil organic carbon semi-arid", topic="soil")
    assert results
    assert all(c.topic == "soil" for c in results)


def test_retrieval_finds_relevant_content(store):
    results = store.retrieve("wild bee ground nesting tillage", topic="soil")
    assert any("bee" in c.text.lower() for c in results)


def test_retrieval_empty_for_unknown_topic(store):
    assert store.retrieve("anything", topic="not_a_real_topic") == []


def test_fao_ipcc_surfaced_for_climate_topic(store):
    results = store.retrieve("drylands aridity thresholds", topic="climate")
    assert any("FAO" in c.source_name or "IPCC" in c.source_name for c in results)
