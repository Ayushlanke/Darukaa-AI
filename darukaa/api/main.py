import httpx
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from darukaa import config
from darukaa.api.ui import HTML_PAGE
from darukaa.conversation import llm, pipeline
from darukaa.conversation.controller import detect_named_domain

app = FastAPI(
    title="Darukaa.Earth AI Biodiversity Intelligence",
    description="Scientific ecological reasoning engine combining soil, climate, land use, and biodiversity metrics with NVIDIA Nemotron on OpenRouter.",
    version="1.0.0",
)
_db, _store = pipeline.bootstrap()


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        description="Free-text query or environmental condition statement",
        json_schema_extra={"example": "My soil organic carbon is 0.3%, annual rainfall is low, and the land use is monoculture."},
    )
    session_id: str = Field(
        default="default",
        description="Session identifier for multi-turn conversational memory",
        json_schema_extra={"example": "session_1"},
    )


class ProfileRequest(BaseModel):
    profile: dict = Field(
        ...,
        description="Structured environmental profile measurements",
        json_schema_extra={
            "example": {
                "soil": {"organic_carbon_pct": 0.3},
                "climate": {"rainfall_category": "low"},
                "land_use": {"land_use_type": "monoculture"},
            }
        },
    )
    session_id: str = Field(
        default="default",
        description="Session identifier for multi-turn conversational memory",
        json_schema_extra={"example": "session_1"},
    )


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    """Polished conversational web interface for Darukaa.Earth."""
    return HTMLResponse(content=HTML_PAGE)


@app.get("/ui", response_class=HTMLResponse)
def ui() -> HTMLResponse:
    """Alternative route to access the web chat interface."""
    return HTMLResponse(content=HTML_PAGE)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat")
def chat(req: ChatRequest) -> dict:
    """Text input (mandatory) — extraction uses NVIDIA Nemotron via OpenRouter;
    without an API key, the deterministic clarifying-question path runs offline."""
    session_id = req.session_id.strip() if (req.session_id and req.session_id.strip()) else "default"
    try:
        updates = llm.extract_fields(req.message) if (config.OPENROUTER_API_KEY or config.ANTHROPIC_API_KEY) else {}
        named_domain = detect_named_domain(req.message)
        return pipeline.run_turn(_db, _store, session_id, updates, named_domain, user_message=req.message)
    except llm.OpenRouterAPIError as exc:
        return {
            "type": "error",
            "action": "error",
            "status_code": exc.status_code,
            "message": exc.message,
            "session_id": session_id,
        }
    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code if exc.response is not None else 500
        if code == 429:
            msg = (
                "OpenRouter API Rate Limit Reached (HTTP 429: Too Many Requests). "
                "The active model has temporarily exceeded its request quota. "
                "Please wait a few moments before sending another request."
            )
        elif code == 402:
            msg = (
                "OpenRouter API Payment Required (HTTP 402). Insufficient usage credits for this model. "
                "To use the free tier, configure OPENROUTER_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free, "
                "or add credits at https://openrouter.ai/credits."
            )
        elif code == 401:
            msg = "OpenRouter API Unauthorized (HTTP 401). Invalid API key. Please check OPENROUTER_API_KEY in your configuration."
        else:
            msg = f"OpenRouter API error (HTTP {code}). Please verify your network and credentials."
        return {
            "type": "error",
            "action": "error",
            "status_code": code,
            "message": msg,
            "session_id": session_id,
        }


@app.post("/profile")
def submit_profile(req: ProfileRequest) -> dict:
    """Structured JSON input (mandatory) — works fully offline, no LLM call needed."""
    session_id = req.session_id.strip() if (req.session_id and req.session_id.strip()) else "default"
    try:
        return pipeline.run_turn(_db, _store, session_id, req.profile)
    except Exception as exc:
        return {
            "action": "error",
            "message": str(exc),
            "session_id": session_id,
        }
