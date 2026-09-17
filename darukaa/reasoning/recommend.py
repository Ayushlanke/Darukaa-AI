import re
from dataclasses import dataclass

from darukaa.knowledge.ingest import is_fao_or_ipcc
from darukaa.knowledge.kb import find_matches

_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?%?")
GENERIC_PHRASES = ("use sustainable practices", "protect biodiversity", "be more sustainable")


@dataclass(frozen=True)
class Citation:
    source_name: str
    evidence_type: str
    source_url: str = ""


@dataclass(frozen=True)
class Recommendation:
    what: str
    why: str
    supporting_variables: tuple
    impacted_metrics: tuple
    time_horizon: str
    evidence: tuple
    limitations: str
    confidence: str


def _confidence_label(value: float, force_low: bool) -> str:
    if force_low:
        return "low"
    if value >= 0.7:
        return "high"
    if value >= 0.4:
        return "medium"
    return "low"


def select_top_domains(ranking: list, fired_rules) -> set:
    """architecture.md §5.4: the single top-ranked domain, unless a fired interaction rule
    links it to another populated domain, in which case use that linked set — never the
    full ranking, which would defeat top-domain preference entirely (every populated
    domain would count as "top", matching KB entries the concern doesn't actually target)."""
    if not ranking:
        return set()
    top = ranking[0]
    populated = set(ranking)
    for rule in fired_rules:
        if top in rule.linked_domains:
            return set(rule.linked_domains) & populated
    return {top}


def build_recommendation(top_domains, assessments: dict, profile):
    """Matches the top-ranked domains against the intervention KB (architecture.md §5.4).
    Returns None if no KB entry targets any of them — the caller (D20) must state that
    limitation explicitly and fall back to raw retrieved evidence, never invent or silently
    substitute a different domain."""
    matches = find_matches(set(top_domains), profile)
    if not matches:
        return None
    entry = matches[0]

    contributing_domains = [d for d in entry.domains if d in assessments]
    confidences = [assessments[d].confidence for d in contributing_domains] or [0.0]
    confidence_value = min(confidences)

    # Only the single most-relevant retrieved chunk per contributing domain is added
    # alongside the intervention's own citation — the full per-domain retrieval set
    # (up to 5-6 chunks each) is for the sub-assessment, not for one recommendation's
    # citation list; including all of it drowned the specific citation in loosely-related
    # domain-general evidence. A relevant FAO/IPCC chunk is added too if one was retrieved
    # (D21), since EvidenceStore.retrieve() deliberately appends it at the end of its list,
    # not necessarily first by relevance.
    evidence = [Citation(entry.source_name, entry.evidence_type, entry.source_url)]
    seen = {entry.source_name}
    for domain in contributing_domains:
        domain_evidence = assessments[domain].evidence
        if domain_evidence and domain_evidence[0].source_name not in seen:
            chunk = domain_evidence[0]
            evidence.append(Citation(chunk.source_name, chunk.evidence_type))
            seen.add(chunk.source_name)
        fao_ipcc_chunk = next((c for c in domain_evidence if is_fao_or_ipcc(c)), None)
        if fao_ipcc_chunk and fao_ipcc_chunk.source_name not in seen:
            evidence.append(Citation(fao_ipcc_chunk.source_name, fao_ipcc_chunk.evidence_type))
            seen.add(fao_ipcc_chunk.source_name)

    why = f"{entry.why} Evidence: {entry.effect_size}."
    return Recommendation(
        what=entry.what,
        why=why,
        supporting_variables=tuple(contributing_domains),
        impacted_metrics=entry.impacted_metrics,
        time_horizon=entry.time_horizon,
        evidence=tuple(evidence),
        limitations=entry.limitations,
        confidence=_confidence_label(confidence_value, entry.evidence_type == "non_quantifiable"),
    )


def _numbers_in(text: str) -> set:
    return set(_NUMBER_RE.findall(text))


def faithfulness_check(candidate_text: str, recommendation: Recommendation):
    """architecture.md §5.5 / D22. Targets this project's own recurring failure mode
    (fabricated or misattributed numbers, research.md's Method section): a sentence
    introducing a number absent from the recommendation's own grounded text is dropped,
    never silently passed through. Returns (safe_text, whether_anything_was_dropped)."""
    ground_truth = f"{recommendation.why} {recommendation.limitations} " + " ".join(
        c.source_name for c in recommendation.evidence
    )
    ground_numbers = _numbers_in(ground_truth)
    sentences = [s.strip() for s in candidate_text.split(".") if s.strip()]
    kept, dropped = [], False
    for sentence in sentences:
        if _numbers_in(sentence) - ground_numbers:
            dropped = True
            continue
        kept.append(sentence)
    safe_text = (". ".join(kept) + ".") if kept else recommendation.why
    return safe_text, dropped


def contains_generic_phrase(what: str, why: str) -> bool:
    """Defense-in-depth backstop (architecture.md §5.5) — the primary defense against
    genericity is the structural KB specificity/multi-domain preference in find_matches."""
    combined = f"{what} {why}".lower()
    return any(phrase in combined for phrase in GENERIC_PHRASES)
