// Stacked score breakdown for the latest suggestion (FR-63, 104; DESIGN.md Charts). Segments sum to the final score.
import type { Breakdown } from "../api/types";

const SEGMENTS = [
  { key: "s_h", label: "History", color: "bg-chart-history" },
  { key: "s_t", label: "Trend", color: "bg-chart-trend" },
  { key: "s_p", label: "Culinary", color: "bg-chart-culinary" },
  { key: "s_g", label: "Persona", color: "bg-chart-persona" },
];

export function ScoreChart({ breakdown }: { breakdown: Breakdown | null }) {
  if (!breakdown) return <p className="text-sm text-muted">Ask Zest for a dish to see how the levers scored it.</p>;
  const c = breakdown.contributions;
  return (
    <figure>
      <div className="flex h-5 w-full overflow-hidden rounded-sm bg-subtle" role="img"
        aria-label={`Final score ${breakdown.final.toFixed(3)}: ` + SEGMENTS.map((s) => `${s.label} ${(c[s.key] ?? 0).toFixed(3)}`).join(", ")}>
        {SEGMENTS.map((s) => (
          <div key={s.key} className={s.color} style={{ width: `${(c[s.key] ?? 0) * 100}%` }} />
        ))}
      </div>
      <figcaption className="mt-3 grid grid-cols-2 gap-2 text-xs text-secondary">
        {SEGMENTS.map((s) => (
          <span key={s.key} className="flex items-center gap-2">
            <span className={`inline-block h-3 w-3 rounded-xs ${s.color}`} aria-hidden="true" />
            {s.label}: <span className="font-mono">{(c[s.key] ?? 0).toFixed(3)}</span>
            <span className="text-muted">(weight {Math.round((breakdown.weights_effective[s.key] ?? 0) * 100)}%)</span>
          </span>
        ))}
        <span className="col-span-2 font-semibold text-ink">Final score: <span className="font-mono">{breakdown.final.toFixed(3)}</span></span>
      </figcaption>
    </figure>
  );
}
