// Renderers for the 13 card types (API Spec §4.5). Taps go to `onAction`; nothing here changes the cart directly.
import { useState, type ReactElement } from "react";
import type { Breakdown, Card } from "../api/types";
import { Camera, Play, Sparkle, Utensils, rupees } from "../icons";
import { ScoreChart } from "./ScoreChart";

export interface CardHandlers {
  onAction: (type: string, payload: Record<string, unknown>) => void;
  onChip: (chip: string) => void;
  onSample: (photoId: string) => void;
  onOpenCart: () => void;
  onBreakdown: (b: Breakdown) => void;
  busy: boolean;
}

const pill = "inline-flex items-center gap-1.5 rounded-full border border-strong bg-white px-3 py-1.5 text-sm font-medium text-secondary transition-all duration-150 hover:border-brand hover:text-brand active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40";
const primary = "inline-flex items-center gap-1.5 rounded-full bg-brand px-3 py-1.5 text-sm font-medium text-white transition-all duration-150 hover:bg-brand-hover active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40";
const CHIP_ICON: Record<string, ReactElement> = { "YouTube link": <Play />, "Upload photo": <Camera />, "Text recipe": <Utensils />, "Feeling hungry": <Sparkle /> };

function Choices({ options, onPick, disabled }: { options: { value: string; label: string }[]; onPick: (v: string) => void; disabled: boolean }) {
  const [picked, setPicked] = useState<string | null>(null);
  return (
    <div className="mt-2 flex flex-wrap gap-2">
      {options.map((o, i) => (
        <button key={o.value} type="button" disabled={disabled || picked !== null} aria-pressed={picked === o.value}
          className={i === 0 ? primary : pill} onClick={() => { setPicked(o.value); onPick(o.value); }}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

export function CardView({ card, h }: { card: Card; h: CardHandlers }) {
  const [used, setUsed] = useState(false);
  const once = (fn: () => void) => () => { setUsed(true); fn(); };
  switch (card.type) {
    case "starter_chips":
      return (
        <div className="mt-2 flex flex-wrap gap-2">
          {card.chips.map((c) => <button key={c} type="button" className={pill} disabled={h.busy} onClick={() => h.onChip(c)}>{CHIP_ICON[c]}{c}</button>)}
        </div>
      );
    case "dish_added":
      return (
        <div className="mt-2 rounded-md border-l-4 border-brand bg-brand-tint p-3 text-sm">
          <p className="font-semibold text-ink">{card.dish_name}</p>
          <p className="text-secondary">{card.reason}</p>
          <p className="mt-1 text-secondary">{card.line_count} items · <span className="font-semibold">{rupees(card.dish_total_inr)}</span></p>
          <button type="button" className={`${pill} mt-2`} onClick={h.onOpenCart}>🛒 View cart</button>
        </div>
      );
    case "swap_options":
      return (
        <div className="mt-2 flex flex-wrap gap-2" role="group" aria-label="Swap options">
          {card.options.map((o) => (
            <button key={o.dish_id} type="button" className={pill} disabled={h.busy || used}
              onClick={once(() => h.onAction("swap", { suggestion_id: card.suggestion_id, alt_dish_id: o.dish_id }))}>
              Swap to {o.name}
            </button>
          ))}
        </div>
      );
    case "undo":
      return <button type="button" className={`${pill} mt-2`} disabled={h.busy || used}
        onClick={once(() => h.onAction("undo", { suggestion_id: card.suggestion_id }))}>↶ Undo</button>;
    case "why_this":
      return <WhyThis breakdown={card.breakdown} onShow={h.onBreakdown} />;
    case "clarify":
      return <Choices options={card.options} disabled={h.busy}
        onPick={(v) => h.onAction("answer", { question_id: card.question_id, choice: v })} />;
    case "confirm":
      return (
        <div>
          {card.prompt && <p className="mt-2 text-sm text-secondary">{card.prompt}</p>}
          <Choices options={card.options} disabled={h.busy} onPick={(v) => h.onAction("confirm", { confirm_id: card.confirm_id, choice: v })} />
        </div>
      );
    case "addon_suggestion":
      return (
        <div className="mt-2 rounded-md border border-line bg-white p-3 text-sm">
          <p><span className="font-semibold">{card.item.name}</span> · {rupees(card.item.price_inr)}</p>
          <p className="text-secondary">{card.reason}</p>
          <Choices options={[{ value: "add", label: "Add" }, { value: "decline", label: "Not now" }]} disabled={h.busy}
            onPick={(v) => h.onAction("add_on", { suggestion_id: card.suggestion_id, choice: v })} />
        </div>
      );
    case "substitution":
      return <SubstitutionCard card={card} onAction={h.onAction} busy={h.busy} />;
    case "photo_consent":
      return (
        <div className="mt-2 rounded-md border border-warn bg-warn-surface p-3 text-sm text-secondary">
          <p>{card.notice}</p>
          <Choices options={[{ value: "yes", label: "I agree" }, { value: "no", label: "No thanks" }]} disabled={h.busy}
            onPick={(v) => h.onAction("consent_photo", { choice: v })} />
          <p className="mt-2 text-xs text-muted">After agreeing, upload the photo again.</p>
        </div>
      );
    case "sample_photos":
      return (
        <div className="mt-2 flex flex-wrap gap-2" role="group" aria-label="Sample photos">
          {card.photos.map((p) => (
            <button key={p.id} type="button" className={pill} disabled={h.busy} onClick={() => h.onSample(p.id)}>
              <span className="rounded-xs bg-dim-surface px-1.5 text-xs text-muted">{p.label}</span> {p.caption}
            </button>
          ))}
        </div>
      );
    case "notice":
      return <p role="status" className={`mt-2 rounded-md border p-2 text-sm ${card.level === "warning" ? "border-warn bg-warn-surface text-secondary" : "border-line bg-white text-secondary"}`}>{card.text}</p>;
    case "cart_summary":
      return <p className="mt-2 text-sm text-secondary">{card.item_count} items · {rupees(card.subtotal_inr)}</p>;
  }
}

export function SubstitutionCard({ card, onAction, busy }: {
  card: Extract<Card, { type: "substitution" }>; onAction: (t: string, p: Record<string, unknown>) => void; busy: boolean;
}) {
  const delta = card.price_delta_inr;
  return (
    <div className="mt-2 rounded-md border border-line bg-white p-3 text-sm">
      <p><span className="text-muted line-through">{card.from_item}</span> → <span className="font-semibold">{card.to_item}</span></p>
      <p className="text-secondary">{delta === 0 ? "Same price" : delta > 0 ? `${rupees(delta)} more` : `${rupees(-delta)} less`} · {card.flavour_note}</p>
      <Choices options={[{ value: "accept", label: "Swap it" }, { value: "decline", label: "Keep it" }]} disabled={busy}
        onPick={(v) => onAction("substitute", { substitution_id: card.substitution_id, choice: v })} />
    </div>
  );
}

function WhyThis({ breakdown, onShow }: { breakdown: Breakdown | null; onShow: (b: Breakdown) => void }) {
  const [open, setOpen] = useState(false);
  if (!breakdown) return null;
  return (
    <div className="mt-2">
      <button type="button" className={pill} aria-expanded={open} onClick={() => { setOpen(!open); onShow(breakdown); }}>Why this?</button>
      {open && <div className="mt-2 rounded-md border border-line bg-white p-3"><ScoreChart breakdown={breakdown} /></div>}
    </div>
  );
}
