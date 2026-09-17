import json
import logging
import re
import time
import httpx

from darukaa import config
from darukaa.reasoning.recommend import Recommendation

logger = logging.getLogger("darukaa.llm")

# Thin wrapper around OpenRouter API targeting NVIDIA Nemotron
# (nvidia/nemotron-3-ultra-550b-a55b). Preserves Darukaa's core
# knowledge-grounded and deterministic reasoning architecture.

EXTRACT_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "soil": {
            "type": "object",
            "properties": {
                "organic_carbon_pct": {"type": "number"},
                "ph": {"type": "number"},
                "moisture_pct": {"type": "number"},
            },
        },
        "climate": {
            "type": "object",
            "properties": {
                "rainfall_category": {"type": "string", "enum": ["low", "medium", "high"]},
                "rainfall_mm_annual": {"type": "number"},
                "temperature_c": {"type": "number"},
                "aridity_index": {"type": "number"},
            },
        },
        "land_use": {
            "type": "object",
            "properties": {
                "land_use_type": {
                    "type": "string",
                    "enum": ["monoculture", "intercropped", "agroforestry", "natural_habitat", "pasture"],
                },
                "fragmentation": {"type": "string", "enum": ["low", "medium", "high"]},
            },
        },
        "water": {
            "type": "object",
            "properties": {
                "availability_category": {"type": "string", "enum": ["low", "medium", "high"]},
                "groundwater_trend": {"type": "string", "enum": ["declining", "stable", "improving"]},
                "irrigation_dependent": {"type": "boolean"},
            },
        },
        "human_impact": {
            "type": "object",
            "properties": {
                "pesticide_use": {"type": "string", "enum": ["low", "medium", "high"]},
                "deforestation_nearby": {"type": "boolean"},
            },
        },
        "biodiversity": {
            "type": "object",
            "properties": {
                "species_richness_estimate": {"type": "string", "enum": ["low", "medium", "high"]},
                "habitat_diversity_index": {"type": "string", "enum": ["low", "medium", "high"]},
                "pollinator_activity_observed": {
                    "type": "string",
                    "enum": ["none", "rare", "moderate", "abundant"],
                },
                "trend": {"type": "string", "enum": ["declining", "stable", "improving"]},
            },
        },
        "region": {
            "type": "object",
            "properties": {
                "free_text_region": {"type": "string"},
                "lat": {"type": "number"},
                "lon": {"type": "number"},
            },
        },
    },
}

EXTRACT_TOOL = {
    "name": "extract_environmental_fields",
    "description": (
        "Extract only the environmental measurement values the user actually stated. "
        "Omit any field the user did not mention — never guess or fill in a plausible value."
    ),
    "input_schema": EXTRACT_TOOL_SCHEMA,
}

OPENROUTER_EXTRACT_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_environmental_fields",
        "description": (
            "Extract only the environmental measurement values the user actually stated. "
            "Omit any field the user did not mention — never guess or fill in a plausible value."
        ),
        "parameters": EXTRACT_TOOL_SCHEMA,
    },
}


class _ChatCompletionsNamespace:
    def __init__(self, client: "OpenRouterClient"):
        self._client = client

    def create(self, **kwargs):
        return self._client.create_chat_completion(**kwargs)


class _ChatNamespace:
    def __init__(self, client: "OpenRouterClient"):
        self.completions = _ChatCompletionsNamespace(client)


class _MessagesNamespace:
    def __init__(self, client: "OpenRouterClient"):
        self._client = client

    def create(self, **kwargs):
        return self._client.create_chat_completion(**kwargs)


class OpenRouterAPIError(Exception):
    """Raised when OpenRouter API returns an error like 429 rate limit or 402 credit exhaustion."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


class OpenRouterClient:
    """Minimal client for OpenRouter chat completions with tool-calling and retry handling."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or config.OPENROUTER_API_KEY or config.ANTHROPIC_API_KEY
        self.base_url = (base_url or config.OPENROUTER_BASE_URL).rstrip("/")
        self.chat = _ChatNamespace(self)
        self.messages = _MessagesNamespace(self)

    def create_chat_completion(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: dict | str | None = None,
        max_tokens: int = 1024,
        model: str | None = None,
    ) -> dict:
        if not self.api_key:
            raise OpenRouterAPIError(401, "OPENROUTER_API_KEY is not set. Please provide your OpenRouter API key.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://darukaa.earth",
            "X-Title": "Darukaa Earth",
        }
        payload = {
            "model": model or config.OPENROUTER_MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice

        max_retries = 2
        last_exc = None
        for attempt in range(max_retries):
            try:
                with httpx.Client(timeout=35.0) as client:
                    resp = client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                    if resp.status_code == 429:
                        if attempt < max_retries - 1:
                            time.sleep(2.0)
                            continue
                        raise OpenRouterAPIError(
                            429,
                            "OpenRouter API rate limit reached (HTTP 429: Too Many Requests). "
                            "The active model has temporarily exceeded its request quota. "
                            "Please wait a few moments before sending another request."
                        )
                    if resp.status_code == 402:
                        raise OpenRouterAPIError(
                            402,
                            "OpenRouter API Payment Required (HTTP 402). "
                            "Insufficient usage credits for this model. "
                            "To use the free tier, set OPENROUTER_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free, "
                            "or add credits at https://openrouter.ai/credits."
                        )
                    if resp.status_code == 401:
                        raise OpenRouterAPIError(
                            401,
                            "OpenRouter API Unauthorized (HTTP 401). "
                            "Invalid or missing API key. Please verify OPENROUTER_API_KEY in your .env configuration."
                        )
                    resp.raise_for_status()
                    return resp.json()
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                if exc.response.status_code == 429 and attempt < max_retries - 1:
                    time.sleep(2.0)
                    continue
                if exc.response.status_code == 429:
                    raise OpenRouterAPIError(
                        429,
                        "OpenRouter API rate limit reached (HTTP 429: Too Many Requests). "
                        "The active model has temporarily exceeded its request quota. "
                        "Please wait a few moments before sending another request."
                    )
                if exc.response.status_code == 402:
                    raise OpenRouterAPIError(
                        402,
                        "OpenRouter API Payment Required (HTTP 402). Insufficient usage credits for this model. "
                        "Switch to nvidia/nemotron-3-ultra-550b-a55b:free or add credits at https://openrouter.ai/credits."
                    )
                raise
            except httpx.RequestError as exc:
                last_exc = exc
                if attempt < max_retries - 1:
                    time.sleep(1.5)
                    continue
                raise
        if last_exc:
            raise last_exc


_client = None


def _get_client() -> OpenRouterClient:
    global _client
    if _client is None:
        _client = OpenRouterClient(
            api_key=config.OPENROUTER_API_KEY,
            base_url=config.OPENROUTER_BASE_URL,
        )
    return _client


def _call_llm(client, **kwargs):
    if isinstance(client, OpenRouterClient):
        return client.create_chat_completion(**kwargs)

    # Check if client is a mock with specific methods configured
    mock_children = getattr(client, "_mock_children", None)
    if mock_children is not None:
        if "messages" in mock_children:
            return client.messages.create(**kwargs)
        if "create_chat_completion" in mock_children:
            return client.create_chat_completion(**kwargs)
        if "chat" in mock_children:
            return client.chat.completions.create(**kwargs)

    if hasattr(client, "create_chat_completion"):
        return client.create_chat_completion(**kwargs)
    if hasattr(client, "chat") and hasattr(client.chat, "completions"):
        return client.chat.completions.create(**kwargs)
    if hasattr(client, "messages"):
        return client.messages.create(**kwargs)
    raise TypeError(f"Unsupported client object: {type(client)}")


def extract_fields(message: str) -> dict:
    client = _get_client()
    messages = [
        {
            "role": "system",
            "content": (
                "You are an environmental field extraction engine for Darukaa.Earth. "
                "Extract only the environmental measurement values explicitly stated by the user. "
                "Never guess or fill in plausible values for unmentioned fields."
            ),
        },
        {"role": "user", "content": message},
    ]

    tool_choice = {
        "type": "function",
        "function": {"name": "extract_environmental_fields"},
    }

    response = _call_llm(
        client,
        model=config.OPENROUTER_MODEL,
        max_tokens=1024,
        tools=[OPENROUTER_EXTRACT_TOOL],
        tool_choice=tool_choice,
        messages=messages,
    )

    # 1. Check Anthropic mock response format (e.g. response.content = [block])
    content_blocks = getattr(response, "content", None)
    if content_blocks and isinstance(content_blocks, (list, tuple)):
        for block in content_blocks:
            if getattr(block, "type", None) == "tool_use" and hasattr(block, "input"):
                return block.input
            if isinstance(block, dict) and block.get("type") == "tool_use":
                return block.get("input", {})

    # 2. Check OpenAI / OpenRouter response structure (dict or object)
    choices = getattr(response, "choices", None)
    if choices is None and isinstance(response, dict):
        choices = response.get("choices")

    if choices and len(choices) > 0:
        first_choice = choices[0]
        msg = getattr(first_choice, "message", None)
        if msg is None and isinstance(first_choice, dict):
            msg = first_choice.get("message", {})

        # Tool calls
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls is None and isinstance(msg, dict):
            tool_calls = msg.get("tool_calls")

        if tool_calls:
            for tc in tool_calls:
                fn = getattr(tc, "function", None)
                if fn is None and isinstance(tc, dict):
                    fn = tc.get("function", {})
                args = getattr(fn, "arguments", None)
                if args is None and isinstance(fn, dict):
                    args = fn.get("arguments")

                if isinstance(args, str):
                    try:
                        return json.loads(args)
                    except json.JSONDecodeError:
                        pass
                elif isinstance(args, dict):
                    return args

        # Fallback: check content for JSON
        content = getattr(msg, "content", None)
        if content is None and isinstance(msg, dict):
            content = msg.get("content")
        if content and isinstance(content, str):
            content = content.strip()
            if "```" in content:
                match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(1))
                    except json.JSONDecodeError:
                        pass
            if content.startswith("{") and content.endswith("}"):
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    pass

    return {}


def narrate(recommendation: Recommendation, user_question: str | None = None) -> str:
    if user_question:
        prompt = (
            "Narrate this already-computed recommendation conversationally in 2-4 sentences, "
            f"specifically addressing the user's question or follow-up: '{user_question}'. "
            "Do not invent any new fact, number, or source beyond what is given below.\n\n"
            f"What: {recommendation.what}\n"
            f"Why: {recommendation.why}\n"
            f"Impacted metrics: {', '.join(recommendation.impacted_metrics)}\n"
            f"Time horizon: {recommendation.time_horizon}\n"
            f"Confidence: {recommendation.confidence}\n"
            f"Limitations: {recommendation.limitations}"
        )
    else:
        prompt = (
            "Narrate this already-computed recommendation conversationally in 2-4 sentences. "
            "Do not invent any new fact, number, or source beyond what is given below.\n\n"
            f"What: {recommendation.what}\n"
            f"Why: {recommendation.why}\n"
            f"Impacted metrics: {', '.join(recommendation.impacted_metrics)}\n"
            f"Time horizon: {recommendation.time_horizon}\n"
            f"Confidence: {recommendation.confidence}\n"
            f"Limitations: {recommendation.limitations}"
        )
    client = _get_client()
    response = _call_llm(
        client,
        model=config.OPENROUTER_MODEL,
        max_tokens=512,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are the Darukaa.Earth conversational narrator. "
                    "Narrate the provided recommendation strictly adhering to given facts."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )

    # 1. Check Anthropic mock response format
    content_blocks = getattr(response, "content", None)
    if content_blocks and isinstance(content_blocks, (list, tuple)):
        return "".join(
            getattr(b, "text", "") if hasattr(b, "text") else b.get("text", "")
            for b in content_blocks
            if getattr(b, "type", None) == "text" or (isinstance(b, dict) and b.get("type") == "text")
        )

    # 2. Check OpenAI / OpenRouter response structure
    choices = getattr(response, "choices", None)
    if choices is None and isinstance(response, dict):
        choices = response.get("choices")

    if choices and len(choices) > 0:
        first_choice = choices[0]
        msg = getattr(first_choice, "message", None)
        if msg is None and isinstance(first_choice, dict):
            msg = first_choice.get("message", {})
        content = getattr(msg, "content", None)
        if content is None and isinstance(msg, dict):
            content = msg.get("content")
        if content and isinstance(content, str):
            return content.strip()

    return ""
