// Section 1: recommendation levers (Settings Panel §1 to §7; FR-05, 06, 08, 104; DESIGN.md Accordions, Forms).
import { useId, useState, type ReactNode } from "react";
import type { Breakdown, Inspector, LeverConfig, LeverSet } from "../api/types";
import { Chevron } from "../icons";
import { HISTORY_LABELS, LEVER_HELP, TREND_LABELS, WEIGHT_LABELS, clone, shares } from "../levers";
import { InfoTip, TagPill } from "./InfoTip";
import { InspectorTable } from "./InspectorTable";
import { ScoreChart } from "./ScoreChart";

function Accordion({ title, children, open: initial = false }: { title: string; children: ReactNode; open?: boolean }) {
  const [open, setOpen] = useState(initial);
  const id = useId();
  return (
    <section className="border-b border-line last:border-b-0">
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

/** Tag and ⓘ for a lever label (FR-122); returns the tooltip id for aria-describedby. */
function Help({ label, tipId }: { label: string; tipId: string }) {
  const h = LEVER_HELP[label];
  if (!h) return null;
  return <span className="ml-1.5 inline-flex items-center gap-1.5 align-middle"><TagPill tag={h.tag} /><InfoTip id={tipId} label={label} text={h.text} /></span>;
}

function Slider({ label, value, min = 0, max = 1, step = 0.05, onChange, suffix, format }: {
  label: string; value: number; min?: number; max?: number; step?: number; onChange: (v: number) => void;
  suffix?: ReactNode; format?: (v: number) => string;
}) {
  const id = useId();
  const tipId = `${id}-tip`;
  const shown = format ? format(value) : value.toFixed(2);
  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between gap-3">
        <span><label htmlFor={id} className="text-sm text-secondary">{label}</label><Help label={label} tipId={tipId} /></span>
        <span className="font-mono text-sm tabular-nums text-ink">{shown}{suffix}</span>
      </div>
      <input id={id} type="range" min={min} max={max} step={step} value={value} aria-valuetext={shown}
        aria-describedby={LEVER_HELP[label] ? tipId : undefined}
        onChange={(e) => onChange(Number(e.target.value))} className="w-full accent-brand" />
    </div>
  );
}

function Select({ label, value, options, onChange }: { label: string; value: string; options: string[]; onChange: (v: string) => void }) {
  const id = useId();
  const tipId = `${id}-tip`;
  return (
    <div>
      <span className="flex items-center"><label htmlFor={id} className={fieldLabel}>{label}</label><Help label={label} tipId={tipId} /></span>
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
  const presetId = useId();
  const dietTip = `${useId()}-tip`;
  const stockTip = `${useId()}-tip`;
  const presetMatch = config.presets.find((p) => JSON.stringify(p.levers) === JSON.stringify(levers))?.name ?? "";
  const cap = config.ranges["business.price_cap_inr"] ?? { min: 80, max: 400 };

  return (
    <div className="px-5">
      <p className="pt-4 text-xs text-muted">Reviewer Workbench &gt; Active Persona Levers</p>
      <div className="mt-3">
        <label htmlFor={presetId} className={fieldLabel}>Persona preset</label>
        <select id={presetId} value={presetMatch} onChange={(e) => {
          const p = config.presets.find((x) => x.name === e.target.value); if (p) onChange(clone(p.levers));
        }} className="mt-1 h-10 w-full rounded-md border border-strong bg-white px-3 text-sm">
          <option value="">Custom</option>
          {config.presets.map((p) => <option key={p.name} value={p.name}>{p.name}</option>)}
        </select>
      </div>

      <div className="mt-2">
        <Accordion title="Master Scoring & Algorithmic Weights" open>
          {WEIGHT_LABELS.map((w) => (
            <Slider key={w.key} label={w.label} value={levers.weights[w.key]}
              onChange={(v) => set((l) => { l.weights[w.key] = v; })}
              suffix={<span className="ml-2 text-muted">({Math.round(eff[w.share] * 100)}%)</span>} />
          ))}
          <p className="text-xs text-muted">
            Effective share = weight ÷ sum of weights. Weights are relative: doubling all four changes nothing.
            {restored && <span className="text-warn"> All four are 0, so the defaults apply in the next session.</span>}
          </p>
        </Accordion>

        <Accordion title="User Persona & Hard-Constraint Guardrails" open>
          <div className="grid gap-3 2xl:grid-cols-3">
            <Select label="Probable Gender" value={levers.gender} options={config.options.gender} onChange={(v) => set((l) => { l.gender = v; })} />
            <Select label="Dietary Preference" value={levers.diet} options={config.options.diet} onChange={(v) => set((l) => { l.diet = v; })} />
            <Select label="Religious / Cultural Beliefs" value={levers.faith} options={config.options.faith} onChange={(v) => set((l) => { l.faith = v; })} />
          </div>
        </Accordion>

        <Accordion title="Specialized Diets & Lifestyle">
          <fieldset aria-describedby={`${dietTip}`}>
            <legend className={`${fieldLabel} flex items-center`}>Specialized Diet Mode<Help label="Specialized Diet Mode" tipId={dietTip} /></legend>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {config.options.specialized_diets.map((d) => (
                <label key={d} className="flex items-center gap-2 text-sm text-secondary">
                  <input type="checkbox" className="h-[18px] w-[18px] accent-brand" checked={levers.specialized_diets.includes(d)}
                    onChange={(e) => set((l) => {
                      const rest = l.specialized_diets.filter((x) => x !== d && x !== "Standard / Balanced");
                      const next = e.target.checked ? [...rest, d] : rest;
                      l.specialized_diets = d === "Standard / Balanced" && e.target.checked ? [d] : next.length ? next : ["Standard / Balanced"];
                    })} />
                  {d}
                </label>
              ))}
            </div>
          </fieldset>
        </Accordion>

        <Accordion title="Gourmet & Culinary Style">
          <Slider label="Gourmet / Imported Food Affinity" value={levers.gourmet_affinity} onChange={(v) => set((l) => { l.gourmet_affinity = v; })} />
          <Slider label="Artisanal & Organic Preference" value={levers.artisanal_organic} onChange={(v) => set((l) => { l.artisanal_organic = v; })} />
        </Accordion>

        <Accordion title="Historical Category Affinity">
          {HISTORY_LABELS.map((h) => (
            <Slider key={h.key} label={h.label} value={levers.history[h.key]} onChange={(v) => set((l) => { l.history[h.key] = v; })} />
          ))}
        </Accordion>

        <Accordion title="Real-Time Market Trends">
          {TREND_LABELS.map((t) => (
            <Slider key={t.key} label={t.label} value={levers.trends[t.key]} onChange={(v) => set((l) => { l.trends[t.key] = v; })} />
          ))}
        </Accordion>

        <Accordion title="Business & Inventory Guardrails">
          <Slider label="Max Companion Add-on Price Cap" value={levers.business.price_cap_inr} min={cap.min} max={cap.max} step={10}
            format={(v) => `₹${v}`} onChange={(v) => set((l) => { l.business.price_cap_inr = v; })} />
          <label className="flex items-center gap-3 text-sm text-secondary">
            <input type="checkbox" role="switch" aria-checked={levers.business.stock_filter} checked={levers.business.stock_filter}
              aria-describedby={stockTip}
              className="h-[18px] w-[18px] accent-brand" onChange={(e) => set((l) => { l.business.stock_filter = e.target.checked; })} />
            Hide out-of-stock items (stock filter)
            <Help label="Hide out-of-stock items (stock filter)" tipId={stockTip} />
          </label>
        </Accordion>

        <Accordion title="Recommendation Score Breakdown" open>
          <ScoreChart breakdown={breakdown} />
        </Accordion>

        <Accordion title="Retrieval & Scoring Inspector">
          <InspectorTable inspector={inspector} />
        </Accordion>
      </div>
    </div>
  );
}
