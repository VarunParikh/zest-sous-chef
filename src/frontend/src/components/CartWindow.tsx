// Screen 1 (Express Cart) and the order-placed state inside the same mobile-shaped window
// (DESIGN.md Screen 1, Interaction Patterns; FR-72 to 75, 80, 81, 83, 103; C1: 10 s progress bar; C13; C14).
import { useEffect, useRef, useState, type KeyboardEvent, type RefObject } from "react";
import { ApiFailure, api } from "../api/client";
import type { Card, CartView, Order } from "../api/types";
import { Back, Bike, CategoryTile, Check, Close, CourseIcon, Minus, Plus, Trash, rupees } from "../icons";
import { SubstitutionCard } from "./Cards";

export function CartWindow({ sessionId, cart, setCart, onClose, returnFocus, onAction, onOrdered }: {
  sessionId: string; cart: CartView; setCart: (c: CartView) => void; onClose: () => void;
  returnFocus: RefObject<HTMLButtonElement | null>; onAction: (t: string, p: Record<string, unknown>) => Promise<void>; onOrdered: () => void;
}) {
  const dialog = useRef<HTMLDivElement>(null);
  const [order, setOrder] = useState<Order | null>(null);
  const [placing, setPlacing] = useState(false);
  const [problem, setProblem] = useState<{ text: string; subs: Extract<Card, { type: "substitution" }>[]; blocked: string[] } | null>(null);
  const [progress, setProgress] = useState(0);
  const key = useRef<string>(crypto.randomUUID());

  useEffect(() => {
    const opener = returnFocus.current;
    dialog.current?.querySelector<HTMLElement>("[data-autofocus]")?.focus();
    return () => opener?.focus();  // FR-103: focus returns to the cart icon
  }, [returnFocus]);

  useEffect(() => {
    if (!order) return;
    const total = order.collapse_after_s * 1000, start = performance.now();
    const tick = window.setInterval(() => {
      const p = Math.min(1, (performance.now() - start) / total);
      setProgress(p);
      if (p >= 1) { window.clearInterval(tick); onOrdered(); }
    }, 100);
    return () => window.clearInterval(tick);
  }, [order, onOrdered]);

  const run = async (fn: () => Promise<CartView>) => {
    try { setCart(await fn()); setProblem(null); key.current = crypto.randomUUID(); }
    catch (e) { if (e instanceof ApiFailure) setProblem({ text: e.body.user_message, subs: [], blocked: [] }); }
  };

  const buy = async () => {
    if (placing) return;
    setPlacing(true);
    try {
      setOrder(await api.checkout(sessionId, key.current));
    } catch (e) {
      if (e instanceof ApiFailure) {
        const d = e.body.details as { line_ids?: string[]; substitutions?: Extract<Card, { type: "substitution" }>[]; cart?: CartView };
        if (d.cart) setCart(d.cart);
        setProblem({ text: e.body.user_message, subs: d.substitutions ?? [], blocked: d.line_ids ?? [] });
      }
    } finally {
      setPlacing(false);
    }
  };

  const onKey = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Escape" && !order) { e.preventDefault(); onClose(); return; }
    if (e.key !== "Tab") return;  // focus trap (FR-103)
    const items = Array.from(dialog.current?.querySelectorAll<HTMLElement>("button:not([disabled]), [href], input, [tabindex='0']") ?? []);
    if (!items.length) return;
    const first = items[0], last = items[items.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  };

  const ownerDish = (lineId: string | null) => cart.dishes.find((d) => d.lines.some((l) => l.line_id === lineId))?.name ?? "another dish";

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-[rgba(17,24,39,0.45)] backdrop-blur-[4px]" onMouseDown={(e) => { if (e.target === e.currentTarget && !order) onClose(); }}>
      <div ref={dialog} role="dialog" aria-modal="true" aria-labelledby="cart-title" onKeyDown={onKey}
        className="z-50 flex h-[min(844px,100dvh)] w-full max-w-[420px] flex-col overflow-hidden rounded-[20px] bg-white shadow-modal">
        {order ? (
          <div className="flex flex-1 flex-col items-center justify-center gap-5 bg-gradient-to-b from-celebrate-from to-celebrate-to px-8 text-center text-white" role="status" aria-live="assertive">
            <h2 id="cart-title" className="sr-only">Order placed</h2>
            <span className="flex h-24 w-24 items-center justify-center rounded-full bg-white/15 backdrop-blur-[12px]">
              <span className="flex h-16 w-16 items-center justify-center rounded-full bg-celebrate-seal text-white"><Check /></span>
            </span>
            <p className="font-display text-2xl font-bold leading-tight">🎉 {order.message.text}</p>
            <p className="text-celebrate-text">Order {order.order_id}</p>
            <p className="text-celebrate-text">{rupees(order.subtotal_inr)}</p>
            <span className="text-celebrate-text"><Bike /></span>
            <p className="text-sm text-celebrate-text">Packed → Dispatched → Arriving shortly</p>
            <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-white/20" role="progressbar" aria-label="Closing in 10 seconds"
              aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(progress * 100)}>
              <div className="h-full bg-white" style={{ width: `${progress * 100}%` }} />
            </div>
          </div>
        ) : (
          <>
            <header className="flex h-14 items-center justify-between border-b border-line px-3">
              <button type="button" aria-label="Back to chat" onClick={onClose} className="flex h-[38px] w-[38px] items-center justify-center rounded-md text-muted hover:text-brand"><Back /></button>
              <h2 id="cart-title" className="font-display text-base font-semibold">QuickMart Express Cart</h2>
              <button type="button" data-autofocus aria-label="Close cart" onClick={onClose} className="flex h-[38px] w-[38px] items-center justify-center rounded-md text-muted hover:text-brand"><Close /></button>
            </header>
            <div className="flex-1 space-y-[18px] overflow-y-auto bg-canvas p-4">
              {cart.dishes.length === 0 && (
                <p className="mt-16 text-center text-sm text-muted">🧺<br />Your cart is empty. Pick a recipe or paste a YouTube link to get started!</p>
              )}
              {cart.dishes.map((d, i) => (
                <section key={d.cart_dish_id} className="rounded-lg border border-line bg-white p-[14px]" aria-label={`Dish ${i + 1}: ${d.name}`}>
                  <div className="flex items-center gap-2">
                    <CourseIcon course={d.course} />
                    <h3 className="flex-1 text-sm font-semibold leading-snug">Dish {i + 1}: {d.name} ({rupees(d.dish_total_inr)})</h3>
                    <button type="button" aria-label={`Remove ${d.name}`} onClick={() => run(() => api.removeDish(sessionId, d.cart_dish_id))}
                      className="flex h-[38px] w-[38px] items-center justify-center rounded-md text-muted hover:text-err"><Trash /></button>
                  </div>
                  <ul className="mt-2 divide-y divide-line">
                    {d.lines.map((ln) => {
                      const shared = !ln.priced && ln.shared_from_line_id !== null;
                      const blocked = problem?.blocked.includes(ln.line_id) || !ln.in_stock;
                      const noteId = `note-${ln.line_id}`;
                      return (
                        <li key={ln.line_id} className={`flex items-center gap-3 px-1 py-[10px] ${shared ? "bg-[#F9FAFB] opacity-45" : ""}`}
                          aria-disabled={shared || undefined} aria-describedby={shared || blocked ? noteId : undefined}>
                          <CategoryTile icon={ln.icon} />
                          <div className="min-w-0 flex-1">
                            <p className="line-clamp-2 break-words text-sm font-semibold leading-snug">{ln.variant_name}{ln.packs[0] ? ` (${ln.packs[0].pack})` : ""}</p>
                            {shared ? (
                              <p id={noteId} className="text-xs text-muted">Inactive / Dimmed - Already included in {ownerDish(ln.shared_from_line_id)}</p>
                            ) : (
                              <p className="text-sm">{rupees(ln.price_inr)}{ln.estimated && <span className="ml-1 text-xs text-muted">(estimate)</span>}</p>
                            )}
                            {blocked && <p id={noteId} className="text-xs font-medium text-err">Out of stock</p>}
                          </div>
                          {!shared && (
                            <div className="flex items-center rounded-sm border border-strong" role="group" aria-label={`Quantity of ${ln.variant_name}`}>
                              <button type="button" aria-label="Decrease" disabled={ln.quantity <= 1}
                                onClick={() => run(() => api.setQuantity(sessionId, ln.line_id, ln.quantity - 1))}
                                className="flex h-8 w-7 items-center justify-center disabled:opacity-40"><Minus /></button>
                              <span className="w-6 text-center font-mono text-sm" aria-live="polite">{ln.quantity}</span>
                              <button type="button" aria-label="Increase" disabled={ln.quantity >= 9}
                                onClick={() => run(() => api.setQuantity(sessionId, ln.line_id, ln.quantity + 1))}
                                className="flex h-8 w-7 items-center justify-center disabled:opacity-40"><Plus /></button>
                            </div>
                          )}
                          <button type="button" aria-label={`Remove ${ln.variant_name}`} onClick={() => run(() => api.removeLine(sessionId, ln.line_id))}
                            className="flex h-[38px] w-[38px] items-center justify-center rounded-md text-muted hover:text-err"><Trash /></button>
                        </li>
                      );
                    })}
                  </ul>
                </section>
              ))}
              {problem && (
                <div role="alert" className="rounded-md border border-err-border bg-err-surface p-3 text-sm text-err">
                  {problem.text}
                  {problem.subs.map((s) => (
                    <SubstitutionCard key={s.substitution_id} card={s} busy={false}
                      onAction={async (t, p) => { await onAction(t, p); setProblem(null); setCart(await api.cart(sessionId)); }} />
                  ))}
                </div>
              )}
            </div>
            <footer className="border-t border-line px-5 py-4">
              <div className="mb-3 flex items-center justify-between text-sm">
                <span className="text-secondary">Subtotal ({cart.item_count} items)</span>
                <span className="font-semibold">{rupees(cart.subtotal_inr)}</span>
              </div>
              <button type="button" onClick={buy} disabled={placing || cart.item_count === 0}
                className="h-12 w-full rounded-[10px] bg-brand text-sm font-semibold text-white transition-all duration-150 hover:bg-brand-hover active:scale-[0.98] active:bg-brand-active disabled:cursor-not-allowed disabled:opacity-40">
                ⚡ Buy Now
              </button>
              <p className="mt-2 text-center text-xs text-muted">Mock store: no real order or payment is made.</p>
            </footer>
          </>
        )}
      </div>
    </div>
  );
}
