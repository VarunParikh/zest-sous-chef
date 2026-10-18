"""`POST /sessions/{id}/chat` (API Spec v0.4 §4.2; FR-10, 11, 102). JSON text messages; photos are block 2.4."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Request
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from backend.api.cart import context
from backend.api.errors import ApiError
from backend.cart import service
from backend.flows.cards import Message, TurnResponse
from backend.flows import photo
from backend.flows.chat import Deps, Outcome, handle
from backend.flows.photo import sample_list
from backend.flows.templates import TEMPLATES
from backend.flows.turns import build_turn
from backend.llm.client import LLMError, OllamaClient
from backend.llm.image import MAX_BYTES, ImageRejected, prepare_image
from backend.session.levers import LeverSet

router = APIRouter(prefix="/api/v1/sessions/{session_id}")
MAX_TEXT = 2000


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field("", max_length=MAX_TEXT)
    sample_photo_id: Optional[str] = None  # FR-55: a bundled sample photo with pre-computed detections
    levers: Optional[LeverSet] = None  # API Spec v0.3, C31: compared only, never used for ranking


def _llm(request: Request, session_id: str) -> OllamaClient:
    s = request.app.state.settings
    return OllamaClient(s.ollama_base_url, s.llm_model, s.timeout_llm_s, transport=request.app.state.llm_transport,
                        tracer=request.app.state.tracer, session_id=session_id, num_ctx=s.llm_num_ctx)


def chat_deps(request: Request, session_id: str) -> Deps:
    state = request.app.state
    return Deps(guard=state.guard, llm=_llm(request, session_id), store=state.store, retriever_factory=state.get_retriever,
                ctx=context(request), tracer=state.tracer, settings=state.settings, transcripts=state.transcripts,
                vision_transport=state.llm_transport)


def _reject(status: int, code: str) -> ApiError:
    return ApiError(status, code, TEMPLATES["MSG-UPLOAD-REJECT"], "MSG-UPLOAD-REJECT")


async def _parse(request: Request) -> tuple[ChatRequest, bytes | None, bool]:
    """JSON text or sample-photo messages, or multipart with one image (API Spec §4.2; FR-57)."""
    if request.headers.get("content-type", "").startswith("multipart/form-data"):
        form = await request.form(max_files=2)
        images = form.getlist("image")
        if len(images) > 1:
            raise _reject(400, "BAD_REQUEST")
        image = None
        if images:
            data = await images[0].read(MAX_BYTES + 1)
            try:
                image = prepare_image(data)  # size and magic checks, EXIF and GPS stripped, in memory only
            except ImageRejected as e:
                raise _reject(413, "IMAGE_TOO_LARGE") if "5 MB" in str(e) else _reject(415, "UNSUPPORTED_MEDIA") from None
            finally:
                del data
        levers = form.get("levers")
        try:
            body = ChatRequest(text=str(form.get("text") or ""), levers=LeverSet.model_validate_json(levers) if levers else None)
        except ValidationError:
            raise ApiError(422, "VALIDATION_ERROR", "That request was not valid.") from None
        return body, image, str(form.get("consent", "")).lower() == "true"
    try:
        return ChatRequest.model_validate_json(await request.body()), None, False
    except ValidationError as e:
        errors = [{"loc": [str(x) for x in err.get("loc", ())], "msg": err.get("msg", "")} for err in e.errors()]
        raise ApiError(422, "VALIDATION_ERROR", "That request was not valid.", details={"errors": errors}) from None


def _turn(request: Request, session_id: str, body: ChatRequest, image: bytes | None, consent: bool) -> TurnResponse:
    session = request.app.state.sessions.get(session_id)
    if not body.text.strip() and image is None and body.sample_photo_id is None:
        raise ApiError(400, "EMPTY_MESSAGE", "Type a message first.")
    if body.sample_photo_id is not None and body.sample_photo_id not in {p["id"] for p in sample_list()}:
        raise ApiError(400, "BAD_REQUEST", "That sample photo doesn't exist.")
    state = request.app.state
    with session.busy():
        text = body.text if body.text.strip() else ("[photo]" if image is not None or body.sample_photo_id else "")
        session.messages.append(Message(message_id=session.next_message_id(), role="user", text=text))
        deps, out = chat_deps(request, session_id), Outcome()
        try:
            if image is not None:
                photo.upload_turn(session, image, consent, deps, out)
            elif body.sample_photo_id is not None:
                photo.sample_turn(session, body.sample_photo_id, deps, out)
            else:
                out = handle(session, body.text, deps)
        except LLMError:  # the text model unreachable or invalid with no template fallback left
            raise ApiError(503, "DEPENDENCY_UNAVAILABLE", TEMPLATES["MSG-SERVER"], "MSG-SERVER", retryable=True) from None
        return build_turn(session, out.messages, current_levers=body.levers, known_prices=out.known_prices,
                          cart=service.view(session.cart, state.store), cart_changed=out.cart_changed,
                          suggestions=out.suggestions, fallbacks_used=out.fallbacks)


@router.post("/chat")
async def chat(session_id: str, request: Request) -> TurnResponse:
    request.app.state.sessions.get(session_id)  # 404 before reading any upload
    body, image, consent = await _parse(request)
    return await run_in_threadpool(_turn, request, session_id, body, image, consent)


samples_router = APIRouter(prefix="/api/v1")


@samples_router.get("/samples/photos")
def samples() -> dict:
    """API Spec endpoint 13 (FR-55). Labels are assistant-written and unverified until the owner reviews them."""
    return {"photos": sample_list()}
