"""`POST /sessions/{id}/chat` (API Spec v0.4 §4.2; FR-10, 11, 102). JSON text messages; photos are block 2.4."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field

from backend.api.cart import context
from backend.api.errors import ApiError
from backend.cart import service
from backend.flows.cards import Message, TurnResponse
from backend.flows.chat import Deps, handle
from backend.flows.templates import TEMPLATES
from backend.flows.turns import build_turn
from backend.llm.client import LLMError, LLMInvalid, OllamaClient
from backend.session.levers import LeverSet

router = APIRouter(prefix="/api/v1/sessions/{session_id}")
MAX_TEXT = 2000


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(max_length=MAX_TEXT)
    levers: Optional[LeverSet] = None  # API Spec v0.3, C31: compared only, never used for ranking


def _llm(request: Request, session_id: str) -> OllamaClient:
    s = request.app.state.settings
    return OllamaClient(s.ollama_base_url, s.llm_model, s.timeout_llm_s, transport=request.app.state.llm_transport,
                        tracer=request.app.state.tracer, session_id=session_id, num_ctx=s.llm_num_ctx)


def chat_deps(request: Request, session_id: str) -> Deps:
    state = request.app.state
    return Deps(guard=state.guard, llm=_llm(request, session_id), store=state.store, retriever_factory=state.get_retriever,
                ctx=context(request), tracer=state.tracer, settings=state.settings)


@router.post("/chat")
def chat(session_id: str, body: ChatRequest, request: Request) -> TurnResponse:
    session = request.app.state.sessions.get(session_id)
    if not body.text.strip():
        raise ApiError(400, "EMPTY_MESSAGE", "Type a message first.")
    state = request.app.state
    with session.busy():
        session.messages.append(Message(message_id=session.next_message_id(), role="user", text=body.text))
        deps = chat_deps(request, session_id)
        try:
            out = handle(session, body.text, deps)
        except LLMInvalid:  # an invalid reply after the retry with no template fallback left
            raise ApiError(503, "DEPENDENCY_UNAVAILABLE", TEMPLATES["MSG-SERVER"], "MSG-SERVER", retryable=True) from None
        except LLMError:
            raise ApiError(503, "DEPENDENCY_UNAVAILABLE", TEMPLATES["MSG-SERVER"], "MSG-SERVER", retryable=True) from None
        return build_turn(session, out.messages, current_levers=body.levers, known_prices=out.known_prices,
                          cart=service.view(session.cart, state.store), cart_changed=out.cart_changed,
                          suggestions=out.suggestions, fallbacks_used=out.fallbacks)
