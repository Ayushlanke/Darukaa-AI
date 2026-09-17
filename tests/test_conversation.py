import sqlite3
from unittest.mock import MagicMock, patch

from darukaa.conversation import llm, session
from darukaa.conversation.controller import (
    clarifying_question,
    detect_named_domain,
    merge_profile,
    missing_fields_for,
    needs_clarification,
)
from darukaa.measurements.profile import Category, Contradiction, EnvironmentalProfile


def test_domain_less_query_asks_default_field_set_matching_pdf_example():
    profile = EnvironmentalProfile()
    domain = detect_named_domain("Biodiversity is declining on my land")
    missing = missing_fields_for(profile, domain)
    question = clarifying_question(missing)
    assert question == "Can you provide soil organic carbon %, rainfall pattern, land use type?"


def test_domain_specific_query_narrows_to_that_domain():
    profile = EnvironmentalProfile()
    domain = detect_named_domain("my soil seems degraded")
    assert domain == "soil"
    missing = missing_fields_for(profile, domain)
    assert missing == ("soil.organic_carbon_pct", "soil.ph", "soil.moisture_pct")


def test_needs_clarification_below_threshold():
    profile = merge_profile(EnvironmentalProfile(), {"soil": {"organic_carbon_pct": 0.3}})
    assert needs_clarification(profile) is True


def test_no_clarification_needed_at_threshold():
    profile = merge_profile(
        EnvironmentalProfile(),
        {"soil": {"organic_carbon_pct": 0.3}, "climate": {"rainfall_category": "low"}},
    )
    assert needs_clarification(profile) is False


def test_merge_updates_incrementally_without_losing_prior_fields():
    profile = merge_profile(EnvironmentalProfile(), {"soil": {"organic_carbon_pct": 0.3}})
    profile = merge_profile(profile, {"climate": {"rainfall_category": "low"}})
    assert profile.soil.organic_carbon_pct == 0.3
    assert profile.climate.rainfall_category == Category.LOW


def test_merge_surfaces_contradiction():
    profile = merge_profile(EnvironmentalProfile(), {"climate": {"rainfall_category": "high"}})
    try:
        merge_profile(profile, {"climate": {"aridity_index": 0.8}})
        assert False, "expected Contradiction"
    except Contradiction:
        pass


def test_session_round_trip():
    conn = sqlite3.connect(":memory:")
    session.init_db(conn)
    profile = merge_profile(EnvironmentalProfile(), {"soil": {"organic_carbon_pct": 0.3}})
    session.save_profile(conn, "s1", profile)
    loaded = session.load_profile(conn, "s1")
    assert loaded.soil.organic_carbon_pct == 0.3


def test_session_returns_empty_profile_for_unknown_session():
    conn = sqlite3.connect(":memory:")
    session.init_db(conn)
    assert session.load_profile(conn, "unknown").populated_domains() == []


def test_extract_fields_calls_anthropic_tool_use_and_returns_input():
    # 1. Test OpenRouter tool_calls response format
    fake_tool_call = {
        "type": "function",
        "function": {
            "name": "extract_environmental_fields",
            "arguments": '{"soil": {"organic_carbon_pct": 0.3}}',
        },
    }
    fake_openrouter_response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [fake_tool_call],
                }
            }
        ]
    }
    with patch.object(llm, "_get_client") as get_client:
        get_client.return_value.create_chat_completion.return_value = fake_openrouter_response
        result = llm.extract_fields("my soil organic carbon is 0.3%")
    assert result == {"soil": {"organic_carbon_pct": 0.3}}

    # 2. Test backward-compatibility with Anthropic mock content format
    fake_block = MagicMock()
    fake_block.type = "tool_use"
    fake_block.input = {"soil": {"organic_carbon_pct": 0.3}}
    fake_response = MagicMock(content=[fake_block])
    with patch.object(llm, "_get_client") as get_client:
        get_client.return_value.messages.create.return_value = fake_response
        result = llm.extract_fields("my soil organic carbon is 0.3%")
    assert result == {"soil": {"organic_carbon_pct": 0.3}}
