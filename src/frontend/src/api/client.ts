// Typed client for the backend (API Spec v0.6). Every call goes through `/api` (the Vite proxy).
import type { CartView, Inspector, LeverConfig, LeverSet, Order, SessionResponse, TurnResponse, ApiErrorBody } from "./types";

export class ApiFailure extends Error {
  constructor(public status: number, public body: ApiErrorBody) {
    super(body.user_message || body.code);
  }
}

const SERVER_DOWN: ApiErrorBody = {
  code: "INTERNAL",
  template_id: "MSG-SERVER",
  user_message: "Your food will be ready but seems like our servers are struggling. We will be back shortly",
  retryable: true,
  details: {},
};

async function call<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`/api/v1${path}`, init);
  } catch {
    throw new ApiFailure(0, SERVER_DOWN);
  }
  if (res.status === 204) return undefined as T;
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new ApiFailure(res.status, body?.error ?? SERVER_DOWN);
  return body as T;
}

const json = (method: string, body: unknown): RequestInit => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const api = {
  config: () => call<LeverConfig>("/config/levers"),
  createSession: (levers: LeverSet) => call<SessionResponse>("/sessions", json("POST", { levers })),
  deleteSession: (id: string) => call<void>(`/sessions/${id}`, { method: "DELETE" }),
  chat: (id: string, text: string, levers: LeverSet) => call<TurnResponse>(`/sessions/${id}/chat`, json("POST", { text, levers })),
  samplePhoto: (id: string, photoId: string, levers: LeverSet) =>
    call<TurnResponse>(`/sessions/${id}/chat`, json("POST", { text: "", sample_photo_id: photoId, levers })),
  upload: (id: string, file: File, consent: boolean, levers: LeverSet) => {
    const form = new FormData();
    form.append("text", "");
    form.append("image", file);
    form.append("levers", JSON.stringify(levers));
    if (consent) form.append("consent", "true");
    return call<TurnResponse>(`/sessions/${id}/chat`, { method: "POST", body: form });
  },
  action: (id: string, type: string, payload: Record<string, unknown>, levers: LeverSet) =>
    call<TurnResponse>(`/sessions/${id}/action`, json("POST", { type, payload, levers })),
  cart: (id: string) => call<CartView>(`/sessions/${id}/cart`),
  setQuantity: (id: string, lineId: string, quantity: number) =>
    call<CartView>(`/sessions/${id}/cart/lines/${lineId}`, json("PATCH", { quantity })),
  removeLine: (id: string, lineId: string) => call<CartView>(`/sessions/${id}/cart/lines/${lineId}`, { method: "DELETE" }),
  removeDish: (id: string, dishId: string) => call<CartView>(`/sessions/${id}/cart/dishes/${dishId}`, { method: "DELETE" }),
  checkout: (id: string, key: string) => call<Order>(`/sessions/${id}/checkout`, { method: "POST", headers: { "Idempotency-Key": key } }),
  inspector: (id: string) => call<Inspector>(`/sessions/${id}/inspector`),
};
