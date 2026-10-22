// Lever tooltip and Rule/Preference tag (FR-122; DESIGN.md Tooltips: dark slate bubble, text-xs, 200 ms hover).
import { useEffect, useRef, useState } from "react";
import type { LeverTag } from "../levers";

export function TagPill({ tag }: { tag: LeverTag }) {
  return (
    <span data-lever-tag={tag}
      className={`rounded-xs px-1.5 py-px text-[10px] font-semibold uppercase tracking-[0.05em] ${tag === "Rule" ? "bg-warn-surface text-ink" : "bg-subtle text-muted"}`}>
      {tag}
    </span>
  );
}

/** An ⓘ that shows `text` on hover (after 200 ms), focus or tap; Escape closes it. `id` is the tooltip element's id,
 * which the control references with aria-describedby, so screen readers read the help with the control. */
export function InfoTip({ id, label, text }: { id: string; label: string; text: string }) {
  const [open, setOpen] = useState(false);
  const timer = useRef<number | undefined>(undefined);
  useEffect(() => () => window.clearTimeout(timer.current), []);
  const show = (delay: number) => { window.clearTimeout(timer.current); timer.current = window.setTimeout(() => setOpen(true), delay); };
  const hide = () => { window.clearTimeout(timer.current); setOpen(false); };
  return (
    <span className="relative inline-flex" onMouseEnter={() => show(200)} onMouseLeave={hide}>
      <button type="button" aria-label={`About ${label}`} aria-expanded={open} aria-describedby={id}
        onFocus={() => show(0)} onBlur={hide} onClick={() => (open ? hide() : show(0))}
        onKeyDown={(e) => { if (e.key === "Escape") hide(); }}
        className="flex h-4 w-4 items-center justify-center rounded-full border border-strong text-[10px] leading-none text-muted hover:border-brand hover:text-brand">
        i
      </button>
      <span id={id} role="tooltip" hidden={!open}
        className="absolute left-1/2 top-6 z-30 w-60 -translate-x-1/2 rounded-[6px] bg-[#111827] px-[10px] py-[6px] text-xs leading-relaxed text-white shadow-card">
        {text}
      </span>
    </span>
  );
}
