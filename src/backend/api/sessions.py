"""Lever config and session routes (API Spec §3 endpoints 2 to 4, §4.1; FR-01, 04, 05, 06)."""
from __future__ import annotations

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, ConfigDict

from backend.catalogue.seed import load_personas
from backend.engine.scoring import effective_weights
from backend.flows.cards import TurnResponse
from backend.flows.greeting import greeting_turn
from backend.session.levers import LEVER_OPTIONS, LeverSet, merge_levers, persona_summary, persona_tag

router = APIRouter(prefix="/api/v1")


class CreateSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    levers: LeverSet = LeverSet()


class CreateSessionResponse(BaseModel):
    session_id: str
    snapshot_hash: str
    persona_label: str
    turn: TurnResponse


def load_presets() -> dict[str, LeverSet]:
    data = load_personas()
    return {p["name"]: LeverSet.model_validate(merge_levers(data["defaults"], p["levers"])) for p in data["personas"]}


def _ranges(model: type[BaseModel], prefix: str = "") -> dict[str, dict]:
    """Numeric ranges read from the field constraints, so the panel and validation never disagree."""
    out: dict[str, dict] = {}
    for name, f in model.model_fields.items():
        sub = f.annotation
        if isinstance(sub, type) and issubclass(sub, BaseModel):
            out.update(_ranges(sub, f"{prefix}{name}."))
            continue
        bounds = {}
        for m in f.metadata:
            if getattr(m, "ge", None) is not None:
                bounds["min"] = m.ge
            if getattr(m, "le", None) is not None:
                bounds["max"] = m.le
        if bounds:
            out[prefix + name] = bounds
    return out


@router.get("/config/levers")
def config_levers(request: Request) -> dict:
    presets = request.app.state.presets
    return {
        "defaults": LeverSet().model_dump(mode="json"),
        "options": {k: list(v) for k, v in LEVER_OPTIONS.items()},
        "ranges": _ranges(LeverSet),
        "default_shares": effective_weights(LeverSet().weights)[0],  # FR-08, FR-104
        "presets": [{"name": n, "levers": p.model_dump(mode="json"), "summary": persona_summary(p), "tag": persona_tag(n)}
                    for n, p in presets.items()],  # FR-121: summary and tag generated from the levers
    }


@router.post("/sessions", status_code=201)
def create_session(body: CreateSessionRequest, request: Request) -> CreateSessionResponse:
    session = request.app.state.sessions.create(body.levers)
    return CreateSessionResponse(session_id=session.session_id, snapshot_hash=session.snapshot_hash,
                                 persona_label=session.persona_label, turn=greeting_turn(session))


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(session_id: str, request: Request) -> Response:
    request.app.state.sessions.delete(session_id)
    return Response(status_code=204)
