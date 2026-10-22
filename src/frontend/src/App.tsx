// Zest workbench: levers (left) and chat (right) in one window (FR-100; DESIGN.md Screen 0).
// State lives here in plain React state (ADR-010: decided at build time). A refresh resets everything.
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ApiFailure, api } from "./api/client";
import { EMPTY_CART, type Breakdown, type Card, type CartView, type Inspector, type LeverConfig, type LeverSet, type Message, type TurnResponse } from "./api/types";
import { CartWindow } from "./components/CartWindow";
import { ChatPanel, type BusyKind } from "./components/ChatPanel";
import { LeverPanel } from "./components/LeverPanel";
import { Tour, tourSeen } from "./components/Tour";
import { clone, sameLevers } from "./levers";
import { rupees } from "./icons";

const DEMO_LINK = "https://www.youtube.com/watch?v=6YVx0i_hrZ0";
const DEMO_RECIPE = "Kadai paneer: 250 g paneer, 2 capsicum and 1 onion";
const CLEAR_CONFIRM = "Clearing the chat will also empty your cart. Continue?";
let localId = 0;

// Apply and rerun (FR-120, Conversation Design §6.7 UI-RERUN*): the last request of this session and its top pick
type LastRequest = { kind: "text"; text: string } | { kind: "sample"; id: string } | { kind: "upload" };
type Pick = { name: string; score: number | null };
const short = (t: string) => (t.length > 40 ? `${t.slice(0, 39)}…` : t);
const fmtScore = (s: number | null) => (s === null ? "" : ` (${s.toFixed(2)})`);

/** The dish a turn put in the cart and its final score, if the turn suggested one. */
function topPick(turn: TurnResponse): Pick | null {
  for (const m of turn.messages) {
    const added = m.cards.find((c): c is Extract<Card, { type: "dish_added" }> => c.type === "dish_added");
    if (!added) continue;
    const why = m.cards.find((c): c is Extract<Card, { type: "why_this" }> => c.type === "why_this");
    const final = why?.breakdown && why.breakdown.kind !== "addon" && typeof why.breakdown.final === "number" ? why.breakdown.final : null;
    return { name: added.dish_name, score: final };
  }
  return null;
}

function compareLine(before: Pick, now: Pick): string {
  if (before.name === now.name) {
    return now.score !== null && before.score !== null
      ? `Same pick, new score ${now.score.toFixed(2)} (was ${before.score.toFixed(2)})`
      : `Same pick: ${now.name}`;
  }
  return `Before: ${before.name}${fmtScore(before.score)} → Now: ${now.name}${fmtScore(now.score)}`;
}

export default function App() {
  const [config, setConfig] = useState<LeverConfig | null>(null);
  const [levers, setLevers] = useState<LeverSet | null>(null);
  const [snapshot, setSnapshot] = useState<LeverSet | null>(null);
  const [session, setSession] = useState<{ id: string; persona: string } | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [cart, setCart] = useState<CartView>(EMPTY_CART);
  const [busy, setBusy] = useState(false);
  const [busyKind, setBusyKind] = useState<BusyKind>("text");
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [cartOpen, setCartOpen] = useState(false);
  const [breakdown, setBreakdown] = useState<Breakdown | null>(null);
  const [inspector, setInspector] = useState<Inspector | null>(null);
  const [serverFlag, setServerFlag] = useState(false);
  const [confirmClear, setConfirmClear] = useState(false);
  const [tab, setTab] = useState<"levers" | "chat">("chat");
  const [lastRequest, setLastRequest] = useState<LastRequest | null>(null);
  const [lastPick, setLastPick] = useState<Pick | null>(null);
  const [confirmRerun, setConfirmRerun] = useState(false);
  const [tourOpen, setTourOpen] = useState(false);
  const cartButton = useRef<HTMLButtonElement>(null);
  const sessionRef = useRef<{ id: string; persona: string } | null>(null);  // current at once, unlike state, for the rerun

  const startSession = useCallback(async (with_: LeverSet) => {
    const s = await api.createSession(with_);
    sessionRef.current = { id: s.session_id, persona: s.persona_label };
    setSession(sessionRef.current);
    setLastRequest(null); setLastPick(null);
    setSnapshot(clone(with_));
    setMessages([...s.turn.messages, ...noticeMessages(s.turn)]);
    setCart(s.turn.cart);
    setBreakdown(null); setInspector(null); setServerFlag(false); setError(null);
  }, []);

  useEffect(() => {
    api.config().then(async (c) => {
      setConfig(c); setLevers(clone(c.defaults)); await startSession(c.defaults);
      if (!tourSeen()) setTourOpen(true);  // FR-126: first visit only; the help icon restarts it
    })
      .catch((e) => setError(e instanceof ApiFailure ? e.body.user_message : String(e)));
  }, [startSession]);

  const absorb = useCallback(async (turn: TurnResponse) => {
    setMessages((m) => [...m, ...turn.messages, ...noticeMessages(turn)]);
    setCart(turn.cart);
    setServerFlag(turn.levers_changed_since_snapshot);
    for (const msg of turn.messages) for (const c of msg.cards) if (c.type === "why_this" && c.breakdown?.contributions && c.breakdown.kind !== "addon") setBreakdown(c.breakdown as Breakdown);
    const pick = topPick(turn);
    if (pick) setLastPick(pick);
    // After every turn: add-on offers (FR-119) arrive as cards, not suggestions, and the server keeps the latest pool
    const current = sessionRef.current;
    if (current) setInspector(await api.inspector(current.id).catch(() => null));
    return pick;
  }, []);

  const guarded = useCallback(async (fn: () => Promise<TurnResponse>, kind: BusyKind = "text") => {
    if (busy || !sessionRef.current) return;
    setBusyKind(kind); setBusy(true); setError(null);
    try { await absorb(await fn()); }
    catch (e) {
      if (e instanceof ApiFailure && e.body.code !== "SESSION_BUSY") setError(e.body.user_message);
    } finally { setBusy(false); }
  }, [busy, absorb]);

  const userSays = (text: string) => setMessages((m) => [...m, { message_id: `local_${++localId}`, role: "user", template_id: null, text, cards: [] }]);
  const send = (text: string) => {
    if (!session || !levers) return;
    setLastRequest({ kind: "text", text });
    userSays(text); setDraft("");
    void guarded(() => api.chat(session.id, text, levers), /youtu\.?be/i.test(text) ? "video" : "text");
  };
  const act = async (type: string, payload: Record<string, unknown>) => { if (session && levers) await guarded(() => api.action(session.id, type, payload, levers)); };

  const newChat = async () => {
    if (!session || !levers) return;
    setConfirmClear(false); setCartOpen(false);
    await api.deleteSession(session.id).catch(() => undefined);
    await startSession(levers);
  };
  const clearChat = () => (cart.item_count > 0 ? setConfirmClear(true) : void newChat());  // C32: confirm when the cart has items

  // FR-120: a new session with the current levers (C4 kept), then the same request again; the cart is emptied only
  // after the user confirms (AC-47). An uploaded photo is never stored (T-103), so the picker opens instead.
  const rerun = async () => {
    if (!lastRequest || !levers || busy) return;
    setConfirmRerun(false); setCartOpen(false);
    const before = lastPick, request = lastRequest, old = sessionRef.current;
    if (old) await api.deleteSession(old.id).catch(() => undefined);
    await startSession(levers);
    const current = sessionRef.current;
    if (!current) return;
    if (request.kind === "upload") { window.dispatchEvent(new Event("zest:upload")); return; }
    setLastRequest(request);
    userSays(request.kind === "text" ? request.text : `Sample photo ${request.id}`);
    setBusyKind(request.kind === "sample" ? "sample" : /youtu\.?be/i.test(request.kind === "text" ? request.text : "") ? "video" : "text");
    setBusy(true); setError(null);
    try {
      const turn = request.kind === "text" ? await api.chat(current.id, request.text, levers) : await api.samplePhoto(current.id, request.id, levers);
      const now = await absorb(turn);
      if (before && now) {
        const text = compareLine(before, now);
        setMessages((m) => [...m, { message_id: `local_${++localId}`, role: "assistant", template_id: "UI-RERUN-COMPARE", text: "",
          cards: [{ type: "notice", level: "info", template_id: "UI-RERUN-COMPARE", text }] }]);
      }
    } catch (e) {
      if (e instanceof ApiFailure && e.body.code !== "SESSION_BUSY") setError(e.body.user_message);
    } finally { setBusy(false); }
  };
  const askRerun = () => (cart.item_count > 0 ? setConfirmRerun(true) : void rerun());
  const rerunLabel = !lastRequest ? null
    : lastRequest.kind === "upload" ? "Apply, then upload your photo again"
    : `Apply and rerun “${short(lastRequest.kind === "text" ? lastRequest.text : `Sample photo ${lastRequest.id}`)}”`;

  const handlers = {
    busy,
    onAction: (t: string, p: Record<string, unknown>) => void act(t, p),
    onChip: (chip: string) => {
      if (chip === "YouTube link") send(DEMO_LINK);  // FR-124: starters act on one tap
      else if (chip === "Text recipe") send(DEMO_RECIPE);
      else if (chip === "Upload photo") window.dispatchEvent(new Event("zest:upload"));
      else send("I am feeling indulgent");
    },
    onSample: (id: string) => {
      if (session && levers) { setLastRequest({ kind: "sample", id }); userSays(`Sample photo ${id}`); void guarded(() => api.samplePhoto(session.id, id, levers), "sample"); }
    },
    onSend: send,
    onTour: () => setTourOpen(true),
    onOpenCart: () => setCartOpen(true),
    onBreakdown: setBreakdown,
  };

  const banner = useMemo(() => !sameLevers(levers, snapshot) || serverFlag, [levers, snapshot, serverFlag]);

  if (!config || !levers || !session) {
    return <main className="flex h-full items-center justify-center text-muted">{error ?? "Starting Zest…"}</main>;
  }

  return (
    <div className="flex h-[100dvh] flex-col overflow-hidden">
      <header className="z-20 flex h-14 shrink-0 items-center justify-between gap-4 border-b border-line bg-white px-6">
        <div>
          <p className="font-display text-lg font-bold leading-tight text-ink">Zest 2.0 🧑‍🍳</p>
          <p className="text-xs text-muted">QuickMart AI Sous-Chef</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="hidden items-center gap-2 rounded-full border border-ok-border bg-ok-surface px-3 py-1 text-xs text-ok-text md:flex">
            <span className="h-2 w-2 rounded-full bg-ok" aria-hidden="true" /> Active - 10 Min Delivery Connected · mock data
          </span>
          <span className="text-xs text-secondary">Persona: <span className="font-semibold">{session.persona}</span></span>
          <button type="button" onClick={() => setLevers(clone(config.defaults))}
            className="rounded-[10px] border border-strong bg-white px-3 py-1.5 text-xs font-medium text-secondary hover:bg-[#F9FAFB]">
            Reset levers
          </button>
          <button type="button" aria-label="Help and tour" title="Help and tour" onClick={() => setTourOpen(true)}
            className="flex h-8 w-8 items-center justify-center rounded-full border border-strong bg-white text-sm font-semibold text-secondary hover:border-brand hover:text-brand">
            ?
          </button>
        </div>
      </header>

      <div className="flex shrink-0 justify-center p-2 lg:hidden">
        <div role="tablist" aria-label="Workbench sections" className="flex rounded-md bg-subtle p-[3px]">
          {(["levers", "chat"] as const).map((t) => (
            <button key={t} role="tab" type="button" aria-selected={tab === t} onClick={() => setTab(t)}
              className={`rounded-md px-4 py-1.5 text-sm ${tab === t ? "bg-white text-brand shadow-sm" : "text-secondary"}`}>
              {t === "levers" ? "🎛️ Settings Levers" : "💬 Chat with Zest"}
            </button>
          ))}
        </div>
      </div>

      <main className="mx-auto grid min-h-0 w-full max-w-[1600px] flex-1 gap-6 px-6 pb-4 pt-4 lg:grid-cols-2">
        <section aria-label="Recommendation levers"
          className={`${tab === "levers" ? "block" : "hidden"} min-h-0 overflow-y-auto rounded-xl border border-line bg-white shadow-sm lg:block`}>
          <h2 className="flex h-12 items-center justify-between border-b border-line px-5 text-base font-semibold">
            Recommendation Levers
            {banner && <span className="rounded-full border border-warn bg-warn-surface px-2 py-0.5 text-xs font-medium text-secondary">Not applied yet: start a new chat</span>}
          </h2>
          <LeverPanel config={config} levers={levers} onChange={setLevers} breakdown={breakdown} inspector={inspector} />
        </section>
        <div className={`${tab === "chat" ? "block" : "hidden"} min-h-0 lg:block`}>
          <ChatPanel messages={messages} busy={busy} busyKind={busyKind} error={error} draft={draft} setDraft={setDraft} onSend={send}
            onUpload={(f) => { setLastRequest({ kind: "upload" }); userSays(`📷 ${f.name}`); void guarded(() => api.upload(session.id, f, false, levers), "photo"); }}
            handlers={handlers} cartCount={cart.item_count} onOpenCart={() => setCartOpen(true)} cartButton={cartButton}
            onClearChat={clearChat} banner={banner} onNewChat={() => void newChat()} rerunLabel={rerunLabel} onRerun={askRerun} />
        </div>
      </main>

      {confirmClear && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-[rgba(17,24,39,0.45)]">
          <div role="alertdialog" aria-modal="true" aria-labelledby="clear-title" className="w-full max-w-sm rounded-xl bg-white p-5 shadow-modal"
            onKeyDown={(e) => { if (e.key === "Escape") setConfirmClear(false); }}>
            <p id="clear-title" className="text-sm text-ink">{CLEAR_CONFIRM}</p>
            <div className="mt-4 flex justify-end gap-2">
              <button type="button" autoFocus onClick={() => setConfirmClear(false)} className="rounded-[10px] border border-strong px-4 py-2 text-sm">Cancel</button>
              <button type="button" onClick={() => void newChat()} className="rounded-[10px] bg-brand px-4 py-2 text-sm font-semibold text-white">Clear</button>
            </div>
          </div>
        </div>
      )}

      <Tour open={tourOpen} onClose={() => setTourOpen(false)} userActions={messages.filter((m) => m.role === "user").length}
        onStep={(anchor) => setTab(["personas", "lever", "inspector"].includes(anchor) ? "levers" : "chat")} />

      {confirmRerun && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-[rgba(17,24,39,0.45)]">
          <div role="alertdialog" aria-modal="true" aria-labelledby="rerun-title" className="w-full max-w-sm rounded-xl bg-white p-5 shadow-modal"
            onKeyDown={(e) => { if (e.key === "Escape") setConfirmRerun(false); }}>
            <p id="rerun-title" className="text-sm text-ink">
              This starts a fresh chat with your new settings and empties your cart ({cart.item_count} items, {rupees(cart.subtotal_inr)}).
            </p>
            <div className="mt-4 flex justify-end gap-2">
              <button type="button" autoFocus onClick={() => setConfirmRerun(false)} className="rounded-[10px] border border-strong px-4 py-2 text-sm">Cancel</button>
              <button type="button" onClick={() => void rerun()} className="rounded-[10px] bg-brand px-4 py-2 text-sm font-semibold text-white">Apply and rerun</button>
            </div>
          </div>
        </div>
      )}

      {cartOpen && (
        <CartWindow sessionId={session.id} cart={cart} setCart={setCart} returnFocus={cartButton} onAction={act}
          onClose={() => setCartOpen(false)}
          onOrdered={async () => {
            setCartOpen(false); setCart(await api.cart(session.id).catch(() => EMPTY_CART));
            document.getElementById("chat-input")?.focus();  // the cart icon is disabled once the cart is empty
          }} />
      )}
    </div>
  );
}

function noticeMessages(turn: TurnResponse): Message[] {
  return turn.notices.map((n, i) => ({ message_id: `${turn.turn_id}_notice_${i}`, role: "assistant", template_id: n.template_id, text: "", cards: [n] }));
}
