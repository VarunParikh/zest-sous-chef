# API Spec: Zest AI Sous-Chef

Status: **APPROVED v0.5 (owner re-approved 2026-10-18) (2026-10-18): C37 doc-sync to ADR-003 v3 (local `qwen3-vl:4b-instruct` default, Gemini opt-in, samples for the demo and as fallback). ** v0.4 was APPROVED (owner, 2026-10-18): §3 endpoints 7 to 10 return the cart and endpoint 8 has a defined body; §4.6 lines gain `in_stock` and `quantity`; §4.7 OUT_OF_STOCK details carry substitutions (C34, C35). v0.3: §4.2 to §4.4 add the optional current `levers` and `levers_changed_since_snapshot` (C31). v0.2 was APPROVED (owner, 2026-10-18), re-approved after the C15 sync to the ADR-003 Day-1 decision. v0.1 was APPROVED (owner, 2026-10-17) · Date: 2026-10-17 · Source: PRD v0.3, Architecture v0.1, Data Model v0.1, Conversation Design v0.1
Scope: the browser-to-backend REST contract, the response card types, errors, and the outbound contracts to the model, the opt-in Gemini photo provider and the transcript source. **Webhooks:** none. The app is a browser client with no inbound callbacks; there are no outbound webhooks. The live contract is the OpenAPI document that FastAPI generates from the Pydantic models in the Data Model; this document is the design that those models must satisfy.

## 1. Design decisions (owner delegated the API style, 2026-10-17)
| Decision | Choice | Reason |
|---|---|---|
| Style | **Hybrid.** `POST /chat` for anything that needs language or photo understanding; `POST /action` for button taps; resource endpoints for the cart | Language goes through guard, intent and flows in one place. Taps (swap, Undo, Yes/No) are deterministic and must not go through the model or guard. Cart edits are plain resources |
| One response shape | `/chat` and `/action` return the same `TurnResponse` | The frontend renders one structure |
| Replies | **Whole, not streamed** (owner decision) with a typing indicator | Short templated copy; simpler to test; less overhead |
| Auth | None. The `session_id` in the path scopes everything | No accounts (non-goal). CORS allows only localhost origins |
| Levers | The client keeps the current levers and sends them at session creation; the server stores only the immutable snapshot | Matches FR-01 and FR-02; no server-side lever state to desynchronise |
| Versioning | Prefix `/api/v1` | Cheap insurance |

## 2. Conventions
- JSON over HTTP; `Content-Type: application/json`, except photo upload (`multipart/form-data`).
- Times are ISO 8601 UTC. Money is a whole-rupee integer named `*_inr`.
- IDs are opaque strings.
- Every response carries `X-Request-Id` for trace correlation.
- Per-session mutual exclusion: while a turn is being processed, another `/chat`, `/action` or cart-mutating call for that session returns `409 SESSION_BUSY` (FR-102).
- Server-side turn deadline 60 s; individual calls use NFR-10 timeouts.

## 3. Endpoints
| # | Method and path | Purpose | Requirements |
|---|---|---|---|
| 1 | `GET /api/v1/health` | Dependency status for the health page | NFR-02 |
| 2 | `GET /api/v1/config/levers` | Defaults, option lists and ranges for the lever panel; persona presets | FR-05, 06 |
| 3 | `POST /api/v1/sessions` | Create a session with a lever snapshot; returns the greeting turn | FR-01, 03 |
| 4 | `DELETE /api/v1/sessions/{id}` | Discard a session (Clear chat discards, then creates anew) | FR-04 |
| 5 | `POST /api/v1/sessions/{id}/chat` | Send a user message (text, or text plus image, or a sample photo id) | FR-10 to 57 |
| 6 | `POST /api/v1/sessions/{id}/action` | Send a button tap (swap, undo, answer, confirm, add-on, variant) | FR-41, 64, 76, 77, 114 |
| 7 | `GET /api/v1/sessions/{id}/cart` | Read the cart | FR-72 |
| 8 | `PATCH /api/v1/sessions/{id}/cart/lines/{line_id}` | Change quantity (1 to 9) or switch variant: body `{"quantity": n}` or `{"variant_id": id}` (v0.4) | FR-74, 114 |
| 9 | `DELETE /api/v1/sessions/{id}/cart/lines/{line_id}` | Remove a line | FR-74 |
| 10 | `DELETE /api/v1/sessions/{id}/cart/dishes/{cart_dish_id}` | Remove a dish | FR-74 |
| 11 | `POST /api/v1/sessions/{id}/checkout` | Buy Now (requires `Idempotency-Key` header) | FR-80, 81, 83 |
| 12 | `GET /api/v1/sessions/{id}/inspector` | Retrieval and scoring detail for the latest suggestions | FR-63, 115 |
| 13 | `GET /api/v1/samples/photos` | Bundled sample photos with labels | FR-55 |
| 14 | `POST /api/v1/demo/stock-scenario/{scenario_id}` | Apply a scripted stock change | UJ10, UJ22 |
| 15 | `PUT /api/v1/demo/context` | Override time and weather label | FR-67 |
Endpoints 7 to 10 return the cart (section 4.6) (v0.4). Endpoints 14 and 15 exist only when `DEMO_CONTROLS=true` (default false) and return `404` otherwise.

## 4. Key request and response shapes

### 4.1 `POST /sessions`
Request: `{ "levers": LeverSet }` (omitted fields take defaults; values validated against the ranges).
Response `201`:
```json
{
  "session_id": "s_8f3a",
  "snapshot_hash": "b41c9e",
  "persona_label": "Custom",
  "turn": {
    "turn_id": "t_0001",
    "messages": [
      {"message_id": "m_1", "role": "assistant", "template_id": "MSG-GREET",
       "text": "Hey there! I'm Zest, your AI cooking assistant. Paste a YouTube recipe link, describe what's in your fridge, or upload a photo of your ingredients to start!",
       "cards": [{"type": "starter_chips", "chips": ["YouTube link", "Upload photo", "Text recipe", "Feeling hungry"]}]}
    ],
    "cart": {"dishes": [], "item_count": 0, "subtotal_inr": 0},
    "cart_changed": false,
    "pending": null,
    "suggestions": [],
    "notices": []
  }
}
```
Errors: `422 INVALID_LEVERS` (field out of range or unknown option).

### 4.2 `POST /sessions/{id}/chat`
JSON request: `{ "text": "I am feeling indulgent" }`
Multipart request: parts `text` (optional), `image` (JPEG, PNG or WebP, at most 5 MB), `consent` (`true` after the notice).
Sample photo request: `{ "text": "", "sample_photo_id": "sp_03" }`
Optional in every form (v0.3, C31): `"levers": LeverSet`, the lever panel's current values (a multipart request sends it as a JSON string part). The server only compares them with the session snapshot to set `levers_changed_since_snapshot` (FR-03); it never stores them and never uses them for ranking (FR-02).
Response `200`: a `TurnResponse` (section 4.4).

### 4.3 `POST /sessions/{id}/action`
```json
{ "type": "swap", "ref_message_id": "m_7", "payload": {"suggestion_id": "sg_12", "alt_dish_id": "shahi_paneer"} }
```
| `type` | Payload | Notes |
|---|---|---|
| `swap` | `suggestion_id`, `alt_dish_id` | Replaces only the dish added by that suggestion (FR-41) |
| `undo` | `suggestion_id` | Reverses that suggestion's cart change |
| `answer` | `question_id`, `choice` | Answers a clarifying question or Yes/No |
| `confirm` | `confirm_id`, `choice` (`replace`, `add`, `cancel`, `yes`, `no`) | Replace-or-add, Clear chat with cart |
| `add_on` | `suggestion_id`, `choice` (`add`, `decline`) | Add-ons are added only on `add` (FR-64) |
| `substitute` | `substitution_id`, `choice` (`accept`, `decline`) | FR-76 |
| `consent_photo` | `choice` | Records the photo notice response for the session |
Stale references return `409 STALE_ACTION`. The body may also carry the optional current `levers` (as in section 4.2, C31).

### 4.4 `TurnResponse`
```json
{
  "turn_id": "t_0007",
  "messages": [
    {
      "message_id": "m_14",
      "role": "assistant",
      "template_id": "MSG-MOOD-ADD",
      "text": "Feeling indulgent? Let's go with Butter Chicken: rich, creamy and a weekend favourite. I've added the ingredients. ✅",
      "cards": [
        {"type": "dish_added", "suggestion_id": "sg_12", "dish_id": "butter_chicken", "dish_name": "Butter Chicken",
         "reason": "Rich, creamy and a weekend favourite", "line_count": 9, "dish_total_inr": 412},
        {"type": "swap_options", "suggestion_id": "sg_12",
         "options": [{"dish_id": "shahi_paneer", "name": "Shahi Paneer"}, {"dish_id": "gajar_halwa", "name": "Gajar Halwa"}]},
        {"type": "undo", "suggestion_id": "sg_12"},
        {"type": "why_this", "suggestion_id": "sg_12"}
      ]
    }
  ],
  "cart": {"dishes": [], "item_count": 9, "subtotal_inr": 412},
  "cart_changed": true,
  "pending": null,
  "suggestions": [{"suggestion_id": "sg_12", "type": "dish", "candidate_id": "butter_chicken", "rank": 1}],
  "notices": [],
  "fallbacks_used": [],
  "levers_changed_since_snapshot": false
}
```
`levers_changed_since_snapshot` (v0.3, C31) is true when the request carried `levers` that differ from the session snapshot, and false when they match or were omitted; the UI then shows MSG-LEVER-BANNER (FR-03).
The dish total and prices are examples; real values come from the catalogue. `cart` is the full cart snapshot, so the client never reconstructs it.

### 4.5 Card types (a discriminated union on `type`)
| `type` | Fields | Used by |
|---|---|---|
| `starter_chips` | `chips[]` | greeting |
| `dish_added` | `suggestion_id`, `dish_id`, `dish_name`, `reason`, `line_count`, `dish_total_inr` | MSG-MOOD-ADD, MSG-PHOTO-OK, MSG-YT-OK |
| `swap_options` | `suggestion_id`, `options[]` (max 2) | mood, photo |
| `undo` | `suggestion_id` | any cart-adding suggestion |
| `why_this` | `suggestion_id` (breakdown fetched from the inspector or embedded when small) | FR-63 |
| `clarify` | `question_id`, `prompt`, `options[]` | MSG-AMBIG, pantry question |
| `confirm` | `confirm_id`, `prompt`, `options[]` | MSG-CLEAR-CONFIRM, MSG-CHAT-CLEAR-CONFIRM |
| `addon_suggestion` | `suggestion_id`, `item` (name, variant, price_inr), `reason` | FR-64 |
| `substitution` | `substitution_id`, `from_item`, `to_item`, `price_delta_inr`, `flavour_note` | FR-76 |
| `photo_consent` | `notice` | MSG-PHOTO-CONSENT |
| `sample_photos` | `photos[]` (id, caption, label "Sample") | FR-55 |
| `notice` | `level` (`info`, `warning`), `template_id`, `text` | persona warnings, lever banner |
| `cart_summary` | `item_count`, `subtotal_inr` | confirmations |

### 4.6 Cart
```json
{
  "dishes": [{
    "cart_dish_id": "cd_1", "dish_id": "paneer_butter_masala", "name": "Paneer Butter Masala", "dish_total_inr": 331,
    "lines": [{
      "line_id": "l_1", "ingredient_name": "butter", "variant_id": "butter-salted-100",
      "variant_name": "Salted Butter", "packs": [{"sku_id": "butter-salted-100-100g", "count": 1, "pack": "100 g"}],
      "price_inr": 58, "priced": true, "shared_from_line_id": null, "estimated": false,
      "reason": "Chosen for your history preference", "alternative_variant_ids": ["butter-unsalted-100"],
      "in_stock": true, "quantity": 1
    }]
  }],
  "item_count": 11, "subtotal_inr": 331
}
```
Dimmed shared lines carry `"priced": false` and `"shared_from_line_id"`. `in_stock` is false for a line kept with the stock filter off, or one that went out of stock after carting; Buy Now is then blocked (FR-83). `quantity` multiplies the packs a priced line owns (1 to 9, C35) (v0.4, C34). Prices and totals are always catalogue values (FR-79).

### 4.7 `POST /sessions/{id}/checkout`
Header: `Idempotency-Key: <uuid>`. Response `200`:
```json
{ "order_id": "o_3c1", "subtotal_inr": 331, "placed_at": "2026-10-17T10:15:00Z",
  "message": {"template_id": "MSG-ORDER", "text": "Order is placed, the rider will see you in 10 mins"},
  "collapse_after_s": 10 }
```
A repeated key returns the same order (no second order, FR-80). Errors: `409 OUT_OF_STOCK` (details `{"line_ids": [...], "substitutions": [substitution cards]}`, one card per blocked line that has an in-stock alternative, accepted with the `substitute` action; v0.4, C34; FR-76, 83), `409 PRICE_CHANGED` (updated cart returned), `400 EMPTY_CART`.

### 4.8 `GET /sessions/{id}/inspector`
For each of the latest suggestions: the pool with `lexical_rank`, `vector_rank`, `vector_distance`, `fused_rank`, `eligible`, `filtered_by`, the four component scores, `weights_effective`, `value_term` (variants) and `final` (FR-115).

## 5. Errors
Envelope: `{ "error": { "code": "...", "template_id": "MSG-...", "user_message": "...", "retryable": true, "details": {} } }`
| HTTP | `code` | When | UI behaviour |
|---|---|---|---|
| 400 | `EMPTY_MESSAGE`, `EMPTY_CART`, `BAD_REQUEST` | Invalid input | Inline message |
| 404 | `SESSION_NOT_FOUND` | Unknown or expired session | Start a new session |
| 409 | `SESSION_BUSY` | Another turn in progress | Input stays locked |
| 409 | `STALE_ACTION` | Tap refers to an old suggestion | Ignore; refresh state |
| 409 | `OUT_OF_STOCK`, `PRICE_CHANGED` | Checkout revalidation | Show blocking lines |
| 413 | `IMAGE_TOO_LARGE` | Over 5 MB | MSG-UPLOAD-REJECT |
| 415 | `UNSUPPORTED_MEDIA` | Not JPEG, PNG or WebP | MSG-UPLOAD-REJECT |
| 422 | `INVALID_LEVERS`, `VALIDATION_ERROR` | Schema or range failure | Inline message |
| 503 | `DEPENDENCY_UNAVAILABLE` | Model, Gemini or similar failed after retry and no fallback applied | MSG-SERVER |
| 500 | `INTERNAL` | Unexpected | MSG-SERVER |
Dependency failures with a defined fallback (Gemini to samples, transcript to fixture, vector to lexical) return `200` with `fallbacks_used` populated and the fallback message, not an error.

## 6. Outbound integration contracts

### 6.1 Local model (Ollama)
Chat call with `temperature: 0`, JSON mode or schema-constrained output, one retry, timeout from config. Output types (all Pydantic-validated; invalid output is retried once, then MSG-REPHRASE):
```json
{ "IntentResult": {"intent": "mood_intent", "confidence": 0.91, "mood_tags": ["indulgent"], "servings": null} }
```
```json
{ "ExtractionResult": {"dish_name": "Paneer Butter Masala", "servings": 2,
  "ingredients": [{"name": "paneer", "qty": 250, "unit": "g", "estimated": false},
                  {"name": "kothmir", "qty": null, "unit": null, "estimated": true}]} }
```
The model never returns SKUs, prices or stock. Prompts and few-shot examples are specified in the Agent Design.

### 6.2 Vision provider (photos only)
Default `ollama` with `qwen3-vl:4b-instruct` (ADR-003 v3, 2026-10-18): input is the stripped image bytes and a fixed instruction, sent to the local Ollama only, timeout `TIMEOUT_VISION_S` (60 s). Opt-in `gemini`: the same input; the key travels only in the `x-goog-api-key` header. `samples`: returns the pre-computed `DetectionResult` of a bundled sample photo, labelled as a sample (the demo path and the fallback). Output for all three:
```json
{ "DetectionResult": {"items": [{"name": "paneer", "confidence": 0.93}, {"name": "capsicum", "confidence": 0.81}], "scene_is_food": true, "quality": "ok"} }
```
`quality` is `ok`, `dark` or `blurry`. Bytes are never written to disk and never logged. The model name is read from config; the actual name served is recorded in the health check, not assumed.

### 6.3 Transcript source
`fetch_transcript(video_id)` returns `{ "source": "live|fixture|title_description", "text": "...", "title": "...", "description": "..." }` or raises `TranscriptUnavailable`. The chain and timeouts are in the Architecture.

## 7. Security notes for the API
CORS restricted to localhost origins; request body limit 6 MB; image content-type and magic-byte checks; no secrets or stack traces in responses; `X-Request-Id` only; demo endpoints off by default; logs follow NFR-06.

## 8. Contract testing
FastAPI's generated OpenAPI is exported to `docs/.../openapi.json` on each build. Contract tests (pytest) assert: every endpoint's success and error shapes, discriminated card validation, `409` busy and stale paths, idempotent checkout, and that no response contains a price in message `text` outside cards and templates.

## 9. Requirement coverage
| Area | Endpoints |
|---|---|
| Session and levers (FR-01 to 09) | 2, 3, 4 |
| Language flows (FR-10 to 57) | 5, 6, 13 |
| Engine visibility (FR-63, 115) | 12 |
| Cart and checkout (FR-70 to 83) | 7 to 11 |
| Resilience demo (UJ10, 22) | 14, 15 |

## 10. Open items
1. Exact field names may be refined when the Pydantic models are generated; the OpenAPI output then becomes authoritative.
2. Whether `why_this` embeds the breakdown or fetches it lazily is an implementation choice; embedding is simpler for two or three items.
3. `persona_label` for custom lever sets is "Custom"; presets come from `GET /config/levers`.

## 11. Sources
| Source | Used for | Link |
|---|---|---|
| FastAPI documentation | OpenAPI generation, validation | https://fastapi.tiangolo.com/ |
| Pydantic documentation | Models and discriminated unions | https://docs.pydantic.dev/ |
| RFC 9110, HTTP Semantics | Status code usage (cited from knowledge; verify) | https://www.rfc-editor.org/rfc/rfc9110 |
| IETF draft on the Idempotency-Key header | Checkout idempotency (draft; verify status) | https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/ |
