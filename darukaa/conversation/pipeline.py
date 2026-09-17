import sqlite3

from darukaa import config
from darukaa.conversation import llm, session
from darukaa.conversation.controller import (
    clarifying_question,
    merge_profile,
    missing_fields_for,
    needs_clarification,
)
from darukaa.knowledge.ingest import parse_research_md
from darukaa.knowledge.kb import init_db as init_kb_db
from darukaa.knowledge.store import EvidenceStore
from darukaa.measurements.profile import Contradiction
from darukaa.reasoning.assessor import assess_all, rank_domains
from darukaa.reasoning.interactions import apply_interactions
from darukaa.reasoning.recommend import build_recommendation, faithfulness_check, select_top_domains


def bootstrap():
    """Shared setup for both the API and the CLI (architecture.md §9 — one conversation
    core, two front ends)."""
    db = sqlite3.connect(config.DB_PATH, check_same_thread=False)
    session.init_db(db)
    init_kb_db(db)
    research_md = config.REPO_ROOT / "docs" / "research.md"
    store = EvidenceStore(parse_research_md(research_md))
    return db, store


def run_turn(
    db: sqlite3.Connection,
    store: EvidenceStore,
    session_id: str,
    updates: dict,
    named_domain=None,
    user_message: str | None = None,
) -> dict:
    profile = session.load_profile(db, session_id)
    try:
        profile = merge_profile(profile, updates)
    except Contradiction as exc:
        return {"type": "clarification", "message": str(exc)}
    session.save_profile(db, session_id, profile)

    if needs_clarification(profile):
        missing = missing_fields_for(profile, named_domain)
        message = (
            clarifying_question(missing)
            if missing
            else "Could you share a bit more about your land's conditions?"
        )
        return {"type": "clarification", "message": message}

    assessments = assess_all(profile, store)
    adjusted, fired = apply_interactions(profile, assessments)
    ranking = rank_domains(adjusted)
    top_domains = select_top_domains(ranking, fired)
    recommendation = build_recommendation(top_domains, adjusted, profile)

    if recommendation is None:
        # D20 — no silent substitution or invented recommendation.
        return {
            "type": "no_match",
            "message": (
                f"No specific intervention in our knowledge base directly targets "
                f"{ranking[0]} under these conditions."
            ),
            "top_domain": ranking[0],
        }

    why = recommendation.why
    if config.OPENROUTER_API_KEY or config.ANTHROPIC_API_KEY:
        narrated_raw = llm.narrate(recommendation, user_question=user_message)
        why, _dropped = faithfulness_check(narrated_raw, recommendation)

    return {
        "type": "recommendation",
        "what": recommendation.what,
        "why": why,
        "supporting_variables": recommendation.supporting_variables,
        "impacted_metrics": recommendation.impacted_metrics,
        "time_horizon": recommendation.time_horizon,
        "confidence": recommendation.confidence,
        "limitations": recommendation.limitations,
        "evidence": [{"source": c.source_name, "evidence_type": c.evidence_type} for c in recommendation.evidence],
        "interactions_applied": [r.description for r in fired],
    }
