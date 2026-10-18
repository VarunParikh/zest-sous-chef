// Section 2: chat with Zest (FR-101 to 103; DESIGN.md Section 2, Footers, Loading States, Accessibility).
import { useEffect, useRef, useState, type FormEvent, type RefObject } from "react";
import type { Message } from "../api/types";
import { CartIcon, ImageIcon, Send } from "../icons";
import { CardView, type CardHandlers } from "./Cards";

export function ChatPanel({ messages, busy, error, draft, setDraft, onSend, onUpload, handlers, cartCount, onOpenCart,
  cartButton, onClearChat, banner, onNewChat }: {
  messages: Message[]; busy: boolean; error: string | null; draft: string; setDraft: (s: string) => void;
  onSend: (text: string) => void; onUpload: (f: File) => void; handlers: CardHandlers; cartCount: number;
  onOpenCart: () => void; cartButton: RefObject<HTMLButtonElement | null>; onClearChat: () => void; banner: boolean; onNewChat: () => void;
}) {
  const feed = useRef<HTMLDivElement>(null);
  const file = useRef<HTMLInputElement>(null);
  const input = useRef<HTMLInputElement>(null);
  const [, force] = useState(0);
  useEffect(() => { feed.current?.scrollTo({ top: feed.current.scrollHeight, behavior: "smooth" }); }, [messages, busy]);
  useEffect(() => {
    const open = () => file.current?.click();
    window.addEventListener("zest:upload", open);
    return () => window.removeEventListener("zest:upload", open);
  }, []);
  useEffect(() => { if (!busy) input.current?.focus(); force((n) => n + 1); }, [busy, draft]);

  const submit = (e: FormEvent) => { e.preventDefault(); if (!busy && draft.trim()) onSend(draft.trim()); };
  const empty = cartCount === 0;

  return (
    <section aria-labelledby="chat-title" className="flex h-full flex-col overflow-hidden rounded-xl border border-line bg-white shadow-sm">
      <header className="flex h-12 shrink-0 items-center justify-between border-b border-line px-5">
        <h2 id="chat-title" className="text-base font-semibold">Chat with Zest</h2>
        <div className="flex items-center gap-2">
          <button type="button" onClick={onClearChat} disabled={busy}
            className="rounded-[10px] border border-strong bg-white px-3 py-1.5 text-xs font-medium text-secondary hover:bg-[#F9FAFB] disabled:opacity-40">
            Clear chat
          </button>
          <button ref={cartButton} type="button" onClick={onOpenCart} disabled={empty}
            aria-label={empty ? "Cart is empty" : `Open cart, ${cartCount} items`}
            className="relative flex h-[38px] w-[38px] items-center justify-center rounded-md text-brand hover:bg-brand-tint disabled:cursor-not-allowed disabled:text-dim disabled:opacity-40">
            <CartIcon />
            {!empty && (
              <span aria-hidden="true" className="absolute -right-1 -top-1 min-w-[20px] rounded-full bg-brand px-1.5 text-center text-xs font-semibold leading-5 text-white">{cartCount}</span>
            )}
          </button>
        </div>
      </header>

      {banner && (
        <div role="status" className="flex shrink-0 items-center justify-between gap-3 border-b-2 border-warn bg-warn-surface px-5 py-3 text-sm font-semibold text-ink">
          <span className="flex items-center gap-2"><span aria-hidden="true">⚠️</span>Changes apply from your next chat session.</span>
          <button type="button" onClick={onNewChat}
            className="rounded-[10px] bg-brand px-3 py-1.5 text-xs font-semibold text-white hover:bg-brand-hover">Start new chat</button>
        </div>
      )}

      <div ref={feed} className="flex-1 space-y-3 overflow-y-auto px-5 py-4" aria-live="polite" aria-relevant="additions" aria-label="Conversation">
        {messages.map((m) => (
          <div key={m.message_id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start gap-2"}`}>
            {m.role !== "user" && <span aria-hidden="true" className="mt-1 text-xl">🧑‍🍳</span>}
            <div className={`max-w-[85%] ${m.role === "user" ? "rounded-lg bg-brand px-4 py-3 text-sm leading-normal text-white" : ""}`}>
              {m.role === "user" ? m.text : (
                <>
                  <p className="sr-only">Zest says:</p>
                  {m.text && <p className="rounded-lg bg-subtle px-4 py-3 text-sm leading-normal text-ink">{m.text}</p>}
                  {m.cards.map((c, i) => <CardView key={i} card={c} h={handlers} />)}
                </>
              )}
            </div>
          </div>
        ))}
        {busy && (
          <div className="flex items-center gap-2" role="status" aria-label="Zest is thinking">
            <span aria-hidden="true" className="text-xl">🧑‍🍳</span>
            <span className="flex gap-1 rounded-lg bg-subtle px-4 py-3">
              {[0, 1, 2].map((i) => <span key={i} className="h-2 w-2 animate-pulse rounded-full bg-muted" style={{ animationDelay: `${i * 150}ms` }} />)}
            </span>
          </div>
        )}
      </div>

      {error && (
        <p role="alert" className="mx-5 mb-2 rounded-md border border-err-border bg-err-surface px-3 py-2 text-sm text-err">{error}</p>
      )}

      <form onSubmit={submit} className="flex shrink-0 items-center gap-2 border-t border-line bg-white px-5 py-3">
        <input ref={file} type="file" accept="image/jpeg,image/png,image/webp" className="hidden" tabIndex={-1}
          onChange={(e) => { const f = e.target.files?.[0]; if (f) onUpload(f); e.target.value = ""; }} />
        <button type="button" aria-label="Upload food or fridge image" disabled={busy} onClick={() => file.current?.click()}
          className="flex h-[38px] w-[38px] shrink-0 items-center justify-center rounded-md text-muted hover:text-brand disabled:opacity-40"><ImageIcon /></button>
        <label htmlFor="chat-input" className="sr-only">Message Zest</label>
        <input id="chat-input" ref={input} value={draft} onChange={(e) => setDraft(e.target.value)} disabled={busy}
          placeholder={busy ? "Zest is thinking…" : "Type a message, paste a YouTube link, or describe your fridge"}
          className="h-11 min-w-0 flex-1 rounded-[10px] border border-strong px-[14px] text-sm disabled:bg-subtle" />
        <button type="submit" disabled={busy || !draft.trim()} aria-label="Send"
          className="flex h-11 items-center gap-2 rounded-[10px] bg-brand px-5 text-sm font-semibold text-white hover:bg-brand-hover active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40">
          <Send /> Send
        </button>
      </form>
    </section>
  );
}
