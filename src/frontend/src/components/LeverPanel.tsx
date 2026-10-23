// Section 1: recommendation levers (Settings Panel §1 to §7; FR-05, 06, 08, 104; DESIGN.md Accordions, Forms).
import { createContext, useContext, useEffect, useId, useState, type ReactNode } from "react";
import type { Breakdown, Inspector, LeverConfig, LeverSet } from "../api/types";
import { Chevron } from "../icons";
import { HISTORY_LABELS, LEVER_HELP, TREND_LABELS, WEIGHT_LABELS, changedLevers, clone, sameLevers, shares } from "../levers";
import { InfoTip, TagPill } from "./InfoTip";
import { PersonaCards } from "./PersonaCards";
import { DietIcon } from "./Illustrations";
import { InspectorTable } from "./InspectorTable";
import { ScoreChart } from "./ScoreChart";

function Accordion({ title, children, open: initial = false, tour, openFor }: {
  title: string; children: ReactNode; open?: boolean; tour?: string; openFor?: string | null;
}) {
  const [open, setOpen] = useState(initial);
  const id = useId();
  useEffect(() => { if (openFor) setOpen(true); }, [openFor]);  // FR-128: a chosen persona opens the sections it changes
  return (
    <section className="border-b border-line last:border-b-0" data-tour={tour}>
      <h3>
        <button type="button" aria-expanded={open} aria-controls={id} onClick={() => setOpen(!open)}
          className="flex h-12 w-full items-center justify-between text-left text-sm font-semibold text-ink">
          {title}
          <Chevron open={open} />
        </button>
      </h3>
      <div id={id} hidden={!open} className="space-y-4 pb-5">{children}</div>
    </section>
  );
}

const fieldLabel = "block text-xs font-semibold uppercase tracking-[0.05em] text-secondary";

/** FR-128: which lever paths the persona in use sets, and its name, for the "Set by" marks. */
const SetBy = createContext<{ persona: string | null; paths: Set<string> }>({ persona: null, paths: new Set() });
function SetByMark({ path }: { path?: string }) {
  const { persona, paths } = useContext(SetBy);
  if (!persona || !path || !paths.has(path)) return null;
  return <span data-set-by={path} className="ml-1.5 inline-flex items-center rounded-xs bg-brand-tint px-1.5 py-px align-middle text-[10px] font-semibold text-brand">Set by {persona}</span>;
}

/** Tag and ⓘ for a lever label (FR-122); returns the tooltip id for aria-describedby. */
function Help({ label, tipId }: { label: string; tipId: string }) {
  const h = LEVER_HELP[label];
  if (!h) return null;
  return <span className="ml-1.5 inline-flex items-center gap-1.5 align-middle"><TagPill tag={h.tag} /><InfoTip id={tipId} label={label} text={h.text} /></span>;
}

function Slider({ label, value, min = 0, max = 1, step = 0.05, onChange, suffix, format, path }: {
  label: string; value: number; min?: number; max?: number; step?: number; onChange: (v: number) => void;
  suffix?: ReactNode; format?: (v: number) => string; path?: string;
}) {
  const id = useId();
  const tipId = `${id}-tip`;
  const shown = format ? format(value) : value.toFixed(2);
  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between gap-3">
        <span><label htmlFor={id} className="text-sm text-secondary">{label}</label><Help label={label} tipId={tipId} /><SetByMark path={path} /></span>
        <span className="font-mono text-sm tabular-nums text-ink">{shown}{suffix}</span>
      </div>
      <input id={id} type="range" min={min} max={max} step={step} value={value} aria-valuetext={shown}
        aria-describedby={LEVER_HELP[label] ? tipId : undefined}
        onChange={(e) => onChange(Number(e.target.value))} className="w-full accent-brand" />
    </div>
  );
}

function Select({ label, value, options, onChange, path }: { label: string; value: string; options: string[]; onChange: (v: string) => void; path?: string }) {
  const id = useId();
  const tipId = `${id}-tip`;
  return (
    <div>
      <span className="flex flex-wrap items-center"><label htmlFor={id} className={fieldLabel}>{label}</label><Help label={label} tipId={tipId} /><SetByMark path={path} /></span>
      <select id={id} value={value} onChange={(e) => onChange(e.target.value)} aria-describedby={LEVER_HELP[label] ? tipId : undefined}
        className="mt-1 h-10 w-full rounded-md border border-strong bg-white px-3 text-sm">
        {options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  );
}

export function LeverPanel({ config, levers, onChange, breakdown, inspector }: {
  config: LeverConfig; levers: LeverSet; onChange: (l: LeverSet) => void; breakdown: Breakdown | null; inspector: Inspector | null;
}) {
  const set = (fn: (l: LeverSet) => void) => { const next = clone(levers); fn(next); onChange(next); };
  const { shares: eff, restored } = shares(levers.weights, config.defaults.weights);
  const dietTip = `${useId()}-tip`;
  const stockTip = `${useId()}-tip`;
  const presetMatch = config.presets.find((p) => sameLevers(p.levers, levers))?.name ?? "";
  const cap = config.ranges["business.price_cap_inr"] ?? { min: 80, max: 400 };
  // FR-128: what the persona in use sets, so its changes are listed, marked and their sections opened
  const changes = presetMatch ? changedLevers(levers, config.defaults) : [];
  const setBy = { persona: presetMatch || null, paths: new Set(changes.map((c) => c.path)) };
  const openFor = (section: string) => (changes.some((c) => c.section === section) ? presetMatch : null);

  return (
    <SetBy.Provider value={setBy}>
    <div className="px-5">
      <div className="pt-4">  {/* C83: no breadcrumb above the persona cards (owner, 2026-10-23) */}
        <PersonaCards config={config} active={presetMatch} isDefault={sameLevers(levers, config.defaults)} levers={levers}
          onChange={onChange} onCustom={() => {
            const target = document.querySelector<HTMLElement>('[data-tour="lever"]');
            target?.scrollIntoView({ behavior: "smooth", block: "start" });
            target?.querySelector<HTMLInputElement>("input[type=range]")?.focus({ preventScroll: true });
          }} />
        {changes.length > 0 && (
          <p data-testid="persona-sets" className="mt-2 rounded-md bg-brand-tint px-3 py-2 text-xs leading-relaxed text-secondary">
            <span className="font-semibold text-brand">{presetMatch} sets:</span> {changes.map((c) => c.text).join(" · ")}
          </p>
        )}
      </div>

      <div className="mt-2">
        <Accordion title="Master Scoring & Algorithmic Weights" open tour="lever" openFor={openFor("weights")}>
          {WEIGHT_LABELS.map((w) => (
            <Slider key={w.key} label={w.label} value={levers.weights[w.key]} path={`weights.${w.key}`}
              onChange={(v) => set((l) => { l.weights[w.key] = v; })}
              suffix={<span className="ml-2 text-muted">({Math.round(eff[w.share] * 100)}%)</span>} />
          ))}
          {restored && <p className="text-xs text-warn">All four are 0, so the defaults apply in the next session.</p>}
        </Accordion>

        <Accordion title="User Persona & Hard-Constraint Guardrails" open openFor={openFor("persona")}>
          <div className="grid gap-3 2xl:grid-cols-3">
            <Select label="Probable Gender" path="gender" value={levers.gender} options={config.options.gender} onChange={(v) => set((l) => { l.gender = v; })} />
            <Select label="Dietary Preference" path="diet" value={levers.diet} options={config.options.diet} onChange={(v) => set((l) => { l.diet = v; })} />
            <Select label="Religious / Cultural Beliefs" path="faith" value={levers.faith} options={config.options.faith} onChange={(v) => set((l) => { l.faith = v; })} />
          </div>
        </Accordion>

        <Accordion title="Specialized Diets & Lifestyle" openFor={openFor("diets")}>
          <fieldset aria-describedby={`${dietTip}`}>
            <legend className={`${fieldLabel} flex items-center`}>Specialized Diet Mode<Help label="Specialized Diet Mode" tipId={dietTip} /><SetByMark path="specialized_diets" /></legend>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {config.options.specialized_diets.map((d) => (
                <label key={d} className="flex items-center gap-2 text-sm text-secondary">
                  <input type="checkbox" className="h-[18px] w-[18px] accent-brand" checked={levers.specialized_diets.includes(d)}
                    onChange={(e) => set((l) => {
                      const rest = l.specialized_diets.filter((x) => x !== d && x !== "Standard / Balanced");
                      const next = e.target.checked ? [...rest, d] : rest;
                      l.specialized_diets = d === "Standard / Balanced" && e.target.checked ? [d] : next.length ? next : ["Standard / Balanced"];
                    })} />
                  <DietIcon diet={d} />
                  {d}
                </label>
              ))}
            </div>
          </fieldset>
        </Accordion>

        <Accordion title="Gourmet & Culinary Style" openFor={openFor("style")}>
          <Slider label="Gourmet / Imported Food Affinity" path="gourmet_affinity" value={levers.gourmet_affinity} onChange={(v) => set((l) => { l.gourmet_affinity = v; })} />
          <Slider label="Artisanal & Organic Preference" path="artisanal_organic" value={levers.artisanal_organic} onChange={(v) => set((l) => { l.artisanal_organic = v; })} />
        </Accordion>

        <Accordion title="Historical Category Affinity" openFor={openFor("history")}>
          {HISTORY_LABELS.map((h) => (
            <Slider key={h.key} label={h.label} path={`history.${h.key}`} value={levers.history[h.key]} onChange={(v) => set((l) => { l.history[h.key] = v; })} />
          ))}
        </Accordion>

        <Accordion title="Real-Time Market Trends" openFor={openFor("trends")}>
          {TREND_LABELS.map((t) => (
            <Slider key={t.key} label={t.label} path={`trends.${t.key}`} value={levers.trends[t.key]} onChange={(v) => set((l) => { l.trends[t.key] = v; })} />
          ))}
        </Accordion>

        <Accordion title="Business & Inventory Guardrails" openFor={openFor("business")}>
          <Slider label="Max Companion Add-on Price Cap" path="business.price_cap_inr" value={levers.business.price_cap_inr} min={cap.min} max={cap.max} step={10}
            format={(v) => `₹${v}`} onChange={(v) => set((l) => { l.business.price_cap_inr = v; })} />
          <label className="flex items-center gap-3 text-sm text-secondary">
            <input type="checkbox" role="switch" aria-checked={levers.business.stock_filter} checked={levers.business.stock_filter}
              aria-describedby={stockTip}
              className="h-[18px] w-[18px] accent-brand" onChange={(e) => set((l) => { l.business.stock_filter = e.target.checked; })} />
            Hide out-of-stock items (stock filter)
            <Help label="Hide out-of-stock items (stock filter)" tipId={stockTip} />
            <SetByMark path="business.stock_filter" />
          </label>
        </Accordion>

        <Accordion title="Recommendation Score Breakdown" open>
          <ScoreChart breakdown={breakdown} />
        </Accordion>

        <Accordion title="Retrieval & Scoring Inspector" tour="inspector">
          <InspectorTable inspector={inspector} />
        </Accordion>
      </div>
    </div>
    </SetBy.Provider>
  );
}
