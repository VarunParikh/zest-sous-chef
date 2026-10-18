// Zest workbench: levers (left) and chat (right) in one window (FR-100; DESIGN.md Screen 0).
// State lives here in plain React state (ADR-010: decided at build time). A refresh resets everything.
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ApiFailure, api } from "./api/client";
import { EMPTY_CART, type Breakdown, type CartView, type Inspector, type LeverConfig, type LeverSet, type Message, type TurnResponse } from "./api/types";
import { CartWindow } from "./components/CartWindow";
import { ChatPanel, type BusyKind } from "./components/ChatPanel";
import { LeverPanel } from "./components/LeverPanel";
import { clone, sameLevers } from "./levers";

const DEMO_LINK = "https://www.youtube.com/watch?v=6YVx0i_hrZ0";
const DEMO_RECIPE = "Kadai paneer: 250 g paneer, 2 capsicum and 1 onion";
const CLEAR_CONFIRM = "Clearing the chat will also empty your cart. Continue?";
let localId = 0;

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
  const cartButton = useRef<HTMLButtonElement>(null);

  const startSession = useCallback(async (with_: LeverSet) => {
    const s = await api.createSession(with_);
    setSession({ id: s.session_id, persona: s.persona_label });
    setSnapshot(clone(with_));
    setMessages([...s.turn.messages, ...noticeMessages(s.turn)]);
    setCart(s.turn.cart);
    setBreakdown(null); setInspector(null); setServerFlag(false); setError(null);
  }, []);

  useEffect(() => {
    api.config().then(async (c) => { setConfig(c); setLevers(clone(c.defaults)); await startSession(c.defaults); })
      .catch((e) => setError(e instanceof ApiFailure ? e.body.user_message : String(e)));
  }, [startSession]);

  const absorb = useCallback(async (turn: TurnResponse) => {
    setMessages((m) => [...m, ...turn.messages, ...noticeMessages(turn)]);
    setCart(turn.cart);
    setServerFlag(turn.levers_changed_since_snapshot);
    for (const msg of turn.messages) for (const c of msg.cards) if (c.type === "why_this" && c.breakdown?.contributions && c.breakdown.kind !== "addon") setBreakdown(c.breakdown as Breakdown);
    if (turn.suggestions.length && session) setInspector(await api.inspector(session.id).catch(() => null));
  }, [session]);

  const guarded = useCallback(async (fn: () => Promise<TurnResponse>, kind: BusyKind = "text") => {
    if (busy || !session) return;
    setBusyKind(kind); setBusy(true); setError(null);
    try { await absorb(await fn()); }
    catch (e) {
      if (e instanceof ApiFailure && e.body.code !== "SESSION_BUSY") setError(e.body.user_message);
    } finally { setBusy(false); }
  }, [busy, session, absorb]);

  const userSays = (text: string) => setMessages((m) => [...m, { message_id: `local_${++localId}`, role: "user", template_id: null, text, cards: [] }]);
  const send = (text: string) => {
    if (!session || !levers) return;
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

  const handlers = {
    busy,
    onAction: (t: string, p: Record<string, unknown>) => void act(t, p),
    onChip: (chip: string) => {
      if (chip === "YouTube link") setDraft(DEMO_LINK);
      else if (chip === "Text recipe") setDraft(DEMO_RECIPE);
      else if (chip === "Upload photo") window.dispatchEvent(new Event("zest:upload"));
      else send("I am feeling indulgent");
    },
    onSample: (id: string) => { if (session && levers) { userSays(`Sample photo ${id}`); void guarded(() => api.samplePhoto(session.id, id, levers), "sample"); } },
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
          <p className="font-display text-lg font-bold leading-tight text-ink">Zest 🧑‍🍳</p>
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
            onUpload={(f) => { userSays(`📷 ${f.name}`); void guarded(() => api.upload(session.id, f, false, levers), "photo"); }}
            handlers={handlers} cartCount={cart.item_count} onOpenCart={() => setCartOpen(true)} cartButton={cartButton}
            onClearChat={clearChat} banner={banner} onNewChat={() => void newChat()} />
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
