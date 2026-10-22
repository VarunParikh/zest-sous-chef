// "Who's cooking?" persona cards (FR-121, AC-50, AC-51; Zest 2.0). Summaries and tags come from the server,
// generated from each preset's levers. A keyboard radio group: arrows move and select, like native radios.
import { useRef, useState } from "react";
import type { LeverConfig, LeverSet } from "../api/types";
import { clone } from "../levers";
import { PersonaAvatar } from "./Illustrations";

type Preset = LeverConfig["presets"][number];
const SHOWN = 4;

const display = (name: string) => name.replace(/\s*\(.*\)\s*$/, "");

/** "Custom" is the last card (owner, 2026-10-23): in use whenever the levers match no persona and are not the untouched
 * defaults. It has no levers of its own; choosing it takes the user to the levers to make their own mix. */
export function PersonaCards({ config, active, isDefault, levers, onChange, onCustom }: {
  config: LeverConfig; active: string; isDefault: boolean; levers: LeverSet; onChange: (l: LeverSet) => void; onCustom: () => void;
}) {
  const ordered: Preset[] = [...config.presets.filter((p) => !p.tag), ...config.presets.filter((p) => p.tag)];
  const [all, setAll] = useState(false);
  // Four cards, plus the persona in use if it is further down the list (the default reviewer is), then "Show all"
  const inUse = ordered.find((p) => p.name === active);
  const visible = all ? ordered : [...ordered.slice(0, SHOWN), ...(inUse && !ordered.slice(0, SHOWN).includes(inUse) ? [inUse] : [])];
  const custom = !active && !isDefault;
  const cards: (Preset & { custom?: boolean })[] = [...visible,
    { name: "Custom", levers, tag: null, custom: true,
      summary: custom ? "Your own mix of levers" : "Change any lever below to make your own mix" }];
  const activeIndex = custom ? cards.length - 1 : cards.findIndex((p) => p.name === active);
  const refs = useRef<(HTMLButtonElement | null)[]>([]);
  const pick = (i: number) => {
    const c = cards[i];
    if (c.custom) { onCustom(); return; }  // focus moves to the levers
    onChange(clone(c.levers));
    refs.current[i]?.focus();
  };
  const focusable = activeIndex >= 0 ? activeIndex : 0;

  return (
    <div data-tour="personas">
      <p id="who-cooking" className="block text-xs font-semibold uppercase tracking-[0.05em] text-secondary">Who's cooking?</p>
      <div role="radiogroup" aria-labelledby="who-cooking" className="mt-2 grid gap-2 sm:grid-cols-2"
        onKeyDown={(e) => {
          const i = refs.current.findIndex((r) => r === document.activeElement);
          if (i < 0) return;
          const step = e.key === "ArrowRight" || e.key === "ArrowDown" ? 1 : e.key === "ArrowLeft" || e.key === "ArrowUp" ? -1 : 0;
          if (step) { e.preventDefault(); const n = (i + step + cards.length) % cards.length; if (cards[n].custom) refs.current[n]?.focus(); else pick(n); }
        }}>
        {cards.map((p, i) => {
          const checked = p.custom ? custom : p.name === active;
          return (
            <button key={p.name} ref={(el) => { refs.current[i] = el; }} type="button" role="radio" aria-checked={checked}
              tabIndex={i === focusable ? 0 : -1} onClick={() => pick(i)}
              className={`flex items-center gap-3 rounded-lg border p-3 text-left transition-colors ${checked ? "border-brand bg-brand-tint" : "border-line bg-white hover:border-brand"}`}>
              <PersonaAvatar name={p.name} levers={p.levers} tag={p.tag} prop={p.custom ? "sliders" : undefined} />
              <span className="min-w-0 flex-1">
                <span className="flex flex-wrap items-center gap-1.5 text-sm font-semibold text-ink">
                  {display(p.name)}
                  {p.tag && <span className="rounded-xs bg-subtle px-1.5 text-[10px] font-semibold uppercase text-muted">{p.tag}</span>}
                </span>
                <span className="block text-xs text-secondary">{p.summary}</span>
                <span className={`mt-1.5 inline-block text-xs font-semibold ${checked ? "text-brand" : "text-brand underline"}`}>
                  {checked ? "✓ In use" : p.custom ? "Adjust the levers" : "Use this persona"}
                </span>
              </span>
            </button>
          );
        })}
      </div>
      <div className="mt-2 flex items-center justify-between text-xs">
        {isDefault ? <span className="text-muted">Default settings: no persona chosen yet</span> : <span />}
        {ordered.length > SHOWN && (
          <button type="button" className="font-semibold text-brand hover:underline" onClick={() => setAll(!all)}>
            {all ? "Show fewer" : `Show all ${ordered.length}`}
          </button>
        )}
      </div>
    </div>
  );
}
